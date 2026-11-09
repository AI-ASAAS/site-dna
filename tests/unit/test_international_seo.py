"""Unit tests for InternationalSEOAnalyzer."""

from pathlib import Path

from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder
from site_dna.analysis.technical_seo.international_seo import InternationalSEOAnalyzer

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_international_seo_evaluation():
    """Verify html lang and international SEO evaluation in Fixture G."""
    base_dir = FIXTURES_DIR / "fixture_g_international_seo" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-g")

    assessment, findings = InternationalSEOAnalyzer.analyze(pages)

    assert assessment.html_lang_declared is not None
    assert assessment.bilingual_parity in ("single_language", "multilingual")
