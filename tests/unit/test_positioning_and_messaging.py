"""Unit tests for PositioningAnalyzer and MessagingComparator (Phase 08)."""

from site_dna.analysis.competitor_intelligence.messaging_comparison import MessagingComparator
from site_dna.analysis.competitor_intelligence.positioning_analyzer import PositioningAnalyzer
from tests.fixtures.competitor_intelligence.test_fixtures import (
    COMPETITOR_1_CRAWL_DATA,
    PRIMARY_CRAWL_DATA,
    make_sample_context,
)


def test_positioning_analyzer():
    ctx = make_sample_context()
    analyzer = PositioningAnalyzer()

    # Analyze primary site
    assessment = analyzer.analyze_positioning(ctx.primary_site, PRIMARY_CRAWL_DATA)

    assert assessment.site_id == ctx.primary_site.site_id
    assert assessment.core_value_proposition != ""
    assert isinstance(assessment.claimed_differentiators, list)
    assert assessment.brand_tone != ""


def test_messaging_comparator():
    ctx = make_sample_context()
    comparator = MessagingComparator()

    crawl_dataset = {
        ctx.primary_site.site_id: PRIMARY_CRAWL_DATA,
        ctx.competitor_sites[0].site_id: COMPETITOR_1_CRAWL_DATA,
    }

    benchmarks = comparator.compare_messaging(
        primary_site=ctx.primary_site,
        competitor_sites=ctx.competitor_sites,
        crawl_dataset=crawl_dataset,
    )

    assert len(benchmarks) > 0
    for b in benchmarks:
        assert b.dimension != ""
        assert b.dimension_ar != ""
        assert b.primary_observation != ""
        assert isinstance(b.competitor_observations, dict)
