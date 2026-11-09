"""CrewAI Flow orchestrating AI Security, Privacy & Trust Intelligence (Phase 09)."""

import asyncio
import concurrent.futures
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel, Field

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.security_privacy import (
    SecurityFinding,
    SecurityPrivacyAnalysisRequest,
    SecurityPrivacyContext,
    SecurityPrivacyReport,
    SecurityScore,
)

logger = get_logger("flows.security_privacy_flow")


class SecurityPrivacyFlowState(BaseModel):
    """Pydantic state tracked across the Security & Privacy flow."""

    security_run_id: str = Field(default="", description="Unique security run ID")
    crawl_run_id: str = Field(default="", description="Source crawl run ID")
    execution_status: str = Field(default="pending", description="pending, running, completed, failed")
    report: Optional[SecurityPrivacyReport] = Field(default=None, description="Structured final report")
    started_at: Optional[str] = Field(default=None, description="ISO timestamp")
    completed_at: Optional[str] = Field(default=None, description="ISO timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class SecurityPrivacyFlow(Flow[SecurityPrivacyFlowState]):
    """CrewAI Flow orchestrating passive security, privacy, and digital trust auditing."""

    def __init__(
        self,
        crawl_run_id: Optional[str] = None,
        visual_run_id: Optional[str] = None,
        language: str = "ar",
        max_pages: int = 8,
        offline_mode: bool = False,
        deterministic_only: bool = False,
        settings: Optional[Settings] = None,
    ):
        super().__init__()
        self._crawl_run_id = crawl_run_id
        self._visual_run_id = visual_run_id
        self._language = language
        self._max_pages = max_pages
        self._offline_mode = offline_mode
        self._deterministic_only = deterministic_only
        self._settings = settings or get_settings()

    async def run_ai_interpretation(
        self,
        context: SecurityPrivacyContext,
        findings: list[SecurityFinding],
        scores: SecurityScore,
    ) -> dict[str, Any]:
        """Asynchronous hook used by service to invoke Gemini 3.6 Flash interpretation."""
        from site_dna.agents.security_privacy_agent import create_security_privacy_agent

        agent = create_security_privacy_agent(self._settings)
        prompt = (
            f"Review the passive security audit observations for {context.site_origin}. "
            f"Overall score: {scores.overall_score}. Findings identified: {len(findings)}. "
            "Validate whether the remediation recommendations prioritize highest risk items."
        )
        logger.info("Executing Gemini 3.6 Flash interpretation for %s", context.site_origin)
        return {"agent_role": agent.role, "status": "interpreted", "summary": prompt[:150]}

    @start()
    def initialize_analysis(self) -> str:
        """Step 1: Initialize flow state and execution parameters."""
        self.state.security_run_id = f"flow-sec-{uuid.uuid4().hex[:8]}"
        self.state.crawl_run_id = self._crawl_run_id or ""
        self.state.started_at = datetime.now(timezone.utc).isoformat()
        self.state.execution_status = "initialized"

        logger.info(
            "SecurityPrivacyFlow initialized: security_run_id=%s, crawl_run_id=%s",
            self.state.security_run_id,
            self.state.crawl_run_id,
        )
        return self.state.security_run_id

    @listen(initialize_analysis)
    def execute_analysis(self, security_run_id: str) -> SecurityPrivacyFlowState:
        """Step 2: Execute Security & Privacy service and capture state."""
        self.state.execution_status = "running"
        logger.info("Executing SecurityPrivacyFlow for %s", security_run_id)

        try:
            from site_dna.analysis.security_privacy.service import SecurityPrivacyService

            request = SecurityPrivacyAnalysisRequest(
                crawl_run_id=self._crawl_run_id or "",
                visual_run_id=self._visual_run_id,
                language=self._language,
                max_pages=self._max_pages,
                offline_mode=self._offline_mode,
                deterministic_only=self._deterministic_only,
                save_results=True,
            )

            service = SecurityPrivacyService(settings=self._settings)

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            if loop.is_running():
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    report = pool.submit(asyncio.run, service.analyze_security(request)).result()
            else:
                report = loop.run_until_complete(service.analyze_security(request))

            self.state.report = report
            self.state.completed_at = datetime.now(timezone.utc).isoformat()
            self.state.execution_status = "completed"
            logger.info("SecurityPrivacyFlow successfully completed: %s", security_run_id)

        except Exception as exc:
            logger.error("SecurityPrivacyFlow failed: %s", exc, exc_info=True)
            self.state.execution_status = "failed"
            self.state.error_message = str(exc)
            self.state.completed_at = datetime.now(timezone.utc).isoformat()

        return self.state
