"""Visual Identity Context Builder validating and assembling evidence from prior phases."""

import hashlib
from pathlib import Path
from typing import Any, Optional

from PIL import Image
from pydantic import BaseModel, Field

from site_dna.core.logging import get_logger
from site_dna.schemas.discovery import CrawlResult
from site_dna.schemas.visual import VisualCaptureResult, VisualEvidenceRecord, VisualPageResult

logger = get_logger("analysis.visual_identity.context_builder")


class ContextValidationError(Exception):
    """Raised when visual or crawl artifacts fail integrity, schema, or checksum verification."""


class PageAnalysisContext(BaseModel):
    """Normalized, verified visual and semantic context for a single page."""

    page_url: str
    safe_page_id: str
    status: str
    desktop_screenshots: list[dict[str, Any]] = Field(default_factory=list)
    mobile_screenshots: list[dict[str, Any]] = Field(default_factory=list)
    colors: list[dict[str, Any]] = Field(default_factory=list)
    typography: list[dict[str, Any]] = Field(default_factory=list)
    layout_records: list[dict[str, Any]] = Field(default_factory=list)
    dom_elements: list[dict[str, Any]] = Field(default_factory=list)
    responsive_observations: list[dict[str, Any]] = Field(default_factory=list)
    evidence_records: list[VisualEvidenceRecord] = Field(default_factory=list)
    page_metadata: dict[str, Any] = Field(default_factory=dict)


class VisualAnalysisContext(BaseModel):
    """Validated, normalized multi-page visual analysis context ready for evaluation."""

    crawl_run_id: str
    visual_run_id: str
    target_origin: str
    declared_language: Optional[str] = "ar"
    business_context: dict[str, Any] = Field(default_factory=dict)
    pages: list[PageAnalysisContext] = Field(default_factory=list)
    evidence_index: dict[str, VisualEvidenceRecord] = Field(default_factory=dict)
    screenshot_files: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class VisualIdentityContextBuilder:
    """Loads, validates, and normalizes visual evidence artifacts into an auditable context."""

    def __init__(self, base_dir: str = "runs"):
        self.base_dir = Path(base_dir)

    def build_context(
        self,
        visual_run_id: str,
        crawl_run_id: Optional[str] = None,
        max_pages: int = 8,
    ) -> VisualAnalysisContext:
        """Locate artifacts, verify checksums, and assemble a validated analysis context."""
        logger.info("Building visual analysis context for visual_run_id=%s", visual_run_id)

        # 1. Resolve run directories
        visual_dir, resolved_crawl_id = self._resolve_visual_dir(visual_run_id, crawl_run_id)
        crawl_file = self.base_dir / resolved_crawl_id / "crawl.json"
        if not crawl_file.exists() and crawl_run_id:
            alt = self.base_dir / crawl_run_id / "crawl.json"
            if alt.exists():
                crawl_file = alt
                resolved_crawl_id = crawl_run_id

        visual_file = visual_dir / "visual.json"

        if not visual_file.exists():
            raise ContextValidationError(f"Missing visual.json artifact at {visual_file}")
        if not crawl_file.exists():
            raise ContextValidationError(f"Missing crawl.json artifact at {crawl_file}")

        # 2. Load and validate models
        try:
            visual_result = VisualCaptureResult.model_validate_json(visual_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ContextValidationError(f"Malformed visual.json artifact: {exc}") from exc

        try:
            crawl_result = CrawlResult.model_validate_json(crawl_file.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ContextValidationError(f"Malformed crawl.json artifact: {exc}") from exc

        # 3. Verify run ID alignment
        if visual_result.crawl_run_id != resolved_crawl_id:
            raise ContextValidationError(
                f"Crawl run ID mismatch: visual references {visual_result.crawl_run_id}, crawl is {resolved_crawl_id}"
            )

        # 4. Extract business context from Phase 02
        seed_page = crawl_result.pages[0] if crawl_result.pages else None
        business_context = {
            "canonical_origin": crawl_result.website_info.canonical_origin,
            "declared_language": crawl_result.website_info.declared_language,
            "title": seed_page.metadata.title if seed_page else None,
            "description": seed_page.metadata.description if seed_page else None,
            "headings": [h.model_dump() for h in (seed_page.headings if seed_page else [])],
            "total_crawled_pages": len(crawl_result.pages),
        }

        # 5. Process pages and verify screenshot integrity
        eligible_pages: list[VisualPageResult] = visual_result.pages[:max_pages]
        page_contexts: list[PageAnalysisContext] = []
        global_evidence_index: dict[str, VisualEvidenceRecord] = {}
        verified_screenshots: list[str] = []
        warnings: list[str] = []

        for p_idx, page in enumerate(eligible_pages):
            # Verify desktop screenshots
            valid_desktop_shots = []
            for shot in page.desktop_screenshots:
                if shot.success and shot.file_path:
                    shot_path = Path(shot.file_path)
                    if not shot_path.is_absolute():
                        shot_path = self.base_dir.parent / shot_path

                    if not shot_path.exists():
                        warnings.append(f"Missing screenshot file: {shot.file_path}")
                        continue

                    # Validate SHA-256 checksum
                    file_bytes = shot_path.read_bytes()
                    computed_hash = hashlib.sha256(file_bytes).hexdigest()
                    if computed_hash != shot.sha256:
                        raise ContextValidationError(
                            f"Corrupted screenshot checksum for {shot.file_path}: expected {shot.sha256}, got {computed_hash}"
                        )

                    # Validate real dimensions with Pillow
                    with Image.open(shot_path) as img:
                        w, h = img.size
                        if (w, h) != (shot.width_px, shot.height_px):
                            warnings.append(
                                f"Dimension mismatch for {shot.file_path}: metadata ({shot.width_px}x{shot.height_px}) vs image ({w}x{h})"
                            )

                    valid_desktop_shots.append(shot.model_dump())
                    verified_screenshots.append(str(shot_path.resolve()))

            # Verify mobile screenshots
            valid_mobile_shots = []
            for shot in page.mobile_screenshots:
                if shot.success and shot.file_path:
                    shot_path = Path(shot.file_path)
                    if not shot_path.is_absolute():
                        shot_path = self.base_dir.parent / shot_path

                    if not shot_path.exists():
                        warnings.append(f"Missing mobile screenshot file: {shot.file_path}")
                        continue

                    file_bytes = shot_path.read_bytes()
                    computed_hash = hashlib.sha256(file_bytes).hexdigest()
                    if computed_hash != shot.sha256:
                        raise ContextValidationError(
                            f"Corrupted mobile screenshot checksum for {shot.file_path}: expected {shot.sha256}, got {computed_hash}"
                        )

                    with Image.open(shot_path) as img:
                        w, h = img.size
                        if (w, h) != (shot.width_px, shot.height_px):
                            warnings.append(
                                f"Dimension mismatch for {shot.file_path}: metadata ({shot.width_px}x{shot.height_px}) vs image ({w}x{h})"
                            )

                    valid_mobile_shots.append(shot.model_dump())
                    verified_screenshots.append(str(shot_path.resolve()))

            # Match crawl metadata
            matching_crawl_page = next((cp for cp in crawl_result.pages if cp.final_url == page.page_url), None)
            crawl_meta = matching_crawl_page.metadata.model_dump() if matching_crawl_page else {}

            # Index evidence records
            for ev in page.evidence_records:
                global_evidence_index[ev.evidence_id] = ev

            page_ctx = PageAnalysisContext(
                page_url=page.page_url,
                safe_page_id=page.safe_page_id,
                status=page.status,
                desktop_screenshots=valid_desktop_shots,
                mobile_screenshots=valid_mobile_shots,
                colors=[c.model_dump() for c in page.colors],
                typography=[t.model_dump() for t in page.typography],
                layout_records=[layout.model_dump() for layout in page.layout_records],
                dom_elements=[d.model_dump() for d in page.dom_elements],
                responsive_observations=[r.model_dump() for r in page.responsive_observations],
                evidence_records=page.evidence_records,
                page_metadata=crawl_meta,
            )
            page_contexts.append(page_ctx)

        logger.info(
            "Context assembled: %d pages, %d screenshots, %d evidence records",
            len(page_contexts),
            len(verified_screenshots),
            len(global_evidence_index),
        )

        return VisualAnalysisContext(
            crawl_run_id=resolved_crawl_id,
            visual_run_id=visual_run_id,
            target_origin=visual_result.target_origin,
            declared_language=crawl_result.website_info.declared_language or "ar",
            business_context=business_context,
            pages=page_contexts,
            evidence_index=global_evidence_index,
            screenshot_files=verified_screenshots,
            warnings=warnings,
        )

    def _resolve_visual_dir(
        self,
        visual_run_id: str,
        crawl_run_id: Optional[str] = None,
    ) -> tuple[Path, str]:
        """Find the visual run directory on disk and return (directory_path, crawl_run_id)."""
        if crawl_run_id:
            candidate = self.base_dir / crawl_run_id / "visual" / visual_run_id
            if candidate.exists():
                return candidate, crawl_run_id

        # Search across all runs/ directories
        if self.base_dir.exists():
            for c_dir in self.base_dir.iterdir():
                if c_dir.is_dir():
                    candidate = c_dir / "visual" / visual_run_id
                    if candidate.exists():
                        return candidate, c_dir.name

        raise ContextValidationError(f"Could not locate visual run directory for visual_run_id={visual_run_id}")
