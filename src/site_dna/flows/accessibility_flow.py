"""CrewAI Flow orchestrating AI Web Accessibility, Inclusive Experience & WCAG 2.2 Intelligence (Phase 10)."""

import asyncio
import concurrent.futures
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.accessibility import (
    AccessibilityAnalysisRequest,
    AccessibilityFinding,
    AccessibilityReport,
    AccessibilityScore,
)

logger = get_logger("flows.accessibility_flow")


class AccessibilityFlowState(BaseModel):
    """Flow state tracking the accessibility analysis execution stages."""

    flow_id: str = Field(default_factory=lambda: f"flow-a11y-{uuid.uuid4().hex[:8]}")
    crawl_run_id: str = ""
    visual_run_id: Optional[str] = None
    ux_run_id: Optional[str] = None
    target_url: str = ""
    language: str = "ar"
    started_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    current_stage: str = "initialized"
    execution_status: str = Field(default="pending", description="pending, running, completed, failed")
    report: Optional[AccessibilityReport] = None
    error: Optional[str] = None


class AccessibilityFlow(Flow[AccessibilityFlowState]):
    """CrewAI Flow managing end-to-end accessibility evaluation and AI interpretation."""

    def __init__(
        self,
        crawl_run_id: Optional[str] = None,
        visual_run_id: Optional[str] = None,
        ux_run_id: Optional[str] = None,
        language: str = "ar",
        max_pages: int = 8,
        offline_mode: bool = False,
        deterministic_only: bool = False,
        settings: Optional[Settings] = None,
    ):
        super().__init__()
        self.settings = settings or get_settings()
        if crawl_run_id:
            self.state.crawl_run_id = crawl_run_id
        if visual_run_id:
            self.state.visual_run_id = visual_run_id
        if ux_run_id:
            self.state.ux_run_id = ux_run_id
        self.state.language = language
        self.max_pages = max_pages
        self.offline_mode = offline_mode
        self.deterministic_only = deterministic_only

    @start()
    def initialize_analysis(self) -> dict[str, Any]:
        """Validate input parameters and prepare flow state."""
        self.state.current_stage = "loading_evidence"
        self.state.execution_status = "running"
        logger.info("Starting AccessibilityFlow [%s] for crawl_run_id=%s", self.state.flow_id, self.state.crawl_run_id)
        return {"status": "initialized", "flow_id": self.state.flow_id}

    @listen(initialize_analysis)
    def execute_analysis(self) -> dict[str, Any]:
        """Run the core accessibility service synchronously within thread executor."""
        from site_dna.analysis.accessibility.service import AccessibilityService

        self.state.current_stage = "evaluating_wcag"
        service = AccessibilityService(settings=self.settings)
        req = AccessibilityAnalysisRequest(
            crawl_run_id=self.state.crawl_run_id,
            visual_run_id=self.state.visual_run_id,
            ux_run_id=self.state.ux_run_id,
            language=self.state.language,
            max_pages=self.max_pages,
            offline_mode=self.offline_mode,
            deterministic_only=self.deterministic_only,
            save_results=True,
        )

        try:
            with concurrent.futures.ThreadPoolExecutor() as pool:
                report = pool.submit(asyncio.run, service.analyze_accessibility(req)).result()
            self.state.report = report
            self.state.current_stage = "completed"
            self.state.execution_status = "completed"
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
        except Exception as exc:
            logger.error("Accessibility flow failed: %s", exc, exc_info=True)
            self.state.current_stage = "failed"
            self.state.execution_status = "failed"
            self.state.error = str(exc)

        return self.state

    def run_ai_interpretation(
        self,
        target_url: str,
        findings: list[AccessibilityFinding],
        scores: AccessibilityScore,
    ) -> Optional[str]:
        """Generate qualitative AI accessibility commentary using Gemini 3.6 Flash."""
        if not self.settings.is_gemini_configured():
            logger.info("Gemini API key not configured; skipping AI interpretation.")
            return None

        from site_dna.agents.accessibility_agent import create_accessibility_agent

        agent = create_accessibility_agent(settings=self.settings)
        prompt = (
            f"Target URL: {target_url}\n"
            f"Accessibility Evidence Score: {scores.overall_score}/100 ({scores.score_label_ar})\n"
            f"Confirmed Barriers Count: {len([f for f in findings if f.assessment_state == 'confirmed_failure'])}\n\n"
            "Summarize the most critical accessibility barriers in 2 concise Arabic paragraphs. "
            "Focus only on verified findings. Do not make claims of full WCAG conformance."
        )

        try:
            response = agent.llm.call(prompt)
            return str(response)
        except Exception as e:
            logger.warning("Gemini AI accessibility interpretation unavailable: %s", e)
            return None
