"""Unit tests for CanonicalAnalyzer."""

from pathlib import Path

from site_dna.analysis.technical_seo.canonical_analyzer import CanonicalAnalyzer
from site_dna.analysis.technical_seo.context_builder import TechnicalSEOContextBuilder

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_canonical_healthy():
    """Verify self-referencing canonical evaluation in Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_healthy" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-a")

    assessment, findings = CanonicalAnalyzer.analyze(pages)

    assert assessment.missing_canonical_count == 0
    assert assessment.self_referencing_count == 2
    assert len(findings) == 0


def test_canonical_cross_page_or_missing():
    """Verify detection when canonical points to another page or is missing."""
    base_dir = FIXTURES_DIR / "fixture_c_indexing_conflicts" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-c")

    assessment, findings = CanonicalAnalyzer.analyze(pages)

    assert assessment.cross_page_canonical_count >= 1
    assert len(findings) >= 1
