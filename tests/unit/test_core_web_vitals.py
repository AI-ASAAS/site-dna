"""Unit tests for CoreWebVitalsAnalyzer."""

from pathlib import Path

from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder
from site_dna.analysis.technical_seo.core_web_vitals import CoreWebVitalsAnalyzer

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_core_web_vitals_lab_mode():
    """Verify lab mode Core Web Vitals and strict INP unmeasured boundary."""
    base_dir = FIXTURES_DIR / "fixture_a_healthy" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, visual_result, _ = builder.build_context(crawl_run_id="crawl-a", visual_run_id="vis-a")

    cwv_record, findings = CoreWebVitalsAnalyzer.analyze(pages, visual_result)

    assert cwv_record.field_vs_lab == "lab"
    # Strict boundary requirement: INP must never be guessed or fabricated in laboratory mode
    assert cwv_record.inp_ms is None
    assert cwv_record.inp_source == "not_measured"
    assert cwv_record.lcp_source == "lab_browser"
