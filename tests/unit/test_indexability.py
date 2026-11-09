"""Unit tests for IndexabilityAnalyzer."""

from pathlib import Path

from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder
from site_dna.analysis.technical_seo.indexability import IndexabilityAnalyzer

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_indexability_healthy():
    """Verify healthy indexability assessment for Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_healthy" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-a")

    assessment, findings = IndexabilityAnalyzer.analyze(pages)

    assert assessment.status == "potentially_indexable"
    assert assessment.noindex_count == 0
    assert len(findings) == 0


def test_indexability_conflicts():
    """Verify detection of noindex directives in Fixture C."""
    base_dir = FIXTURES_DIR / "fixture_c_indexing_conflicts" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-c")

    assessment, findings = IndexabilityAnalyzer.analyze(pages)

    assert assessment.noindex_count >= 1
    assert len(findings) >= 1
