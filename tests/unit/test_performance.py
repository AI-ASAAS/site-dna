"""Unit tests for PerformanceAnalyzer."""

from pathlib import Path

from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder
from site_dna.analysis.technical_seo.performance import PerformanceAnalyzer

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_performance_healthy():
    """Verify healthy fast performance metrics in Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_healthy" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, crawl_result, visual_result, _ = builder.build_context(crawl_run_id="crawl-a", visual_run_id="vis-a")

    measurements, findings = PerformanceAnalyzer.analyze(pages, crawl_result, visual_result)

    assert len(measurements) >= 2
    avg_fetch = next(m for m in measurements if m.metric_name == "average_fetch_duration")
    assert avg_fetch.value < 1000.0
    assert len(findings) == 0


def test_performance_heavy_payload():
    """Verify performance warnings for slow fetch and heavy document in Fixture H."""
    base_dir = FIXTURES_DIR / "fixture_h_performance_issues" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, crawl_result, visual_result, _ = builder.build_context(crawl_run_id="crawl-h", visual_run_id="vis-h")

    measurements, findings = PerformanceAnalyzer.analyze(pages, crawl_result, visual_result)

    assert len(findings) >= 2
    assert any("TS-PRF-SLOW-TTFB" == f.finding_id for f in findings)
    assert any("TS-PRF-LARGE-DOM" == f.finding_id for f in findings)
