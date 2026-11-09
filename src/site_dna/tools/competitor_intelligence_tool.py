"""CrewAI BaseTool wrapper for Site DNA Phase 08 — Competitor Intelligence."""

import asyncio
from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from site_dna.analysis.competitor_intelligence.service import CompetitorIntelligenceService
from site_dna.schemas.competitor_intelligence import CompetitorAnalysisRequest


class CompetitorIntelligenceToolInput(BaseModel):
    """Input parameters for Competitor Intelligence analysis tool."""

    primary_run_id: Optional[str] = Field(default=None, description="Existing primary website run ID")
    primary_url: Optional[str] = Field(default=None, description="Primary website URL")
    competitor_urls: list[str] = Field(
        default_factory=list,
        description="Competitor URLs to compare against",
    )
    competitor_run_ids: Optional[list[str]] = Field(
        default=None,
        description="Optional existing run IDs for competitors",
    )
    language: Optional[str] = Field(default="ar", description="Language of report ('ar' or 'en')")
    max_pages_per_site: Optional[int] = Field(default=5, description="Pages budget per site")
    save_results: Optional[bool] = Field(default=True, description="Whether to persist artifacts")
    offline_mode: Optional[bool] = Field(default=False, description="Run in offline mode")


class CompetitorIntelligenceTool(BaseTool):
    """CrewAI tool performing multi-site competitor benchmarking, feature matrices, and opportunity audits."""

    name: str = "competitor_intelligence_analysis_tool"
    description: str = (
        "Audits competitor websites against a primary website, evaluating feature matrices, "
        "pricing structures, positioning promises, UX/visual benchmarks, and strategic opportunities."
    )
    args_schema: type[BaseModel] = CompetitorIntelligenceToolInput

    def _run(
        self,
        primary_run_id: Optional[str] = None,
        primary_url: Optional[str] = None,
        competitor_urls: Optional[list[str]] = None,
        competitor_run_ids: Optional[list[str]] = None,
        language: Optional[str] = "ar",
        max_pages_per_site: Optional[int] = 5,
        save_results: Optional[bool] = True,
        offline_mode: Optional[bool] = False,
    ) -> str:
        """Execute competitor intelligence analysis synchronously and return JSON report string."""
        request = CompetitorAnalysisRequest(
            primary_run_id=primary_run_id,
            primary_url=primary_url,
            competitor_urls=competitor_urls or [],
            competitor_run_ids=competitor_run_ids,
            language=language or "ar",
            max_pages_per_site=max_pages_per_site or 5,
            save_results=True if save_results is None else save_results,
            offline_mode=bool(offline_mode),
        )

        service = CompetitorIntelligenceService()
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                report = pool.submit(asyncio.run, service.analyze_competitors(request)).result()
        else:
            report = loop.run_until_complete(service.analyze_competitors(request))

        return report.model_dump_json(indent=2)
