"""CrewAI Flow orchestrating AI Technical SEO & Performance Analysis."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from site_dna.analysis.technical_seo.service import TechnicalSEOAnalysisService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.technical_seo import (
    TechnicalSEOAnalysisRequest,
    TechnicalSEOReport,
)

logger = get_logger("flows.technical_seo_flow")


class TechnicalSEOFlowState(BaseModel):
    """Pydantic state tracked across the Technical SEO analysis flow."""

    analysis_run_id: str = Field(default="", description="Unique analysis run identifier")
    crawl_run_id: str = Field(default="", description="Source crawl run identifier")
    visual_run_id: Optional[str] = Field(default=None, description="Optional source visual run identifier")
    execution_status: str = Field(default="pending", description="pending, running, completed, failed")
    report: Optional[TechnicalSEOReport] = Field(default=None, description="Structured final report")
    started_at: Optional[str] = Field(default=None, description="ISO timestamp")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class TechnicalSEOFlow(Flow[TechnicalSEOFlowState]):
    """CrewAI Flow orchestrating Technical SEO, Core Web Vitals, and Performance auditing."""

    def __init__(
        self,
        crawl_run_id: str,
        visual_run_id: Optional[str] = None,
        max_pages: int = 8,
        language: str = "ar",
        include_performance: bool = False,
        include_external_metrics: bool = False,
        offline_mode: bool = False,
        deterministic_only: bool = False,
        base_dir: str = "runs",
        settings: Optional[Settings] = None,
    ):
        super().__init__()
        self._crawl_run_id = crawl_run_id
        self._visual_run_id = visual_run_id
        self._max_pages = max_pages
        self._language = language
        self._include_performance = include_performance
        self._include_external_metrics = include_external_metrics
        self._offline_mode = offline_mode
        self._deterministic_only = deterministic_only
        self._base_dir = base_dir
        self._settings = settings or get_settings()

    @start()
    def initialize_analysis(self) -> str:
        """Step 1: Initialize flow state and identifiers."""
        self.state.analysis_run_id = f"flow-seo-{uuid.uuid4().hex[:8]}"
        self.state.crawl_run_id = self._crawl_run_id
        self.state.visual_run_id = self._visual_run_id
        self.state.started_at = datetime.now(timezone.utc).isoformat()
        self.state.execution_status = "initialized"

        logger.info(
            "TechnicalSEOFlow initialized: analysis_run_id=%s, crawl_run_id=%s",
            self.state.analysis_run_id,
            self.state.crawl_run_id,
        )
        return self.state.analysis_run_id

    @listen(initialize_analysis)
    def execute_analysis(self, analysis_run_id: str) -> TechnicalSEOFlowState:
        """Step 2: Execute Technical SEO analysis service and store report."""
        self.state.execution_status = "running"
        logger.info("Executing Technical SEO analysis for crawl_run_id=%s", self.state.crawl_run_id)

        try:
            service = TechnicalSEOAnalysisService(settings=self._settings, base_dir=self._base_dir)
            request = TechnicalSEOAnalysisRequest(
                crawl_run_id=self._crawl_run_id,
                visual_run_id=self._visual_run_id,
                max_pages=self._max_pages,
                language=self._language,
                include_performance=self._include_performance,
                include_external_metrics=self._include_external_metrics,
                offline_mode=self._offline_mode,
                deterministic_only=self._deterministic_only,
            )
            report = service.analyze(request=request)
            self.state.report = report
            self.state.execution_status = "completed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            logger.info(
                "TechnicalSEOFlow completed: score=%s, status=%s",
                report.overall_score,
                report.analysis_status,
            )
        except Exception as exc:
            self.state.execution_status = "failed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            self.state.error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.error("TechnicalSEOFlow failed: %s", self.state.error_message)
            raise

        return self.state
