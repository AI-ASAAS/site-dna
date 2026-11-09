"""UX Context Builder validating and assembling evidence from Phase 02, 03, and 04 artifacts."""

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from PIL import Image
from pydantic import BaseModel, Field

from site_dna.core.logging import get_logger
from site_dna.schemas.discovery import CrawlResult
from site_dna.schemas.visual import VisualCaptureResult, VisualEvidenceRecord

logger = get_logger("analysis.ux_ui.context_builder")


class UXContextValidationError(Exception):
    """Raised when UX artifacts fail integrity, schema, or checksum verification."""


class UXPageContext(BaseModel):
    """Normalized, verified UX and semantic context for a single page."""

    page_url: str
    safe_page_id: str
    status: str
    desktop_screenshots: list[dict[str, Any]] = Field(default_factory=list)
    mobile_screenshots: list[dict[str, Any]] = Field(default_factory=list)
    dom_elements: list[dict[str, Any]] = Field(default_factory=list)
    layout_records: list[dict[str, Any]] = Field(default_factory=list)
    responsive_observations: list[dict[str, Any]] = Field(default_factory=list)
    evidence_records: list[VisualEvidenceRecord] = Field(default_factory=list)
    page_metadata: dict[str, Any] = Field(default_factory=dict)
    links: list[dict[str, Any]] = Field(default_factory=list)
    forms: list[dict[str, Any]] = Field(default_factory=list)
    headings: list[dict[str, Any]] = Field(default_factory=list)
    paragraphs: list[dict[str, Any]] = Field(default_factory=list)


class UXAnalysisContext(BaseModel):
    """Validated, normalized multi-page UX analysis context ready for evaluation."""

    crawl_run_id: str
    visual_run_id: str
    target_origin: str
    declared_language: Optional[str] = "ar"
    business_context: dict[str, Any] = Field(default_factory=dict)
    pages: list[UXPageContext] = Field(default_factory=list)
    evidence_index: dict[str, VisualEvidenceRecord] = Field(default_factory=dict)
    screenshot_files: list[str] = Field(default_factory=list)
    prior_visual_findings: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class UXContextBuilder:
    """Loads, validates, and normalizes evidence artifacts into an auditable UX context."""

    def __init__(self, base_dir: str = "runs"):
        self.base_dir = Path(base_dir)

    def build_context(
        self,
        visual_run_id: Optional[str] = None,
        visual_manifest_file: Optional[str] = None,
        crawl_run_id: Optional[str] = None,
        max_pages: int = 8,
    ) -> UXAnalysisContext:
        """Locate artifacts, verify checksums, and assemble a validated UX analysis context."""
        logger.info(
            "Building UX context: visual_run_id=%s, manifest=%s",
            visual_run_id,
            visual_manifest_file,
        )

        visual_dir, resolved_crawl_id, resolved_vis_id = self._resolve_artifacts(
            visual_run_id=visual_run_id,
            visual_manifest_file=visual_manifest_file,
            crawl_run_id=crawl_run_id,
        )

        crawl_file = self.base_dir / resolved_crawl_id / "crawl.json"
        if not crawl_file.exists() and crawl_run_id:
            alt = self.base_dir / crawl_run_id / "crawl.json"
            if alt.exists():
                crawl_file = alt
                resolved_crawl_id = crawl_run_id

        visual_file = visual_dir / "visual.json"

        if not visual_file.exists():
            raise UXContextValidationError(f"Missing visual.json artifact at {visual_file}")
        if not crawl_file.exists():
            raise UXContextValidationError(f"Missing crawl.json artifact at {crawl_file}")

        try:
            visual_result = VisualCaptureResult.model_validate_json(visual_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise UXContextValidationError(f"Malformed visual.json artifact: {exc}") from exc

        try:
            crawl_result = CrawlResult.model_validate_json(crawl_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise UXContextValidationError(f"Malformed crawl.json artifact: {exc}") from exc

        if visual_result.crawl_run_id != resolved_crawl_id:
            logger.warning(
                "Crawl run ID mismatch: visual references %s, crawl is %s. Normalizing.",
                visual_result.crawl_run_id,
                resolved_crawl_id,
            )
            visual_result.crawl_run_id = resolved_crawl_id

        seed_page = crawl_result.pages[0] if crawl_result.pages else None
        business_context = {
            "canonical_origin": crawl_result.website_info.canonical_origin,
            "declared_language": crawl_result.website_info.declared_language,
            "title": seed_page.metadata.title if seed_page else None,
            "description": seed_page.metadata.description if seed_page else None,
        }

        # Index Phase 02 pages by normalized URL
        crawl_pages_by_url = {self._normalize_url(p.url): p for p in crawl_result.pages}

        pages_context: list[UXPageContext] = []
        evidence_index: dict[str, VisualEvidenceRecord] = {}
        screenshot_files: list[str] = []
        warnings: list[str] = []

        eligible_pages = [p for p in visual_result.pages if p.status == "completed"][:max_pages]

        for vis_page in eligible_pages:
            normalized_url = self._normalize_url(vis_page.page_url)
            crawl_page = crawl_pages_by_url.get(normalized_url)

            # Map crawl links, forms, headings safely
            page_links = []
            if crawl_page:
                raw_links = getattr(crawl_page, "navigation_links", None) or getattr(crawl_page, "links", [])
                page_links = [lnk.model_dump() if hasattr(lnk, "model_dump") else lnk for lnk in raw_links]
            page_forms = (
                [f.model_dump() if hasattr(f, "model_dump") else f for f in crawl_page.forms]
                if crawl_page and hasattr(crawl_page, "forms")
                else []
            )
            page_headings = (
                [h.model_dump() if hasattr(h, "model_dump") else h for h in crawl_page.headings]
                if crawl_page and hasattr(crawl_page, "headings")
                else []
            )
            page_meta = (
                crawl_page.metadata.model_dump()
                if crawl_page and hasattr(crawl_page.metadata, "model_dump")
                else (getattr(crawl_page, "metadata", {}) or {})
            )

            page_paragraphs = []
            if crawl_page:
                raw_p = getattr(crawl_page, "paragraphs", None)
                if raw_p:
                    page_paragraphs.extend([p.model_dump() if hasattr(p, "model_dump") else p for p in raw_p])
                if getattr(crawl_page, "main_content_text", None):
                    page_paragraphs.append(
                        {"text": crawl_page.main_content_text, "word_count": len(crawl_page.main_content_text.split())}
                    )

            page_ctx = UXPageContext(
                page_url=vis_page.page_url,
                safe_page_id=vis_page.safe_page_id,
                status=vis_page.status,
                page_metadata=page_meta,
                links=page_links,
                forms=page_forms,
                headings=page_headings,
                paragraphs=page_paragraphs,
                evidence_records=vis_page.evidence_records,
            )

            # Process desktop screenshots
            for sc in vis_page.desktop_screenshots:
                sc_dict = sc.model_dump()
                shot_path = self._resolve_screenshot_path(sc.file_path, visual_dir)
                sc_dict["file_path"] = str(shot_path.resolve())
                if not shot_path.exists():
                    raise UXContextValidationError(f"Missing desktop screenshot file: {shot_path}")
                self._verify_screenshot_integrity(shot_path, sc.sha256)
                screenshot_files.append(str(shot_path.resolve()))
                page_ctx.desktop_screenshots.append(sc_dict)

            # Process mobile screenshots
            for sc in vis_page.mobile_screenshots:
                sc_dict = sc.model_dump()
                shot_path = self._resolve_screenshot_path(sc.file_path, visual_dir)
                sc_dict["file_path"] = str(shot_path.resolve())
                if not shot_path.exists():
                    raise UXContextValidationError(f"Missing mobile screenshot file: {shot_path}")
                self._verify_screenshot_integrity(shot_path, sc.sha256)
                screenshot_files.append(str(shot_path.resolve()))
                page_ctx.mobile_screenshots.append(sc_dict)

            # DOM elements
            page_ctx.dom_elements = [d.model_dump() for d in vis_page.dom_elements]
            page_ctx.layout_records = [rec.model_dump() for rec in vis_page.layout_records]
            page_ctx.responsive_observations = [r.model_dump() for r in vis_page.responsive_observations]

            # Index evidence records
            for ev in vis_page.evidence_records:
                evidence_index[ev.evidence_id] = ev

            pages_context.append(page_ctx)

        # Look for Phase 04 findings if available
        prior_findings: list[dict[str, Any]] = []
        analysis_base = visual_dir / "analysis"
        if analysis_base.exists():
            for analysis_dir in analysis_base.glob("vi-*"):
                analysis_file = analysis_dir / "analysis.json"
                if analysis_file.exists():
                    try:
                        data = json.loads(analysis_file.read_text(encoding="utf-8"))
                        prior_findings.extend(data.get("findings", []))
                    except Exception as err:
                        logger.warning("Could not read prior visual analysis %s: %s", analysis_file, err)

        return UXAnalysisContext(
            crawl_run_id=resolved_crawl_id,
            visual_run_id=resolved_vis_id,
            target_origin=crawl_result.website_info.canonical_origin or visual_result.website_url,
            declared_language=business_context.get("declared_language") or "ar",
            business_context=business_context,
            pages=pages_context,
            evidence_index=evidence_index,
            screenshot_files=screenshot_files,
            prior_visual_findings=prior_findings,
            warnings=warnings,
        )

    def _resolve_artifacts(
        self,
        visual_run_id: Optional[str] = None,
        visual_manifest_file: Optional[str] = None,
        crawl_run_id: Optional[str] = None,
    ) -> tuple[Path, str, str]:
        """Locate directory and identifiers safely preventing path traversal."""
        if visual_manifest_file:
            manifest_path = Path(visual_manifest_file)
            if not manifest_path.exists():
                raise UXContextValidationError(f"Manifest file not found: {visual_manifest_file}")
            try:
                manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                resolved_crawl_id = manifest_data["crawl_run_id"]
                resolved_vis_id = manifest_data["visual_run_id"]
                visual_dir = manifest_path.parent
                return visual_dir, resolved_crawl_id, resolved_vis_id
            except Exception as exc:
                raise UXContextValidationError(f"Failed to read visual manifest: {exc}") from exc

        if not visual_run_id:
            raise UXContextValidationError("Must provide either visual_run_id or visual_manifest_file")

        # Sanitize against path traversal
        if "/" in visual_run_id or "\\" in visual_run_id or ".." in visual_run_id:
            raise UXContextValidationError(f"Path traversal detected or invalid visual_run_id format: {visual_run_id}")

        if crawl_run_id:
            if "/" in crawl_run_id or "\\" in crawl_run_id or ".." in crawl_run_id:
                raise UXContextValidationError(f"Path traversal detected in crawl_run_id: {crawl_run_id}")
            vis_dir = self.base_dir / crawl_run_id / "visual" / visual_run_id
            if vis_dir.exists():
                return vis_dir, crawl_run_id, visual_run_id

        # Search runs directory for the visual_run_id
        if self.base_dir.exists():
            for c_dir in self.base_dir.iterdir():
                if c_dir.is_dir():
                    candidate = c_dir / "visual" / visual_run_id
                    if candidate.exists():
                        return candidate, c_dir.name, visual_run_id

        raise FileNotFoundError(f"Visual run directory not found for ID: {visual_run_id}")

    def _resolve_screenshot_path(self, file_path_str: str, visual_dir: Path) -> Path:
        """Resolve screenshot path whether absolute, relative to root, runs, or visual_dir."""
        p = Path(file_path_str)
        if p.is_absolute() and p.exists():
            return p
        if (self.base_dir.parent / p).exists():
            return (self.base_dir.parent / p).resolve()
        if (self.base_dir / p).exists():
            return (self.base_dir / p).resolve()
        if (visual_dir / p).exists():
            return (visual_dir / p).resolve()
        return visual_dir / p

    @staticmethod
    def _verify_screenshot_integrity(file_path: Path, expected_sha256: str) -> None:
        """Verify image exists, is valid PNG, and matches SHA-256."""
        data = file_path.read_bytes()
        calculated = hashlib.sha256(data).hexdigest()
        if calculated != expected_sha256:
            raise UXContextValidationError(
                f"Checksum mismatch for {file_path.name}: expected {expected_sha256}, got {calculated}"
            )
        try:
            with Image.open(file_path) as img:
                img.verify()
        except Exception as exc:
            raise UXContextValidationError(f"Corrupt image file {file_path}: {exc}") from exc

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Strip trailing slashes and fragments for uniform indexing."""
        clean = url.split("#")[0].strip()
        if clean.endswith("/") and len(clean) > 8:
            clean = clean[:-1]
        return clean.lower()
