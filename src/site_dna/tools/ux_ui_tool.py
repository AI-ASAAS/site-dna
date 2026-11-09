"""CrewAI BaseTool wrapper for UX/UI and Usability Intelligence Analysis."""

from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from site_dna.analysis.ux_ui.service import UXAnalysisService
from site_dna.schemas.ux_ui import UXAnalysisRequest


class UXUIToolInput(BaseModel):
    """Input parameters for UX/UI Analysis tool."""

    visual_run_id: str = Field(description="Existing visual run identifier (e.g. vis-e6b6128de9b5)")
    crawl_run_id: Optional[str] = Field(default=None, description="Optional associated crawl run identifier")
    max_pages: Optional[int] = Field(default=8, description="Maximum pages to analyze")
    language: Optional[str] = Field(default="ar", description="Language of report ('ar' or 'en')")
    save_results: Optional[bool] = Field(default=True, description="Whether to persist report artifacts")


class UXUITool(BaseTool):
    """CrewAI tool evaluating website UX/UI, navigation, mobile touch targets, forms, and accessibility."""

    name: str = "ux_ui_analysis_tool"
    description: str = (
        "Evaluates website UX/UI usability, navigation graph, mobile touch targets, form inputs, "
        "and basic accessibility using evidence-grounded DOM and visual records, returning explainable "
        "rubric scores, validated findings, and prioritized recommendations."
    )
    args_schema: type[BaseModel] = UXUIToolInput

    def _run(
        self,
        visual_run_id: str,
        crawl_run_id: Optional[str] = None,
        max_pages: Optional[int] = 8,
        language: Optional[str] = "ar",
        save_results: Optional[bool] = True,
    ) -> str:
        """Execute UX/UI analysis synchronously and return JSON report string."""
        request = UXAnalysisRequest(
            visual_run_id=visual_run_id,
            crawl_run_id=crawl_run_id,
            max_pages=max_pages or 8,
            language=language or "ar",
            save_results=True if save_results is None else save_results,
        )

        service = UXAnalysisService()
        report = service.analyze_ux_sync(request)
        return report.model_dump_json(indent=2)
