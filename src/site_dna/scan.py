"""Scan entry points for the website intelligence MVP.

Phase 1 only produces a schema-valid placeholder report. Later phases replace
the placeholder modules with real analyzers.
"""

from datetime import datetime, timezone
from typing import Any

from site_dna.models.common import ModuleResult, ModuleStatus
from site_dna.models.performance import Performance
from site_dna.models.report import (
    ExecutionSummary,
    ProjectInfo,
    Report,
    WebsiteContent,
)
from site_dna.models.seo import SeoAnalysis
from site_dna.models.visual import VisualIdentity
from site_dna.services.report_generator import write_report

PLACEHOLDER_REASON = "phase_1_placeholder"

MODULE_NAMES = (
    "website_content",
    "visual_identity",
    "performance",
    "seo_analysis",
)


def _skipped() -> ModuleResult[Any]:
    return ModuleResult[Any](
        status=ModuleStatus.skipped,
        reason=PLACEHOLDER_REASON,
        duration_ms=0,
        data=None,
    )


def build_placeholder_report(
    scan_id: str,
    input_url: str,
    config: dict[str, Any] | None = None,
    tool_version: str = "0.1.0",
) -> Report:
    """Build the Phase 1 empty report with every module marked ``skipped``."""
    module_results = {name: ModuleStatus.skipped.value for name in MODULE_NAMES}
    return Report(
        scan_id=scan_id,
        project_info=ProjectInfo(
            input_url=input_url,
            final_url=None,
            domain=None,
            scan_timestamp=datetime.now(timezone.utc),
            scan_status="completed",
            processing_time_seconds=0.0,
            permission_attested=True,
            tool_version=tool_version,
            config=config or {},
        ),
        website_content=ModuleResult[WebsiteContent](
            status=ModuleStatus.skipped,
            reason=PLACEHOLDER_REASON,
            duration_ms=0,
            data=None,
        ),
        visual_identity=ModuleResult[VisualIdentity](
            status=ModuleStatus.skipped,
            reason=PLACEHOLDER_REASON,
            duration_ms=0,
            data=None,
        ),
        performance=ModuleResult[Performance](
            status=ModuleStatus.skipped,
            reason=PLACEHOLDER_REASON,
            duration_ms=0,
            data=None,
        ),
        seo_analysis=ModuleResult[SeoAnalysis](
            status=ModuleStatus.skipped,
            reason=PLACEHOLDER_REASON,
            duration_ms=0,
            data=None,
        ),
        execution_summary=ExecutionSummary(
            module_results=module_results,
            warnings=[],
            errors=[],
            timings={},
        ),
    )




__all__ = ["build_placeholder_report", "write_report"]
