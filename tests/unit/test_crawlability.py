"""Unit tests for CrawlabilityAnalyzer."""

from pathlib import Path

from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder
from site_dna.analysis.technical_seo.crawlability import CrawlabilityAnalyzer

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_crawlability_healthy():
    """Verify healthy crawlability signals for Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_healthy" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, crawl_result, _, _ = builder.build_context(crawl_run_id="crawl-a")

    assessment, findings = CrawlabilityAnalyzer.analyze(pages, crawl_result)

    assert assessment.status == "permitted"
    assert assessment.crawl_depth_max <= 2
    assert assessment.broken_links_count == 0


def test_crawlability_restricted_and_deep():
    """Verify detection of restricted crawler permissions in Fixture B."""
    base_dir = FIXTURES_DIR / "fixture_b_crawl_restrictions" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, crawl_result, _, _ = builder.build_context(crawl_run_id="crawl-b")

    assessment, findings = CrawlabilityAnalyzer.analyze(pages, crawl_result)

    assert assessment.status == "restricted"
    assert assessment.crawl_depth_max >= 4
    assert len(findings) >= 1
