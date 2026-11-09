"""CrewAI Flow orchestrating AI UX/UI usability analysis and reporting."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from site_dna.analysis.ux_ui.service import UXAnalysisService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.ux_ui import UXAnalysisRequest, UXReport

logger = get_logger("flows.ux_ui_flow")


class UXFlowState(BaseModel):
    """Pydantic state tracked across the UX/UI analysis flow."""

    analysis_run_id: str = Field(default="", description="Unique analysis run identifier")
    visual_run_id: str = Field(default="", description="Source visual run identifier")
    crawl_run_id: Optional[str] = Field(default=None, description="Source crawl run identifier")
    execution_status: str = Field(default="pending", description="pending, running, completed, failed")
    report: Optional[UXReport] = Field(default=None, description="Structured final report")
    started_at: Optional[str] = Field(default=None, description="ISO timestamp")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class UXUIFlow(Flow[UXFlowState]):
    """CrewAI Flow orchestrating UX/UI usability evaluation and reporting."""

    def __init__(
        self,
        visual_run_id: str,
        crawl_run_id: Optional[str] = None,
        max_pages: int = 8,
        language: str = "ar",
        offline_mode: bool = False,
        deterministic_only: bool = False,
        base_dir: str = "runs",
        settings: Optional[Settings] = None,
    ):
        super().__init__()
        self._visual_run_id = visual_run_id
        self._crawl_run_id = crawl_run_id
        self._max_pages = max_pages
        self._language = language
        self._offline_mode = offline_mode
        self._deterministic_only = deterministic_only
        self._base_dir = base_dir
        self._settings = settings or get_settings()

    @start()
    def initialize_analysis(self) -> str:
        """Step 1: Initialize flow state and identifiers."""
        self.state.analysis_run_id = f"flow-ux-{uuid.uuid4().hex[:8]}"
        self.state.visual_run_id = self._visual_run_id
        self.state.crawl_run_id = self._crawl_run_id
        self.state.started_at = datetime.now(timezone.utc).isoformat()
        self.state.execution_status = "initialized"

        logger.info(
            "UXUIFlow initialized: analysis_run_id=%s, visual_run_id=%s",
            self.state.analysis_run_id,
            self.state.visual_run_id,
        )
        return self.state.analysis_run_id

    @listen(initialize_analysis)
    def execute_analysis(self, analysis_run_id: str) -> UXFlowState:
        """Step 2: Execute UX analysis service and store report."""
        self.state.execution_status = "running"
        logger.info("Executing UX/UI analysis for visual_run_id=%s", self.state.visual_run_id)

        try:
            service = UXAnalysisService(settings=self._settings, base_dir=self._base_dir)
            request = UXAnalysisRequest(
                visual_run_id=self._visual_run_id,
                crawl_run_id=self._crawl_run_id,
                max_pages=self._max_pages,
                language=self._language,
                save_results=True,
            )
            report = service.analyze_ux_sync(
                request=request,
                offline_mode=self._offline_mode,
                deterministic_only=self._deterministic_only,
            )
            self.state.report = report
            self.state.execution_status = "completed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            logger.info("UXUIFlow completed: score=%s, status=%s", report.overall_score, report.analysis_status)
        except Exception as exc:
            self.state.execution_status = "failed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            self.state.error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.error("UXUIFlow failed: %s", self.state.error_message)
            raise

        return self.state
