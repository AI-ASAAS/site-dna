"""Context builder and evidentiary intake for Site DNA Content & Marketing Intelligence."""

import re
from pathlib import Path
from typing import Any, Optional

from site_dna.core.logging import get_logger
from site_dna.schemas.content_marketing import PageContentRecord
from site_dna.schemas.discovery import CrawlResult
from site_dna.schemas.visual import VisualCaptureResult

logger = get_logger("analysis.content_marketing.context_builder")


class ContentContextValidationError(ValueError):
    """Raised when crawl or visual run artifacts are invalid, missing, or compromised."""


class ContentContextBuilder:
    """Loads, validates, and normalizes crawled pages and visual evidence for content auditing."""

    def __init__(self, base_dir: str = "runs"):
        self.base_dir = Path(base_dir).resolve()

    def build_context(
        self,
        crawl_run_id: str,
        visual_run_id: Optional[str] = None,
        max_pages: int = 8,
    ) -> tuple[list[PageContentRecord], dict[str, Any], str, dict[str, Any]]:
        """Validate run IDs, load crawl and visual artifacts, and return normalized content records.

        Returns:
            Tuple of (pages, evidence_index, target_origin, website_info_dict)
        """
        self._sanitize_id(crawl_run_id, "crawl_run_id")
        if visual_run_id:
            self._sanitize_id(visual_run_id, "visual_run_id")

        crawl_dir, resolved_crawl_id = self._resolve_crawl_dir(crawl_run_id)
        crawl_file = crawl_dir / "crawl.json"

        if not crawl_file.exists():
            raise FileNotFoundError(f"Missing crawl.json artifact at {crawl_file}")

        try:
            crawl_result = CrawlResult.model_validate_json(crawl_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ContentContextValidationError(f"Malformed crawl.json artifact: {exc}") from exc

        target_origin = crawl_result.website_info.canonical_origin or "https://unknown.example.com"
        website_info_dict = {
            "initial_url": crawl_result.website_info.initial_url,
            "canonical_origin": target_origin,
            "declared_language": crawl_result.website_info.declared_language,
            "sitemap_found": crawl_result.website_info.sitemap_found,
            "total_crawled_pages": len(crawl_result.pages),
        }

        # Index evidence records
        evidence_index: dict[str, Any] = {}
        if hasattr(crawl_result, "evidence") and crawl_result.evidence:
            for ev in crawl_result.evidence:
                evidence_index[ev.id] = ev.model_dump(mode="json") if hasattr(ev, "model_dump") else ev

        # Optional visual integration
        visual_elements_by_url: dict[str, list[dict[str, Any]]] = {}
        if visual_run_id:
            vis_file = crawl_dir / "visual" / visual_run_id / "visual.json"
            if vis_file.exists():
                try:
                    vis_result = VisualCaptureResult.model_validate_json(vis_file.read_text(encoding="utf-8"))
                    for vp in vis_result.pages:
                        clean_u = self._normalize_url(vp.page_url)
                        visual_elements_by_url[clean_u] = [d.model_dump() for d in vp.dom_elements]
                        for ev_rec in vp.evidence_records:
                            evidence_index[ev_rec.evidence_id] = ev_rec.model_dump()
                except Exception as exc:
                    logger.warning("Optional visual.json parsing failed: %s", exc)

        eligible_pages = crawl_result.pages[:max_pages]
        page_records: list[PageContentRecord] = []

        for idx, page in enumerate(eligible_pages, 1):
            normalized_url = self._normalize_url(page.url)
            page_id = f"p{idx}_{re.sub(r'[^a-zA-Z0-9]', '_', normalized_url)[-16:]}"

            # Collect headings
            headings_data = [{"level": h.level, "text": h.text.strip()} for h in page.headings if h.text]

            # Collect CTA candidates from buttons and navigation
            ctas: list[dict[str, Any]] = []
            for b in page.buttons:
                if b and b.strip():
                    ctas.append({"text": b.strip(), "type": "button", "context": "buttons"})

            for lnk in page.navigation_links:
                txt = lnk.text.strip() if lnk.text else ""
                if txt and len(txt.split()) <= 5:
                    ctas.append(
                        {
                            "text": txt,
                            "type": "link",
                            "url": lnk.url,
                            "is_internal": lnk.is_internal,
                        }
                    )

            # Trust signals
            trust_candidates: list[str] = []
            trust_keywords = [
                "تواصل معنا",
                "اتصل بنا",
                "من نحن",
                "عن الشركة",
                "سياسة الخصوصية",
                "الشروط والأحكام",
                "ضمان",
                "شهادة",
                "عملاؤنا",
                "شركاؤنا",
                "contact",
                "about us",
                "privacy policy",
                "terms of service",
                "guarantee",
                "certification",
                "clients",
                "partners",
                "testimonials",
                "support",
            ]
            content_lower = page.main_content_text.lower()
            for kw in trust_keywords:
                if kw in content_lower:
                    trust_candidates.append(kw)

            # Link evidence IDs
            page_ev_ids = [
                ev_id
                for ev_id, ev_data in evidence_index.items()
                if self._normalize_url(ev_data.get("source_url", "")) == normalized_url
                or self._normalize_url(ev_data.get("page_url", "")) == normalized_url
            ]

            # Service descriptions candidate extraction
            service_descs: list[str] = []
            paragraphs_data: list[dict[str, Any]] = []
            raw_text = page.main_content_text.strip()
            if raw_text:
                chunks = [c.strip() for c in raw_text.split("\n\n") if c.strip()]
                for c in chunks:
                    paragraphs_data.append({"text": c, "word_count": len(c.split())})
                    if any(term in c.lower() for term in ["خدمة", "خدمات", "حلول", "service", "services", "solution"]):
                        service_descs.append(c[:200])

            record = PageContentRecord(
                page_id=page_id,
                page_url=page.url,
                page_type=page.category or "unknown",
                page_title=page.metadata.title,
                meta_description=page.metadata.description,
                language=page.metadata.language or crawl_result.website_info.declared_language,
                dir=page.metadata.dir,
                headings=headings_data,
                main_content=raw_text,
                paragraphs=paragraphs_data,
                service_descriptions=service_descs[:5],
                cta_candidates=ctas[:20],
                navigation_labels=[lnk.text.strip() for lnk in page.navigation_links if lnk.text][:20],
                trust_signal_candidates=trust_candidates,
                word_count=page.word_count or len(raw_text.split()),
                source_evidence_ids=page_ev_ids,
                extraction_limitations=[] if raw_text else ["No visible main content extracted from HTML"],
            )
            page_records.append(record)

        logger.info(
            "Built content context for %d pages from crawl %s",
            len(page_records),
            resolved_crawl_id,
        )
        return page_records, evidence_index, target_origin, website_info_dict

    def _resolve_crawl_dir(self, crawl_run_id: str) -> tuple[Path, str]:
        """Resolve path to crawl directory securely."""
        direct = self.base_dir / crawl_run_id
        if direct.exists() and direct.is_dir():
            return direct, crawl_run_id

        # Search runs directory for matching crawl directory
        if self.base_dir.exists():
            for d in self.base_dir.iterdir():
                if d.is_dir() and d.name == crawl_run_id:
                    return d, d.name

        raise FileNotFoundError(f"Crawl run directory not found for ID: {crawl_run_id}")

    @staticmethod
    def _sanitize_id(identifier: str, field_name: str) -> None:
        """Enforce strict identifier format to prevent path traversal."""
        if not identifier or not re.match(r"^[a-zA-Z0-9_\-]+$", identifier):
            raise ContentContextValidationError(
                f"Path traversal detected or invalid {field_name} format: '{identifier}'"
            )

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Uniform URL normalization for dictionary indexing."""
        clean = url.split("#")[0].strip()
        if clean.endswith("/") and len(clean) > 8:
            clean = clean[:-1]
        return clean.lower()
