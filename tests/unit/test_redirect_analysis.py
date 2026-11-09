"""Unit tests for RedirectAnalyzer."""

from pathlib import Path

from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder
from site_dna.analysis.technical_seo.redirect_analyzer import RedirectAnalyzer

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_redirect_healthy():
    """Verify clean pages without redirects in Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_healthy" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-a")

    assessment, findings = RedirectAnalyzer.analyze(pages)

    assert assessment.redirect_count == 0
    assert len(findings) == 0


def test_redirect_temporary_302():
    """Verify detection of temporary redirects in Fixture D."""
    base_dir = FIXTURES_DIR / "fixture_d_broken_redirects" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-d")

    assessment, findings = RedirectAnalyzer.analyze(pages)

    assert assessment.temporary_redirects_302 >= 1
    assert len(findings) >= 1
