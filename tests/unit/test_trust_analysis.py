"""Unit tests for TrustAnalyzer."""

from pathlib import Path

from site_dna.analysis.content_marketing.context_builder import ContentContextBuilder
from site_dna.analysis.content_marketing.trust_analyzer import TrustAnalyzer

FIXTURES_DIR = Path("tests/fixtures/content_marketing")


def test_trust_analysis_fixture_a():
    """Verify that Fixture A has contact information and about coverage."""
    base_dir = FIXTURES_DIR / "fixture_a_clear_messaging" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-a")

    claims, findings = TrustAnalyzer.analyze(pages)

    assert not any("غياب بيانات" in f.title for f in findings)


def test_trust_analysis_fixture_d_performance_claims():
    """Verify that Fixture D inventories statistical and numerical claims."""
    base_dir = FIXTURES_DIR / "fixture_d_unsupported_claims" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-d")

    claims, findings = TrustAnalyzer.analyze(pages)

    assert len(claims) >= 1
    assert any("ادعاء إحصائي" in f.title for f in findings)
    assert any(c.verification_status == "observed_only" for c in claims)
