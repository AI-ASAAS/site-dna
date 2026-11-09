"""Unit tests for CTAContentAnalyzer."""

from pathlib import Path

from site_dna.analysis.content_marketing.context_builder import ContentContextBuilder
from site_dna.analysis.content_marketing.cta_analyzer import CTAContentAnalyzer

FIXTURES_DIR = Path("tests/fixtures/content_marketing")


def test_cta_analysis_fixture_a_actionable():
    """Verify that Fixture A has an identified actionable primary CTA."""
    base_dir = FIXTURES_DIR / "fixture_a_clear_messaging" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-a")

    assessment, findings = CTAContentAnalyzer.analyze(pages)

    assert assessment.total_ctas_observed > 0
    assert assessment.primary_cta_identified is True
    assert assessment.generic_ctas_count == 0


def test_cta_analysis_fixture_b_generic():
    """Verify that Fixture B captures generic CTA label 'اضغط هنا'."""
    base_dir = FIXTURES_DIR / "fixture_b_weak_value_prop" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-b")

    assessment, findings = CTAContentAnalyzer.analyze(pages)

    assert assessment.generic_ctas_count >= 1
    assert any("صياغة CTA عامة" in f.title for f in findings)
