"""Report assembly and atomic JSON writing (Phase 8)."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

from site_dna import __version__
from site_dna.core.context import ScanContext
from site_dna.models.common import ModuleError, ModuleResult, ModuleStatus
from site_dna.models.performance import Performance
from site_dna.models.report import (
    ExecutionSummary,
    ProjectInfo,
    Report,
    WebsiteContent,
)
from site_dna.models.seo import SeoAnalysis
from site_dna.models.visual import VisualIdentity
from site_dna.services.normalizer import registrable_domain

MODULE_NAMES = ("website_content", "visual_identity", "performance", "seo_analysis")


def _as_website_content(result: ModuleResult[Any] | None) -> WebsiteContent:
    if result is None or result.data is None:
        return WebsiteContent()
    if isinstance(result.data, WebsiteContent):
        return result.data
    return WebsiteContent.model_validate(result.data)


def _as_visual(result: ModuleResult[Any] | None) -> ModuleResult[VisualIdentity]:
    if result is None:
        return ModuleResult[VisualIdentity](status=ModuleStatus.skipped, duration_ms=0)
    return ModuleResult[VisualIdentity](
        status=result.status,
        reason=result.reason,
        duration_ms=result.duration_ms,
        data=result.data,
        warnings=result.warnings,
        errors=result.errors,
    )


def _as_performance(result: ModuleResult[Any] | None) -> ModuleResult[Performance]:
    if result is None:
        return ModuleResult[Performance](status=ModuleStatus.skipped, duration_ms=0)
    return ModuleResult[Performance](
        status=result.status,
        reason=result.reason,
        duration_ms=result.duration_ms,
        data=result.data,
        warnings=result.warnings,
        errors=result.errors,
    )


def _as_seo(result: ModuleResult[Any] | None) -> ModuleResult[SeoAnalysis]:
    if result is None:
        return ModuleResult[SeoAnalysis](status=ModuleStatus.skipped, duration_ms=0)
    return ModuleResult[SeoAnalysis](
        status=result.status,
        reason=result.reason,
        duration_ms=result.duration_ms,
        data=result.data,
        warnings=result.warnings,
        errors=result.errors,
    )


def _scan_status(results: Mapping[str, ModuleResult[Any]]) -> str:
    statuses = [result.status for result in results.values()]
    if statuses and all(status is ModuleStatus.failed for status in statuses):
        return "failed"
    if any(
        status in (ModuleStatus.failed, ModuleStatus.partial, ModuleStatus.skipped, ModuleStatus.not_available)
        for status in statuses
    ):
        return "partial"
    return "completed"


def _domain(url: str | None) -> str | None:
    if not url:
        return None
    host = urlsplit(url).hostname
    return registrable_domain(host) if host else None


def build_report(
    context: ScanContext,
    results: Mapping[str, ModuleResult[Any]],
    *,
    input_url: str | None = None,
) -> Report:
    """Assemble a complete report from module results and the run context."""
    target = input_url or context.config.input_url
    content_result = results.get("website_content")
    website_content = _as_website_content(content_result)

    final_url = next(
        (page.final_url or page.url for page in website_content.pages if page.final_url or page.url),
        None,
    )
    if final_url is None and website_content.pages:
        final_url = website_content.pages[0].url

    warnings: list[str] = []
    errors: list[ModuleError] = []
    module_results: dict[str, str] = {}
    timings: dict[str, float] = dict(context.timings)
    for name in MODULE_NAMES:
        result = results.get(name)
        if result is None:
            module_results[name] = ModuleStatus.skipped.value
            continue
        module_results[name] = result.status.value
        warnings.extend(result.warnings)
        errors.extend(result.errors)
        timings.setdefault(name, round(result.duration_ms / 1000, 3))

    processing = (datetime.now(timezone.utc) - context.started_at).total_seconds()
    return Report(
        scan_id=context.scan_id,
        project_info=ProjectInfo(
            input_url=target,
            final_url=final_url,
            domain=_domain(final_url or target),
            scan_timestamp=context.started_at,
            scan_status=_scan_status(results),
            processing_time_seconds=round(processing, 3),
            permission_attested=context.config.permission_attested,
            tool_version=__version__,
            config=context.config.model_dump(mode="json"),
        ),
        website_content=ModuleResult[WebsiteContent](
            status=content_result.status if content_result else ModuleStatus.skipped,
            reason=content_result.reason if content_result else "not_run",
            duration_ms=content_result.duration_ms if content_result else 0,
            data=website_content,
            warnings=content_result.warnings if content_result else [],
            errors=content_result.errors if content_result else [],
        ),
        visual_identity=_as_visual(results.get("visual_identity")),
        performance=_as_performance(results.get("performance")),
        seo_analysis=_as_seo(results.get("seo_analysis")),
        execution_summary=ExecutionSummary(
            module_results=module_results,
            warnings=warnings,
            errors=errors,
            timings=timings,
        ),
    )


def write_report(report: Report, output_dir: str | Path) -> Path:
    """Atomically write ``report.json`` as UTF-8 and return its path."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    report_path = directory / "report.json"
    temporary_path = directory / ".report.json.tmp"

    payload = report.model_dump(mode="json")
    with temporary_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary_path, report_path)
    return report_path
