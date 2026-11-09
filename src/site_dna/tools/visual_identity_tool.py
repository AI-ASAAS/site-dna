"""CrewAI BaseTool wrapper for Visual Identity Analysis."""

from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from site_dna.analysis.visual_identity.service import VisualIdentityAnalysisService
from site_dna.schemas.visual_identity import VisualIdentityAnalysisRequest


class VisualIdentityToolInput(BaseModel):
    """Input parameters for Visual Identity Analysis tool."""

    visual_run_id: str = Field(description="Existing visual run identifier (e.g. vis-e6b6128de9b5)")
    crawl_run_id: Optional[str] = Field(default=None, description="Optional associated crawl run identifier")
    max_pages: Optional[int] = Field(default=8, description="Maximum pages to analyze")
    language: Optional[str] = Field(default="ar", description="Language of report ('ar' or 'en')")


class VisualIdentityTool(BaseTool):
    """CrewAI tool evaluating website visual identity, color palettes, typography, and consistency."""

    name: str = "visual_identity_analysis_tool"
    description: str = (
        "Evaluates website visual identity using actual screenshots, computed CSS, color palettes, "
        "and typography, returning explainable scores, validated findings, and prioritized recommendations."
    )
    args_schema: type[BaseModel] = VisualIdentityToolInput

    def _run(
        self,
        visual_run_id: str,
        crawl_run_id: Optional[str] = None,
        max_pages: Optional[int] = 8,
        language: Optional[str] = "ar",
    ) -> str:
        """Execute visual identity analysis synchronously and return JSON report string."""
        request = VisualIdentityAnalysisRequest(
            visual_run_id=visual_run_id,
            crawl_run_id=crawl_run_id,
            max_pages=max_pages or 8,
            language=language or "ar",
            save_results=True,
        )

        service = VisualIdentityAnalysisService()
        report = service.analyze_visual_identity_sync(request)
        return report.model_dump_json(indent=2)
