"""Technical SEO Context Builder.

Resolves Phase 02 crawl results and optional Phase 03 visual artifacts,
verifies path safety, and constructs normalized TechnicalPageRecord objects.
"""

import json
import re
from pathlib import Path
from typing import Any, Optional

from site_dna.core.logging import get_logger
from site_dna.schemas.discovery import CrawlResult
from site_dna.schemas.technical_seo import TechnicalPageRecord
from site_dna.schemas.visual import VisualCaptureResult

logger = get_logger("analysis.technical_seo.context_builder")


class TechnicalSEOContextValidationError(Exception):
    """Raised when context validation fails or required run artifacts are missing."""


class TechnicalSEOContextBuilder:
    """Loads, validates, and normalizes crawl and visual evidence for Technical SEO auditing."""

    def __init__(self, base_dir: str = "runs"):
        self.base_dir = Path(base_dir)

    def build_context(
        self,
        crawl_run_id: str,
        visual_run_id: Optional[str] = None,
        max_pages: Optional[int] = None,
    ) -> tuple[list[TechnicalPageRecord], CrawlResult, Optional[VisualCaptureResult], dict[str, Any]]:
        """Resolve run files, validate integrity, and extract normalized TechnicalPageRecord list.

        Returns:
            Tuple of (pages, crawl_result, visual_result, evidence_index)
        """
        if not re.match(r"^[a-zA-Z0-9_\-]+$", crawl_run_id):
            raise TechnicalSEOContextValidationError(
                f"Invalid crawl_run_id format or potential path traversal: '{crawl_run_id}'"
            )

        crawl_dir = (self.base_dir / crawl_run_id).resolve()
        if not crawl_dir.is_relative_to(self.base_dir.resolve()):
            raise TechnicalSEOContextValidationError(
                f"Security Error: Crawl run path escapes base directory: '{crawl_run_id}'"
            )

        crawl_file = crawl_dir / "crawl.json"
        if not crawl_file.exists():
            raise TechnicalSEOContextValidationError(f"Missing crawl.json artifact at {crawl_file}")

        try:
            crawl_data = json.loads(crawl_file.read_text(encoding="utf-8"))
            crawl_result = CrawlResult.model_validate(crawl_data)
        except Exception as exc:
            raise TechnicalSEOContextValidationError(f"Failed to parse or validate crawl.json: {exc}") from exc

        # Resolve optional visual capture result
        visual_result: Optional[VisualCaptureResult] = None
        if visual_run_id:
            if not re.match(r"^[a-zA-Z0-9_\-]+$", visual_run_id):
                raise TechnicalSEOContextValidationError(f"Invalid visual_run_id format: '{visual_run_id}'")
            visual_file = crawl_dir / "visual" / visual_run_id / "visual.json"
            if not visual_file.exists():
                visual_file = crawl_dir / "visual" / visual_run_id / "manifest.json"
            if visual_file.exists():
                try:
                    vis_data = json.loads(visual_file.read_text(encoding="utf-8"))
                    visual_result = VisualCaptureResult.model_validate(vis_data)
                except Exception as exc:
                    logger.warning("Visual artifact found but failed to validate: %s", exc)

        # Build evidence index
        evidence_index: dict[str, Any] = {}
        for ev in crawl_result.evidence:
            evidence_index[ev.id] = ev.model_dump(mode="json")

        if visual_result:
            for page in visual_result.pages:
                for ev in getattr(page, "evidence_records", []):
                    evidence_index[ev.evidence_id] = ev.model_dump(mode="json")

        # Map visual pages by URL for fast lookup
        visual_pages_by_url: dict[str, Any] = {}
        if visual_result:
            for vp in visual_result.pages:
                visual_pages_by_url[vp.page_url.rstrip("/")] = vp

        # Construct normalized TechnicalPageRecord items
        pages: list[TechnicalPageRecord] = []
        raw_pages = crawl_result.pages[:max_pages] if max_pages else crawl_result.pages

        for idx, page in enumerate(raw_pages):
            page_url_norm = page.url.rstrip("/")
            vp = visual_pages_by_url.get(page_url_norm)

            # Collect source evidence IDs
            source_ev_ids = [
                ev.id for ev in crawl_result.evidence if ev.source_url and ev.source_url.rstrip("/") == page_url_norm
            ]
            if not source_ev_ids and crawl_result.evidence:
                source_ev_ids = [crawl_result.evidence[0].id]

            # Headings list
            headings = [h.model_dump() for h in page.headings] if page.headings else []

            # Robots directives
            robots_meta = (page.metadata.robots_meta or "").strip()
            robots_directives = [d.strip() for d in robots_meta.split(",") if d.strip()] if robots_meta else []

            # Internal links
            internal_links = [nav_link.url for nav_link in page.navigation_links] if page.navigation_links else []
            for lnk in crawl_result.discovered_internal_links:
                if lnk not in internal_links:
                    internal_links.append(lnk)

            # Rendered metadata from visual capture if available
            rendered_meta: dict[str, Any] = {}
            if vp:
                rendered_meta["has_desktop_capture"] = bool(vp.desktop_screenshots)
                rendered_meta["has_mobile_capture"] = bool(vp.mobile_screenshots)
                rendered_meta["dom_elements_count"] = len(vp.dom_elements)
                rendered_meta["render_errors"] = list(getattr(vp, "render_errors", []))

            # Structured data (JSON-LD)
            structured_data = list(page.json_ld) if page.json_ld else []

            record = TechnicalPageRecord(
                page_id=f"tech_page_{idx:02d}_{re.sub(r'[^a-zA-Z0-9]', '_', page.url)[:30]}",
                requested_url=page.url,
                final_url=page.final_url,
                canonical_url=page.metadata.canonical_url,
                http_status=page.status_code,
                response_headers={},
                robots_directives=robots_directives,
                sitemap_membership=bool(
                    crawl_result.website_info.sitemap_urls and page.url in crawl_result.website_info.sitemap_urls
                ),
                title=page.metadata.title,
                meta_description=page.metadata.description,
                headings=headings,
                html_lang=page.metadata.language,
                hreflang_links=[],
                viewport_meta=page.metadata.viewport,
                structured_data=structured_data,
                internal_links=internal_links,
                resource_metadata={},
                rendered_metadata=rendered_meta,
                source_evidence_ids=source_ev_ids[:5],
                collection_status="observed",
                limitations=[],
            )
            pages.append(record)

        logger.info(
            "Constructed technical SEO context: %d pages from crawl run %s",
            len(pages),
            crawl_run_id,
        )
        return pages, crawl_result, visual_result, evidence_index
