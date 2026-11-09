"""CrewAI Flow orchestrating AI visual identity analysis and reporting."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from site_dna.analysis.visual_identity.service import VisualIdentityAnalysisService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.visual_identity import VisualIdentityAnalysisRequest, VisualIdentityReport

logger = get_logger("flows.visual_identity_flow")


class VisualIdentityFlowState(BaseModel):
    """Pydantic state tracked across the visual identity analysis flow."""

    analysis_run_id: str = Field(default="", description="Unique analysis run identifier")
    visual_run_id: str = Field(default="", description="Source visual run identifier")
    crawl_run_id: Optional[str] = Field(default=None, description="Source crawl run identifier")
    execution_status: str = Field(default="pending", description="pending, running, completed, failed")
    report: Optional[VisualIdentityReport] = Field(default=None, description="Structured final report")
    started_at: Optional[str] = Field(default=None, description="ISO timestamp")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class VisualIdentityFlow(Flow[VisualIdentityFlowState]):
    """CrewAI Flow orchestrating visual identity evidence evaluation and reporting."""

    def __init__(
        self,
        visual_run_id: str,
        crawl_run_id: Optional[str] = None,
        max_pages: int = 8,
        language: str = "ar",
        offline_mode: bool = False,
        base_dir: str = "runs",
        settings: Optional[Settings] = None,
    ):
        super().__init__()
        self._visual_run_id = visual_run_id
        self._crawl_run_id = crawl_run_id
        self._max_pages = max_pages
        self._language = language
        self._offline_mode = offline_mode
        self._base_dir = base_dir
        self._settings = settings or get_settings()

    @start()
    def initialize_analysis(self) -> str:
        """Step 1: Initialize flow state and identifiers."""
        self.state.analysis_run_id = f"flow-vi-{uuid.uuid4().hex[:8]}"
        self.state.visual_run_id = self._visual_run_id
        self.state.crawl_run_id = self._crawl_run_id
        self.state.started_at = datetime.now(timezone.utc).isoformat()
        self.state.execution_status = "initialized"

        logger.info(
            "VisualIdentityFlow initialized: analysis_run_id=%s, visual_run_id=%s",
            self.state.analysis_run_id,
            self.state.visual_run_id,
        )
        return self.state.analysis_run_id

    @listen(initialize_analysis)
    def execute_analysis(self, analysis_run_id: str) -> VisualIdentityFlowState:
        """Step 2: Execute visual identity analysis service and store report."""
        self.state.execution_status = "running"
        logger.info("Executing visual identity analysis for visual_run_id=%s", self.state.visual_run_id)

        try:
            service = VisualIdentityAnalysisService(settings=self._settings, base_dir=self._base_dir)
            request = VisualIdentityAnalysisRequest(
                visual_run_id=self._visual_run_id,
                crawl_run_id=self._crawl_run_id,
                max_pages=self._max_pages,
                language=self._language,
                save_results=True,
            )
            report = service.analyze_visual_identity_sync(request=request, offline_mode=self._offline_mode)
            self.state.report = report
            self.state.execution_status = "completed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            logger.info("VisualIdentityFlow completed: score=%s", report.overall_score)
        except Exception as exc:
            self.state.execution_status = "failed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            self.state.error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.error("VisualIdentityFlow failed: %s", self.state.error_message)
            raise

        return self.state
