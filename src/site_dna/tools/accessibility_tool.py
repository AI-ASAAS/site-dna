"""CrewAI Tool for Site DNA Phase 10 — Web Accessibility & Inclusive Experience Intelligence."""

import asyncio
from typing import Any, Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from site_dna.analysis.accessibility.service import AccessibilityService
from site_dna.schemas.accessibility import AccessibilityAnalysisRequest


class AccessibilityToolSchema(BaseModel):
    """Input schema for AccessibilityTool."""

    crawl_run_id: str = Field(..., description="ID of completed discovery crawl run")
    visual_run_id: str | None = Field(None, description="Optional ID of visual capture run")
    ux_run_id: str | None = Field(None, description="Optional ID of UX/UI analysis run")
    language: str = Field(default="ar", description="Output language ('ar' or 'en')")
    max_pages: int = Field(default=8, description="Maximum pages to assess")
    deterministic_only: bool = Field(default=False, description="Run deterministic checks only")


class AccessibilityTool(BaseTool):
    """Tool executing Phase 10 passive accessibility and WCAG 2.2 analysis."""

    name: str = "accessibility_intelligence_tool"
    description: str = (
        "Performs passive, evidence-grounded web accessibility, WCAG 2.2 A/AA criteria mapping, "
        "keyboard navigation, color contrast, and inclusive UX analysis on crawl artifacts."
    )
    args_schema: Type[BaseModel] = AccessibilityToolSchema

    def _run(self, **kwargs: Any) -> str:
        """Synchronously execute the accessibility analysis service."""
        service = AccessibilityService()
        req = AccessibilityAnalysisRequest(
            crawl_run_id=kwargs.get("crawl_run_id", ""),
            visual_run_id=kwargs.get("visual_run_id"),
            ux_run_id=kwargs.get("ux_run_id"),
            language=kwargs.get("language", "ar"),
            max_pages=kwargs.get("max_pages", 8),
            deterministic_only=kwargs.get("deterministic_only", False),
            save_results=True,
        )

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                report = pool.submit(asyncio.run, service.analyze_accessibility(req)).result()
        else:
            report = loop.run_until_complete(service.analyze_accessibility(req))

        return report.model_dump_json(indent=2)
