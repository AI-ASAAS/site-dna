"""Unit tests for RobotsAnalyzer."""

from pathlib import Path

from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder
from site_dna.analysis.technical_seo.robots_analyzer import RobotsAnalyzer

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_robots_healthy():
    """Verify healthy robots.txt in Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_healthy" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, crawl_result, _, _ = builder.build_context(crawl_run_id="crawl-a")

    assessment, findings = RobotsAnalyzer.analyze(pages, crawl_result)

    assert assessment.is_present is True
    assert assessment.crawler_allowed is True


def test_robots_disallowed():
    """Verify disallowed crawler in Fixture B."""
    base_dir = FIXTURES_DIR / "fixture_b_crawl_restrictions" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, crawl_result, _, _ = builder.build_context(crawl_run_id="crawl-b")

    assessment, findings = RobotsAnalyzer.analyze(pages, crawl_result)

    assert assessment.is_present is True
    assert assessment.crawler_allowed is False
    assert len(findings) >= 1
