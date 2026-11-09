"""Discovery CrewAI Flow orchestrating website discovery and crawl pipeline."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.discovery.service import WebsiteDiscoveryService
from site_dna.schemas.discovery import CrawlRequest, CrawlResult

logger = get_logger(__name__)


class DiscoveryFlowState(BaseModel):
    """Pydantic state tracked across the website discovery flow."""

    run_id: str = Field(default="", description="Unique execution run identifier")
    target_url: str = Field(default="", description="Target website URL")
    max_pages: Optional[int] = Field(default=None, description="Max pages constraint")
    max_depth: Optional[int] = Field(default=None, description="Max depth constraint")
    execution_status: str = Field(default="pending", description="pending, running, completed, failed")
    crawl_result: Optional[CrawlResult] = Field(default=None, description="Extracted crawl result")
    started_at: Optional[str] = Field(default=None, description="ISO timestamp")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class DiscoveryFlow(Flow[DiscoveryFlowState]):
    """CrewAI Flow orchestrating website discovery and evidence collection."""

    def __init__(
        self,
        target_url: str,
        max_pages: Optional[int] = None,
        max_depth: Optional[int] = None,
        settings: Optional[Settings] = None,
    ):
        super().__init__()
        self._target_url = target_url
        self._max_pages = max_pages
        self._max_depth = max_depth
        self._settings = settings or get_settings()

    @start()
    def initialize_discovery(self) -> str:
        """Step 1: Initialize flow state and validate input parameters."""
        self.state.run_id = f"disc-{uuid.uuid4().hex[:8]}"
        self.state.target_url = self._target_url
        self.state.max_pages = self._max_pages
        self.state.max_depth = self._max_depth
        self.state.started_at = datetime.now(timezone.utc).isoformat()
        self.state.execution_status = "initialized"

        logger.info("DiscoveryFlow initialized: run_id=%s, url=%s", self.state.run_id, self.state.target_url)
        return self.state.run_id

    @listen(initialize_discovery)
    def execute_discovery(self, run_id: str) -> DiscoveryFlowState:
        """Step 2: Execute deterministic crawler service and store structured crawl result."""
        self.state.execution_status = "running"
        logger.info("Executing crawler for run_id=%s, url=%s", run_id, self.state.target_url)

        try:
            service = WebsiteDiscoveryService(settings=self._settings)
            request = CrawlRequest(
                url=self.state.target_url,
                max_pages=self.state.max_pages,
                max_depth=self.state.max_depth,
            )
            result = service.discover_sync(request)
            self.state.crawl_result = result
            self.state.execution_status = "completed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            logger.info(
                "DiscoveryFlow completed successfully: run_id=%s, pages_crawled=%d",
                run_id,
                result.statistics.total_pages_crawled,
            )
        except Exception as exc:
            self.state.execution_status = "failed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            self.state.error_message = f"{type(exc).__name__}: {str(exc)}"
            logger.error("DiscoveryFlow failed for run_id=%s: %s", run_id, self.state.error_message)
            raise

        return self.state
