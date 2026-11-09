"""Unit tests for ContentGapAnalyzer."""

from pathlib import Path

from site_dna.analysis.content_marketing.content_gaps import ContentGapAnalyzer
from site_dna.analysis.content_marketing.context_builder import ContentContextBuilder

FIXTURES_DIR = Path("tests/fixtures/content_marketing")


def test_content_gaps_fixture_b_unclear():
    """Verify that Fixture B triggers unclear_offering gap."""
    base_dir = FIXTURES_DIR / "fixture_b_weak_value_prop" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-b")

    gaps = ContentGapAnalyzer.analyze(pages)

    assert any(g.gap_type == "unclear_offering" for g in gaps)
