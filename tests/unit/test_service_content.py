"""Unit tests for ServiceContentAnalyzer."""

from pathlib import Path

from site_dna.analysis.content_marketing.context_builder import ContentContextBuilder
from site_dna.analysis.content_marketing.service_content import ServiceContentAnalyzer

FIXTURES_DIR = Path("tests/fixtures/content_marketing")


def test_service_content_fixture_a():
    """Verify that Fixture A has adequate service descriptions and clear next steps."""
    base_dir = FIXTURES_DIR / "fixture_a_clear_messaging" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-a")

    assessment, findings = ServiceContentAnalyzer.analyze(pages)

    assert assessment.total_services_identified >= 2
    assert assessment.descriptions_completeness == "adequate"
    assert assessment.next_step_clarity is True


def test_service_content_fixture_b_missing():
    """Verify that Fixture B without services is handled gracefully."""
    base_dir = FIXTURES_DIR / "fixture_b_weak_value_prop" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-b")

    assessment, findings = ServiceContentAnalyzer.analyze(pages)

    assert assessment.descriptions_completeness == "missing"
    assert assessment.total_services_identified == 0
