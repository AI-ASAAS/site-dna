"""Unit tests for TechnicalSEOContextBuilder."""

from pathlib import Path

import pytest

from site_dna.analysis.technical_seo.context_builder import (
    TechnicalSEOContextBuilder,
    TechnicalSEOContextValidationError,
)

FIXTURES_DIR = Path("tests/fixtures/technical_seo")


def test_technical_seo_context_builder_fixture_a():
    """Verify that TechnicalSEOContextBuilder correctly ingests Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_healthy" / "runs"
    builder = TechnicalSEOContextBuilder(base_dir=str(base_dir))

    pages, crawl_result, visual_result, ev_index = builder.build_context(crawl_run_id="crawl-a", visual_run_id="vis-a")

    assert len(pages) == 2
    assert crawl_result.website_info.initial_url == "https://healthy-seo.example.com"
    assert pages[0].requested_url == "https://healthy-seo.example.com/"
    assert pages[0].title == "منصة أساس — حلول الذكاء الاصطناعي السحابية"
    assert pages[0].canonical_url == "https://healthy-seo.example.com/"
    assert "index" in pages[0].robots_directives
    assert len(pages[0].structured_data) == 1
    assert pages[0].structured_data[0]["@type"] == "Organization"
    assert visual_result is not None
    assert len(visual_result.pages) == 1


def test_technical_seo_context_builder_path_traversal():
    """Verify that path traversal attempts raise TechnicalSEOContextValidationError."""
    builder = TechnicalSEOContextBuilder(base_dir=str(FIXTURES_DIR / "fixture_a_healthy" / "runs"))

    with pytest.raises(TechnicalSEOContextValidationError, match="path traversal"):
        builder.build_context(crawl_run_id="../../etc/passwd")

    with pytest.raises(TechnicalSEOContextValidationError, match="Invalid visual_run_id"):
        builder.build_context(crawl_run_id="crawl-a", visual_run_id="../../evil")


def test_technical_seo_context_builder_missing_run():
    """Verify that non-existent crawl run raises TechnicalSEOContextValidationError."""
    builder = TechnicalSEOContextBuilder(base_dir=str(FIXTURES_DIR / "fixture_a_healthy" / "runs"))

    with pytest.raises(TechnicalSEOContextValidationError, match="Missing crawl.json"):
        builder.build_context(crawl_run_id="crawl-nonexistent")
