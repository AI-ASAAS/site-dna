"""Unit tests for ValuePropositionAnalyzer."""

from pathlib import Path

from site_dna.analysis.content_marketing.context_builder import ContentContextBuilder
from site_dna.analysis.content_marketing.value_proposition import ValuePropositionAnalyzer

FIXTURES_DIR = Path("tests/fixtures/content_marketing")


def test_value_proposition_fixture_a_clear():
    """Verify that Fixture A has clear value proposition and offering summary."""
    base_dir = FIXTURES_DIR / "fixture_a_clear_messaging" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-a")

    assessment, findings = ValuePropositionAnalyzer.analyze(pages)

    assert assessment.clarity_rating == "clear"
    assert assessment.offering_summary is not None
    assert "منصة" in assessment.offering_summary
    assert len(assessment.core_benefits) >= 1


def test_value_proposition_fixture_b_weak():
    """Verify that Fixture B triggers unclear value proposition finding."""
    base_dir = FIXTURES_DIR / "fixture_b_weak_value_prop" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-b")

    assessment, findings = ValuePropositionAnalyzer.analyze(pages)

    assert assessment.clarity_rating in ("unclear", "moderate")
    assert any("القيمة المقترحة" in f.title or "Value Proposition" in f.title for f in findings)
