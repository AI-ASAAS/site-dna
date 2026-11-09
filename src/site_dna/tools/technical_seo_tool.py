"""CrewAI BaseTool wrapper for Technical SEO & Performance Analysis."""

from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from site_dna.analysis.technical_seo.service import TechnicalSEOAnalysisService
from site_dna.schemas.technical_seo import TechnicalSEOAnalysisRequest


class TechnicalSEOToolInput(BaseModel):
    """Input parameters for Technical SEO and Performance analysis tool."""

    crawl_run_id: str = Field(description="Existing crawl run identifier (e.g. 98b5cd6a-3225-4c00-9b75-0d13061d85f1)")
    visual_run_id: Optional[str] = Field(default=None, description="Optional associated visual capture run ID")
    max_pages: Optional[int] = Field(default=8, description="Maximum pages to analyze")
    language: Optional[str] = Field(default="ar", description="Language of report ('ar' or 'en')")
    include_performance: Optional[bool] = Field(
        default=False, description="Whether to run live browser performance tests"
    )
    save_results: Optional[bool] = Field(default=True, description="Whether to persist output reports")


class TechnicalSEOTool(BaseTool):
    """CrewAI tool auditing technical crawlability, indexability, canonicals, metadata, and performance."""

    name: str = "technical_seo_analysis_tool"
    description: str = (
        "Audits technical website SEO, crawl accessibility, indexability directives, canonical tags, "
        "XML sitemaps, structured data, JavaScript/mobile rendering parity, and website performance."
    )
    args_schema: type[BaseModel] = TechnicalSEOToolInput

    def _run(
        self,
        crawl_run_id: str,
        visual_run_id: Optional[str] = None,
        max_pages: Optional[int] = 8,
        language: Optional[str] = "ar",
        include_performance: Optional[bool] = False,
        save_results: Optional[bool] = True,
    ) -> str:
        """Execute Technical SEO analysis synchronously and return JSON report string."""
        request = TechnicalSEOAnalysisRequest(
            crawl_run_id=crawl_run_id,
            visual_run_id=visual_run_id,
            max_pages=max_pages or 8,
            language=language or "ar",
            include_performance=bool(include_performance),
            save_results=bool(save_results),
        )

        service = TechnicalSEOAnalysisService()
        report = service.analyze_technical_seo(request)
        overall_score_str = f"{report.overall_score:.1f}" if report.overall_score is not None else "N/A"
        return (
            f"Technical SEO analysis finished successfully. "
            f"Run ID: {report.analysis_run_id}, Target: {report.target_origin}, "
            f"Overall Score: {overall_score_str}/100, Findings: {len(report.findings)}, "
            f"Recommendations: {len(report.recommendations)}, Status: {report.analysis_status}."
        )
