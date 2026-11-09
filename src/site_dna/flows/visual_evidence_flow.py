"""CrewAI Flow orchestrating deterministic visual evidence collection."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.discovery import CrawlResult
from site_dna.schemas.visual import VisualCaptureResult
from site_dna.visual.service import VisualCollectionService

logger = get_logger(__name__)


class VisualFlowState(BaseModel):
    """Pydantic state tracked across the visual capture flow."""

    visual_run_id: str = Field(default="", description="Unique visual run identifier")
    crawl_run_id: str = Field(default="", description="Source crawl run identifier")
    execution_status: str = Field(default="pending", description="pending, running, completed, failed")
    visual_result: Optional[VisualCaptureResult] = Field(default=None, description="Visual capture result")
    started_at: Optional[str] = Field(default=None, description="ISO timestamp")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class VisualEvidenceFlow(Flow[VisualFlowState]):
    """CrewAI Flow orchestrating visual rendering and evidence collection."""

    def __init__(
        self,
        crawl_result: CrawlResult,
        max_pages: Optional[int] = None,
        allow_test_loopback: bool = False,
        test_fixture_origin: Optional[str] = None,
        settings: Optional[Settings] = None,
    ):
        super().__init__()
        self._crawl_result = crawl_result
        self._max_pages = max_pages
        self._allow_test_loopback = allow_test_loopback
        self._test_fixture_origin = test_fixture_origin
        self._settings = settings or get_settings()

    @start()
    def initialize_visual_capture(self) -> str:
        """Step 1: Initialize flow state and record identifiers."""
        self.state.visual_run_id = f"flow-vis-{uuid.uuid4().hex[:8]}"
        self.state.crawl_run_id = self._crawl_result.run_id
        self.state.started_at = datetime.now(timezone.utc).isoformat()
        self.state.execution_status = "initialized"

        logger.info(
            "VisualEvidenceFlow initialized: visual_run_id=%s, crawl_run_id=%s",
            self.state.visual_run_id,
            self.state.crawl_run_id,
        )
        return self.state.visual_run_id

    @listen(initialize_visual_capture)
    def execute_visual_capture(self, visual_run_id: str) -> VisualFlowState:
        """Step 2: Execute visual collection service and store structured result."""
        self.state.execution_status = "running"
        logger.info("Executing visual capture for crawl_run_id=%s", self.state.crawl_run_id)

        try:
            service = VisualCollectionService(settings=self._settings)
            result = service.collect_visual_evidence_sync(
                crawl_result=self._crawl_result,
                max_pages=self._max_pages,
                allow_test_loopback=self._allow_test_loopback,
                test_fixture_origin=self._test_fixture_origin,
            )
            self.state.visual_result = result
            self.state.execution_status = "completed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            logger.info(
                "VisualEvidenceFlow completed successfully: screenshots_saved=%d",
                result.statistics.screenshots_saved,
            )
        except Exception as exc:
            self.state.execution_status = "failed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            self.state.error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.error("VisualEvidenceFlow failed: %s", self.state.error_message)
            raise

        return self.state
