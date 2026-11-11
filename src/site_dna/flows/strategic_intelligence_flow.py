"""CrewAI Flow orchestrating Cross-Agent Strategic Intelligence & Unified Action Roadmap (Phase 11)."""

import asyncio
import concurrent.futures
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from site_dna.analysis.strategic_intelligence.service import StrategicIntelligenceService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.strategic_intelligence import (
    StrategicAnalysisRequest,
    StrategicIntelligenceReport,
)

logger = get_logger("flows.strategic_intelligence_flow")


class StrategicFlowState(BaseModel):
    """Flow state tracking the strategic intelligence execution stages."""

    flow_id: str = Field(default_factory=lambda: f"flow-strat-{uuid.uuid4().hex[:8]}")
    crawl_run_id: str = ""
    target_url: str = ""
    language: str = "ar"
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    current_stage: str = "initialized"
    execution_status: str = Field(default="pending", description="pending, running, completed, failed")
    report: Optional[StrategicIntelligenceReport] = None
    error: Optional[str] = None


class StrategicIntelligenceFlow(Flow[StrategicFlowState]):
    """CrewAI Flow managing end-to-end multi-agent cross-synthesis and roadmap generation."""

    def __init__(
        self,
        crawl_run_id: Optional[str] = None,
        language: str = "ar",
        max_actions: int = 50,
        offline_mode: bool = False,
        deterministic_only: bool = False,
        settings: Optional[Settings] = None,
    ):
        super().__init__()
        self.settings = settings or get_settings()
        if crawl_run_id:
            self.state.crawl_run_id = crawl_run_id
        self.state.language = language
        self.max_actions = max_actions
        self.offline_mode = offline_mode
        self.deterministic_only = deterministic_only

    @start()
    def initialize_strategic_synthesis(self) -> dict[str, Any]:
        """Step 1: Validate crawl run ID and initialize synthesis state."""
        self.state.current_stage = "validating_sources"
        self.state.execution_status = "running"
        logger.info("Starting StrategicIntelligenceFlow for crawl_run_id: %s", self.state.crawl_run_id)
        return {"crawl_run_id": self.state.crawl_run_id, "status": "validated"}

    @listen(initialize_strategic_synthesis)
    def execute_cross_agent_synthesis(self, prev_step: dict[str, Any]) -> dict[str, Any]:
        """Step 2: Ingest all prior phase artifacts, normalize, deduplicate, and build roadmap."""
        self.state.current_stage = "synthesizing_roadmap"

        service = StrategicIntelligenceService(settings=self.settings)
        req = StrategicAnalysisRequest(
            crawl_run_id=self.state.crawl_run_id,
            language=self.state.language,
            max_actions=self.max_actions,
            deterministic_only=self.deterministic_only or self.offline_mode,
            save_results=True,
        )

        try:
            # Handle async execution within synchronous CrewAI Flow method
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    report = executor.submit(asyncio.run, service.analyze_strategy(req)).result()
            else:
                report = asyncio.run(service.analyze_strategy(req))

            self.state.report = report
            self.state.target_url = report.target_url
            self.state.execution_status = "completed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            self.state.current_stage = "completed"

            return {
                "status": "success",
                "strategic_run_id": report.strategic_run_id,
                "actions_count": len(report.actions),
            }
        except Exception as e:
            logger.error("Strategic synthesis flow failed: %s", e, exc_info=True)
            self.state.execution_status = "failed"
            self.state.error = str(e)
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            return {"status": "failed", "error": str(e)}

    def execute_analysis(self) -> StrategicFlowState:
        """Run the Flow and return the resulting state."""
        self.kickoff()
        return self.state
