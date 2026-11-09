"""CrewAI BaseTool wrapper for Site DNA Phase 09 — Security, Privacy & Trust Intelligence."""

import asyncio
from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from site_dna.analysis.security_privacy.service import SecurityPrivacyService
from site_dna.schemas.security_privacy import SecurityPrivacyAnalysisRequest


class SecurityPrivacyToolInput(BaseModel):
    """Input parameters for Security & Privacy analysis tool."""

    crawl_run_id: str = Field(..., description="Completed discovery crawl run ID")
    visual_run_id: Optional[str] = Field(default=None, description="Optional visual run ID")
    language: Optional[str] = Field(default="ar", description="Language of report ('ar' or 'en')")
    max_pages: Optional[int] = Field(default=8, description="Maximum pages to assess")
    save_results: Optional[bool] = Field(default=True, description="Whether to persist artifacts")
    offline_mode: Optional[bool] = Field(default=False, description="Run in offline mode")
    deterministic_only: Optional[bool] = Field(default=False, description="Skip AI layer")


class SecurityPrivacyTool(BaseTool):
    """CrewAI tool performing passive, evidence-based security, privacy, and digital trust audits."""

    name: str = "security_privacy_analysis_tool"
    description: str = (
        "Passively evaluates observable website security controls including HTTPS transport, "
        "HTTP security response headers, cookie attributes (with redacted values), CSP defense-in-depth, "
        "browser isolation controls, third-party resource inventory, and public privacy policy signals."
    )
    args_schema: type[BaseModel] = SecurityPrivacyToolInput

    def _run(
        self,
        crawl_run_id: str,
        visual_run_id: Optional[str] = None,
        language: Optional[str] = "ar",
        max_pages: Optional[int] = 8,
        save_results: Optional[bool] = True,
        offline_mode: Optional[bool] = False,
        deterministic_only: Optional[bool] = False,
    ) -> str:
        """Execute passive security analysis synchronously and return JSON summary."""
        request = SecurityPrivacyAnalysisRequest(
            crawl_run_id=crawl_run_id,
            visual_run_id=visual_run_id,
            language=language or "ar",
            max_pages=max_pages or 8,
            save_results=bool(save_results),
            offline_mode=bool(offline_mode),
            deterministic_only=bool(deterministic_only),
        )

        service = SecurityPrivacyService()
        report = asyncio.run(service.analyze_security(request))
        return report.model_dump_json()
