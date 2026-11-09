"""CrewAI Flow orchestrating AI Competitor Intelligence benchmarking and reporting."""

import asyncio
import uuid
from datetime import datetime, timezone
from typing import Optional

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from site_dna.analysis.competitor_intelligence.service import CompetitorIntelligenceService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import (
    CompetitorAnalysisRequest,
    CompetitorIntelligenceReport,
)

logger = get_logger("flows.competitor_intelligence_flow")


class CompetitorIntelligenceFlowState(BaseModel):
    """Pydantic state tracked across the Competitor Intelligence flow."""

    comparison_run_id: str = Field(default="", description="Unique comparison run identifier")
    primary_run_id: Optional[str] = Field(default=None, description="Primary run identifier")
    competitor_count: int = Field(default=0, description="Number of competitors benchmarked")
    execution_status: str = Field(default="pending", description="pending, running, completed, failed")
    report: Optional[CompetitorIntelligenceReport] = Field(default=None, description="Structured final report")
    started_at: Optional[str] = Field(default=None, description="ISO timestamp")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class CompetitorIntelligenceFlow(Flow[CompetitorIntelligenceFlowState]):
    """CrewAI Flow orchestrating multi-site competitor benchmarking."""

    def __init__(
        self,
        primary_run_id: Optional[str] = None,
        primary_url: Optional[str] = None,
        competitor_urls: Optional[list[str]] = None,
        competitor_run_ids: Optional[list[str]] = None,
        max_pages_per_site: int = 5,
        language: str = "ar",
        offline_mode: bool = False,
        deterministic_only: bool = False,
        base_dir: str = "runs",
        settings: Optional[Settings] = None,
    ):
        super().__init__()
        self._primary_run_id = primary_run_id
        self._primary_url = primary_url
        self._competitor_urls = competitor_urls or []
        self._competitor_run_ids = competitor_run_ids or []
        self._max_pages_per_site = max_pages_per_site
        self._language = language
        self._offline_mode = offline_mode
        self._deterministic_only = deterministic_only
        self._base_dir = base_dir
        self._settings = settings or get_settings()

    @start()
    def initialize_analysis(self) -> str:
        """Step 1: Initialize flow state and identifiers."""
        self.state.comparison_run_id = f"flow-cmp-{uuid.uuid4().hex[:8]}"
        self.state.primary_run_id = self._primary_run_id
        self.state.competitor_count = len(self._competitor_urls) + len(self._competitor_run_ids)
        self.state.started_at = datetime.now(timezone.utc).isoformat()
        self.state.execution_status = "initialized"

        logger.info(
            "CompetitorIntelligenceFlow initialized: comparison_run_id=%s, competitors=%d",
            self.state.comparison_run_id,
            self.state.competitor_count,
        )
        return self.state.comparison_run_id

    @listen(initialize_analysis)
    def execute_analysis(self, comparison_run_id: str) -> CompetitorIntelligenceFlowState:
        """Step 2: Execute Competitor Intelligence analysis service and store report."""
        self.state.execution_status = "running"
        logger.info("Executing competitor benchmark for %s", comparison_run_id)

        try:
            request = CompetitorAnalysisRequest(
                primary_run_id=self._primary_run_id,
                primary_url=self._primary_url,
                competitor_urls=self._competitor_urls,
                competitor_run_ids=self._competitor_run_ids,
                max_pages_per_site=self._max_pages_per_site,
                language=self._language,
                offline_mode=self._offline_mode,
                deterministic_only=self._deterministic_only,
                save_results=True,
            )

            service = CompetitorIntelligenceService(base_dir=self._base_dir, settings=self._settings)

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

            self.state.report = report
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            self.state.execution_status = "completed"
            logger.info("CompetitorIntelligenceFlow successfully completed: %s", comparison_run_id)

        except Exception as exc:
            logger.error("CompetitorIntelligenceFlow failed: %s", exc, exc_info=True)
            self.state.execution_status = "failed"
            self.state.error_message = str(exc)
            self.state.completed_at = datetime.now(timezone.utc).isoformat()

        return self.state
