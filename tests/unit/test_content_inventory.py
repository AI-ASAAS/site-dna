"""Unit tests for ContentInventoryBuilder and PageClassifier."""

from pathlib import Path

from site_dna.analysis.content_marketing.content_inventory import ContentInventoryBuilder
from site_dna.analysis.content_marketing.context_builder import ContentContextBuilder

FIXTURES_DIR = Path("tests/fixtures/content_marketing")


def test_content_inventory_fixture_a():
    """Verify aggregated inventory metrics for Fixture A."""
    base_dir = FIXTURES_DIR / "fixture_a_clear_messaging" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-a")

    inventory = ContentInventoryBuilder.build_inventory(pages)

    assert inventory.total_pages == 3
    assert inventory.total_word_count > 100
    assert inventory.average_word_count_per_page > 30.0
    assert "home" in inventory.page_types_distribution
    assert "services" in inventory.page_types_distribution
    assert "contact" in inventory.page_types_distribution
    assert inventory.headings_summary["h1"] >= 3
