"""Unit tests for SitemapAnalyzer."""

from pathlib import Path

from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder
from site_dna.analysis.technical_seo.sitemap_analyzer import SitemapAnalyzer

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_sitemap_healthy():
    """Verify sitemap discovery and URL mapping in Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_healthy" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, crawl_result, _, _ = builder.build_context(crawl_run_id="crawl-a")

    assessment, findings = SitemapAnalyzer.analyze(pages, crawl_result)

    assert assessment.sitemap_found is True
    assert len(assessment.sitemap_urls) == 2
    assert assessment.duplicate_urls_count == 0


def test_sitemap_missing():
    """Verify handling when sitemap is missing in Fixture J."""
    base_dir = FIXTURES_DIR / "fixture_j_missing_evidence" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, crawl_result, _, _ = builder.build_context(crawl_run_id="crawl-j")

    assessment, findings = SitemapAnalyzer.analyze(pages, crawl_result)

    assert assessment.sitemap_found is False
    assert len(findings) >= 1
