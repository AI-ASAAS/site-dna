"""Unit tests for MobileSEOAnalyzer."""

from pathlib import Path

from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder
from site_dna.analysis.technical_seo.mobile_seo import MobileSEOAnalyzer

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_mobile_seo_healthy():
    """Verify healthy mobile viewport in Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_healthy" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, visual_result, _ = builder.build_context(crawl_run_id="crawl-a", visual_run_id="vis-a")

    assessment, findings = MobileSEOAnalyzer.analyze(pages, visual_result)

    assert assessment.viewport_configured is True
    assert assessment.horizontal_overflow_detected is False
    assert len(findings) == 0
