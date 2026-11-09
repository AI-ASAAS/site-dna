"""Unit tests for MessagingAnalyzer."""

from pathlib import Path

from site_dna.analysis.content_marketing.context_builder import ContentContextBuilder
from site_dna.analysis.content_marketing.messaging_analyzer import MessagingAnalyzer

FIXTURES_DIR = Path("tests/fixtures/content_marketing")


def test_messaging_fixture_b_generic_headline():
    """Verify that Fixture B triggers generic headline warning."""
    base_dir = FIXTURES_DIR / "fixture_b_weak_value_prop" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-b")

    assessment, findings = MessagingAnalyzer.analyze(pages)

    assert assessment.headline_clarity == "ambiguous"
    assert any("مبهم" in f.title or "عام" in f.title for f in findings)


def test_messaging_fixture_d_absolute_claims():
    """Verify that Fixture D captures absolute and exaggerated claims."""
    base_dir = FIXTURES_DIR / "fixture_d_unsupported_claims" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-d")

    assessment, findings = MessagingAnalyzer.analyze(pages)

    assert assessment.absolute_claims_count > 0
    assert any("وعود قطعية" in f.title for f in findings)
