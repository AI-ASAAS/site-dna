"""Local file and artifact storage manager for visual capture outputs and manifests."""

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from site_dna.core.logging import get_logger
from site_dna.schemas.visual import VisualCaptureResult

logger = get_logger("visual.storage")


def generate_safe_page_id(url: str, index: int = 0) -> str:
    """Generate a sanitized, traversal-safe directory name for a page URL."""
    # Clean URL path slug
    clean_slug = re.sub(r"[^a-zA-Z0-9_-]", "_", url.split("://")[-1]).strip("_")[:30]
    hash_suffix = hashlib.sha256(url.encode("utf-8")).hexdigest()[:8]
    return f"page_{index:02d}_{clean_slug}_{hash_suffix}"


class VisualStorageManager:
    """Manages directory hierarchy and persistence for screenshots and visual JSON artifacts."""

    def __init__(
        self,
        crawl_run_id: str,
        visual_run_id: str,
        base_dir: str = "runs",
    ):
        self.crawl_run_id = crawl_run_id
        self.visual_run_id = visual_run_id
        self.root_visual_dir = Path(base_dir) / crawl_run_id / "visual" / visual_run_id
        self.pages_dir = self.root_visual_dir / "pages"
        self.pages_dir.mkdir(parents=True, exist_ok=True)

    def get_page_dir(self, safe_page_id: str) -> Path:
        """Resolve and create isolated directory for a specific page's screenshots."""
        # Sanitize to prevent path traversal
        clean_id = re.sub(r"[^a-zA-Z0-9_-]", "_", safe_page_id)
        page_path = self.pages_dir / clean_id
        page_path.mkdir(parents=True, exist_ok=True)
        return page_path

    def save_visual_result(self, result: VisualCaptureResult) -> Path:
        """Save complete VisualCaptureResult model as visual.json."""
        target_file = self.root_visual_dir / "visual.json"
        target_file.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        logger.info("Saved visual capture result to %s", target_file)
        return target_file

    def save_manifest(self, result: VisualCaptureResult) -> Path:
        """Generate and save manifest.json summarizing all artifacts and checksums."""
        manifest_data: dict[str, Any] = {
            "schema_version": result.schema_version,
            "crawl_run_id": result.crawl_run_id,
            "visual_run_id": result.visual_run_id,
            "status": result.status,
            "target_origin": result.target_origin,
            "created_at": result.created_at.isoformat(),
            "statistics": result.statistics.model_dump(mode="json"),
            "pages": [],
        }

        for page in result.pages:
            page_summary = {
                "page_url": page.page_url,
                "safe_page_id": page.safe_page_id,
                "status": page.status,
                "desktop_screenshots": [s.model_dump(mode="json") for s in page.desktop_screenshots],
                "mobile_screenshots": [s.model_dump(mode="json") for s in page.mobile_screenshots],
                "dom_elements_count": len(page.dom_elements),
                "computed_styles_count": len(page.computed_styles),
                "colors_count": len(page.colors),
                "typography_count": len(page.typography),
                "layout_count": len(page.layout_records),
                "responsive_observations_count": len(page.responsive_observations),
                "evidence_count": len(page.evidence_records),
                "errors": page.render_errors,
            }
            manifest_data["pages"].append(page_summary)

        manifest_file = self.root_visual_dir / "manifest.json"
        manifest_file.write_text(json.dumps(manifest_data, indent=2), encoding="utf-8")
        logger.info("Saved visual manifest to %s", manifest_file)
        return manifest_file
