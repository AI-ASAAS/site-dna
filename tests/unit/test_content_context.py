"""Unit tests for ContentContextBuilder."""

from pathlib import Path

import pytest

from site_dna.analysis.content_marketing.context_builder import (
    ContentContextBuilder,
    ContentContextValidationError,
)

FIXTURES_DIR = Path("tests/fixtures/content_marketing")


def test_content_context_builder_fixture_a():
    """Verify that ContentContextBuilder correctly ingests Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_clear_messaging" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))

    pages, ev_index, target_origin, info = builder.build_context(crawl_run_id="crawl-a")

    assert len(pages) == 3
    assert target_origin == "https://clear-saas.example.com"
    assert info["total_crawled_pages"] == 3
    assert pages[0].page_url == "https://clear-saas.example.com/"
    assert pages[0].word_count > 40
    assert len(pages[0].headings) == 3
    assert len(pages[0].cta_candidates) > 0


def test_content_context_builder_path_traversal():
    """Verify that path traversal attempts raise ContentContextValidationError."""
    builder = ContentContextBuilder(base_dir="tests/fixtures/content_marketing")

    with pytest.raises(ContentContextValidationError, match="Path traversal"):
        builder.build_context(crawl_run_id="../../etc/passwd")


def test_content_context_builder_missing_run():
    """Verify that non-existent crawl run raises FileNotFoundError."""
    builder = ContentContextBuilder(base_dir=str(FIXTURES_DIR / "fixture_a_clear_messaging" / "runs"))

    with pytest.raises(FileNotFoundError):
        builder.build_context(crawl_run_id="crawl-nonexistent")
