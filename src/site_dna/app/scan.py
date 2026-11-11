"""CLI-facing unified scan entry point (Phase 9)."""

import asyncio
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

from site_dna.app.pipeline import ScanPipeline
from site_dna.core.config import ScanConfig, get_settings
from site_dna.core.context import ScanContext
from site_dna.core.logging import get_logger, setup_scan_logging
from site_dna.schema.schema_export import export_schema
from site_dna.services.report_generator import write_report


def run_scan_cli(
    url: str,
    i_have_permission: bool,
    max_pages: Optional[int] = None,
    max_depth: Optional[int] = None,
    output_dir: Optional[str] = None,
    embed_images: bool = False,
    verbose: bool = False,
    *,
    pipeline_factory=None,
) -> int:
    """Run a complete scan after explicit permission attestation."""
    if not url:
        print("error: a target URL is required", file=sys.stderr)
        return 2
    if not i_have_permission:
        print(
            "error: --i-have-permission is required before scanning a website",
            file=sys.stderr,
        )
        return 2

    settings = get_settings()
    config = ScanConfig.from_settings(
        settings,
        input_url=url,
        max_pages=max_pages,
        max_depth=max_depth,
        output_dir=output_dir,
        embed_images=embed_images,
        verbose=verbose,
        permission_attested=True,
    )
    scan_id = uuid4().hex
    storage_root = Path(output_dir) if output_dir else Path(settings.storage_dir)
    setup_scan_logging(
        scan_id,
        storage_root,
        level="DEBUG" if verbose else settings.log_level,
    )

    logger = get_logger("site_dna.scan")
    context = ScanContext(
        config=config,
        settings=settings,
        scan_id=scan_id,
        output_dir=storage_root / scan_id,
        logger=logger,
        started_at=datetime.now(timezone.utc),
    )

    pipeline = pipeline_factory(context) if pipeline_factory else ScanPipeline(context)
    report = asyncio.run(pipeline.run(url))
    report_path = write_report(report, context.output_dir)
    logger.info("scan report written to %s", report_path)

    print("=" * 60)
    print(" Site DNA - Website Intelligence Scan")
    print("=" * 60)
    print(f" Scan status : {report.project_info.scan_status}")
    print(f" Scan ID     : {scan_id}")
    print(f" Target URL  : {url}")
    if report.project_info.final_url:
        print(f" Final URL   : {report.project_info.final_url}")
    content = report.website_content.data
    print(f" Pages       : {content.total_pages if content else 0}")
    print(" Modules:")
    for name, status in report.execution_summary.module_results.items():
        print(f"  - {name:<16}: {status}")
    seo = report.seo_analysis.data
    if seo is not None:
        print(
            " SEO checks  : "
            f"{seo.summary.passed} passed, {seo.summary.warning} warning, "
            f"{seo.summary.failed} failed, {seo.summary.not_available} not available"
        )
    performance = report.performance.data
    if performance is not None:
        print(f" PSI mobile  : {performance.mobile.score if performance.mobile.score is not None else 'n/a'}")
        print(f" PSI desktop : {performance.desktop.score if performance.desktop.score is not None else 'n/a'}")
    print(f" Report      : {report_path}")
    print("=" * 60)

    if report.project_info.scan_status == "rejected":
        return 2
    return 1 if report.project_info.scan_status == "failed" else 0


def run_schema_cli(output: Optional[str] = None) -> int:
    """Export the report JSON Schema and print its path."""
    path = export_schema(output)
    if output is None:
        root_path = Path("schemas") / "report.schema.json"
        root_path.parent.mkdir(parents=True, exist_ok=True)
        root_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Schema written to {path}")
    return 0
