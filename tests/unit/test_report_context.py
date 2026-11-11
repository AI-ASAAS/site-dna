"""Unit tests for ReportContextBuilder on real crawl run."""

from pathlib import Path

import pytest

from site_dna.reporting.report_context import ReportContextBuilder
from site_dna.schemas.final_report import FinalReportRequest


def test_build_context_from_crawl_a():
    """Verify building complete canonical report context from crawl-a run artifacts."""
    run_dir = Path("runs/crawl-a")
    if not run_dir.exists():
        pytest.skip("runs/crawl-a not present in test environment.")

    req = FinalReportRequest(crawl_run_id="crawl-a", mode="comprehensive", language="ar")
    builder = ReportContextBuilder(run_dir=run_dir)
    ctx = builder.build_context(req)

    assert ctx.crawl_run_id == "crawl-a"
    assert ctx.target_url == "https://clear-saas.example.com"
    assert ctx.mode == "comprehensive"
    assert ctx.language == "ar"

    # Multi-agent coverage
    assert "available_stages" in ctx.coverage
    assert len(ctx.coverage["available_stages"]) >= 5

    # Scores
    assert isinstance(ctx.scores, dict)
    assert len(ctx.scores) > 0

    # Unified findings & recommendations
    assert len(ctx.findings) > 0
    assert len(ctx.recommendations) > 0
    assert len(ctx.roadmap_waves) > 0

    # Source manifest checksums
    assert len(ctx.source_manifest) > 0
    for prov in ctx.source_manifest:
        assert len(prov.sha256_hash) == 64
