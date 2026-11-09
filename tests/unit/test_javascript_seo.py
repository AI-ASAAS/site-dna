"""Unit tests for JavaScriptSEOAnalyzer."""

from pathlib import Path

from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder
from site_dna.analysis.technical_seo.javascript_seo import JavaScriptSEOAnalyzer

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_javascript_seo_static():
    """Verify that static healthy pages show clean consistent status in Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_healthy" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, visual_result, _ = builder.build_context(crawl_run_id="crawl-a", visual_run_id="vis-a")

    assessment, findings = JavaScriptSEOAnalyzer.analyze(pages, visual_result)

    assert assessment.status == "consistent"
    assert assessment.content_rendered_only is False


def test_javascript_seo_csr_and_js_links():
    """Verify CSR rendering difference and missing server content in Fixture E."""
    base_dir = FIXTURES_DIR / "fixture_e_javascript_seo" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, visual_result, _ = builder.build_context(crawl_run_id="crawl-e", visual_run_id="vis-e")

    assessment, findings = JavaScriptSEOAnalyzer.analyze(pages, visual_result)

    assert assessment.content_rendered_only is True
    assert len(findings) >= 1
