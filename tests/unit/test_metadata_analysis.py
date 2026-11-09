"""Unit tests for MetadataAnalyzer."""

from pathlib import Path

from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder
from site_dna.analysis.technical_seo.metadata_analyzer import MetadataAnalyzer

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_metadata_healthy():
    """Verify clean metadata in Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_healthy" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-a")

    assessment, findings = MetadataAnalyzer.analyze(pages)

    assert assessment.missing_title_count == 0
    assert assessment.missing_viewport_count == 0
    assert assessment.duplicate_titles_count == 0


def test_metadata_duplicates_and_excessive_length():
    """Verify detection of duplicate titles and excessive length in Fixture K."""
    base_dir = FIXTURES_DIR / "fixture_k_multipage_audit" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-k")

    assessment, findings = MetadataAnalyzer.analyze(pages)

    assert assessment.duplicate_titles_count >= 1
    assert any(f.finding_id == "TS-MET-TITLE-LONG" or "طول" in f.title or "70" in f.description for f in findings)
