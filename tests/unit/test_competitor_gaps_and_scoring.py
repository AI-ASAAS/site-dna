"""Unit tests for Gap Analysis, Opportunity Engine, and 6-Dimension Scoring (Phase 08)."""

from site_dna.analysis.competitor_intelligence.feature_comparison import FeatureMatrixBuilder
from site_dna.analysis.competitor_intelligence.gap_analyzer import CompetitiveGapAnalyzer
from site_dna.analysis.competitor_intelligence.opportunities import OpportunityEngine
from site_dna.analysis.competitor_intelligence.scoring import CompetitorScoringEngine
from site_dna.schemas.competitor_intelligence import CompetitorRelevance
from tests.fixtures.competitor_intelligence.test_fixtures import (
    COMPETITOR_1_CRAWL_DATA,
    PRIMARY_CRAWL_DATA,
    make_sample_context,
)


def test_gap_analysis_and_opportunities():
    ctx = make_sample_context()
    f_builder = FeatureMatrixBuilder()
    crawl_dataset = {
        ctx.primary_site.site_id: PRIMARY_CRAWL_DATA,
        ctx.competitor_sites[0].site_id: COMPETITOR_1_CRAWL_DATA,
    }
    matrix = f_builder.build_matrix(
        primary_site=ctx.primary_site,
        competitor_sites=ctx.competitor_sites,
        crawl_dataset=crawl_dataset,
    )

    gap_analyzer = CompetitiveGapAnalyzer()
    gaps = gap_analyzer.identify_gaps(
        primary_site=ctx.primary_site,
        competitor_sites=ctx.competitor_sites,
        feature_matrix=matrix,
        pricing_records=[],
        trust_assessments=[],
    )

    assert isinstance(gaps, list)
    for g in gaps:
        assert g.title is not None
        assert g.observed_difference != ""
        assert g.validation_required != ""

    opp_engine = OpportunityEngine()
    opportunities = opp_engine.derive_opportunities(
        primary_site=ctx.primary_site,
        gaps=gaps,
        positioning_assessments=[],
    )

    assert isinstance(opportunities, list)
    for opp in opportunities:
        assert opp.title is not None
        assert opp.estimated_impact in ("high", "medium", "low")
        assert opp.estimated_effort in ("small", "medium", "large")


def test_scoring_engine_6_dimensions():
    ctx = make_sample_context()
    f_builder = FeatureMatrixBuilder()

    crawl_dataset = {
        ctx.primary_site.site_id: PRIMARY_CRAWL_DATA,
        ctx.competitor_sites[0].site_id: COMPETITOR_1_CRAWL_DATA,
    }

    matrix = f_builder.build_matrix(
        primary_site=ctx.primary_site,
        competitor_sites=ctx.competitor_sites,
        crawl_dataset=crawl_dataset,
    )

    scoring = CompetitorScoringEngine()
    relevance_records = [
        CompetitorRelevance(
            site_id=ctx.competitor_sites[0].site_id,
            url=ctx.competitor_sites[0].url,
            relevance_category="direct",
            relevance_score=90.0,
            reason="Direct competitor in SaaS CRM space",
            reason_ar="منافس مباشر في إدارة علاقات العملاء",
        )
    ]
    scores = scoring.compute_scores(
        primary_site=ctx.primary_site,
        competitor_sites=ctx.competitor_sites,
        relevance_assessments=relevance_records,
        feature_matrix=matrix,
        gaps=[],
        existing_scores={},
    )

    assert scores.overall_score is not None
    assert 0.0 <= scores.overall_score <= 100.0
    assert len(scores.dimension_scores) == 6
    for dim, val in scores.dimension_scores.items():
        if val is not None:
            assert 0.0 <= val <= 100.0
