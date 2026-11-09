"""Unit tests for StructuredDataAnalyzer."""

from pathlib import Path

from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder
from site_dna.analysis.technical_seo.structured_data import StructuredDataAnalyzer

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_structured_data_valid():
    """Verify parsing and validation of valid Organization JSON-LD in Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_healthy" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-a")

    assessment, findings = StructuredDataAnalyzer.analyze(pages)

    assert assessment.total_schemas_found >= 1
    assert "Organization" in assessment.schema_types
    assert assessment.syntax_error_count == 0


def test_structured_data_incomplete_props():
    """Verify missing required properties detection in Fixture F."""
    base_dir = FIXTURES_DIR / "fixture_f_structured_data" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-f")

    assessment, findings = StructuredDataAnalyzer.analyze(pages)

    assert assessment.total_schemas_found >= 1
    assert len(assessment.missing_required_fields) >= 1
    # Article without headline/author triggers incomplete schema finding
    assert any("ناقص" in f.title or "خصائص" in f.title or "Article" in f.title or "حقول" in f.title for f in findings)
