"""CrewAI BaseTool wrapper for Site DNA Visual Evidence Collection."""

from pathlib import Path
from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from site_dna.schemas.discovery import CrawlResult
from site_dna.visual.service import VisualCollectionService


class VisualEvidenceInput(BaseModel):
    """Input parameters for Visual Evidence Collection tool."""

    crawl_run_id: Optional[str] = Field(default=None, description="Existing crawl run identifier")
    crawl_file: Optional[str] = Field(default=None, description="Path to crawl.json artifact")
    max_pages: Optional[int] = Field(default=None, description="Maximum pages to render and capture")


class VisualEvidenceTool(BaseTool):
    """CrewAI tool providing deterministic, secure browser rendering and visual evidence collection."""

    name: str = "visual_evidence_tool"
    description: str = (
        "Renders website pages in desktop and mobile browser contexts, collects screenshots, "
        "and extracts computed CSS, color palettes, typography, and layout evidence."
    )
    args_schema: type[BaseModel] = VisualEvidenceInput

    def _run(
        self,
        crawl_run_id: Optional[str] = None,
        crawl_file: Optional[str] = None,
        max_pages: Optional[int] = None,
    ) -> str:
        """Execute visual collection synchronously and return JSON-formatted capture summary."""
        target_path: Optional[Path] = None

        if crawl_file:
            target_path = Path(crawl_file)
        elif crawl_run_id:
            target_path = Path("runs") / crawl_run_id / "crawl.json"

        if not target_path or not target_path.exists():
            return f'{{"error": "Crawl file not found at {target_path}"}}'

        crawl_data = target_path.read_text(encoding="utf-8")
        crawl_result = CrawlResult.model_validate_json(crawl_data)

        service = VisualCollectionService()
        result = service.collect_visual_evidence_sync(crawl_result, max_pages=max_pages)
        return result.model_dump_json(indent=2)
