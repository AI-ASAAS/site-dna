"""CrewAI BaseTool wrapper for Content & Marketing Intelligence Analysis."""

from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from site_dna.analysis.content_marketing.service import ContentMarketingAnalysisService
from site_dna.schemas.content_marketing import ContentAnalysisRequest


class ContentMarketingToolInput(BaseModel):
    """Input parameters for Content & Marketing Intelligence analysis tool."""

    crawl_run_id: str = Field(description="Existing crawl run identifier (e.g. 98b5cd6a-3225-4c00-9b75-0d13061d85f1)")
    visual_run_id: Optional[str] = Field(default=None, description="Optional associated visual capture run ID")
    max_pages: Optional[int] = Field(default=8, description="Maximum pages to analyze")
    language: Optional[str] = Field(default="ar", description="Language of report ('ar' or 'en')")
    save_results: Optional[bool] = Field(default=True, description="Whether to persist report artifacts")


class ContentMarketingTool(BaseTool):
    """CrewAI tool auditing website messaging, value proposition, CTAs, and copy proposals."""

    name: str = "content_marketing_analysis_tool"
    description: str = (
        "Audits website content, value proposition clarity, headline messaging, product/service descriptions, "
        "CTA actionability, credibility claims, and generates grounded copy rewrite proposals."
    )
    args_schema: type[BaseModel] = ContentMarketingToolInput

    def _run(
        self,
        crawl_run_id: str,
        visual_run_id: Optional[str] = None,
        max_pages: Optional[int] = 8,
        language: Optional[str] = "ar",
        save_results: Optional[bool] = True,
    ) -> str:
        """Execute content marketing analysis synchronously and return JSON report string."""
        request = ContentAnalysisRequest(
            crawl_run_id=crawl_run_id,
            visual_run_id=visual_run_id,
            max_pages=max_pages or 8,
            language=language or "ar",
            save_results=True if save_results is None else save_results,
        )

        service = ContentMarketingAnalysisService()
        report = service.analyze(request)
        return report.model_dump_json(indent=2)
