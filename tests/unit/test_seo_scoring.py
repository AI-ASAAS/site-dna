"""Unit tests for TechnicalSEOScoringEngine."""

from site_dna.analysis.technical_seo.scoring import TechnicalSEOScoringEngine
from site_dna.schemas.technical_seo import (
    TechnicalPageRecord,
    TechnicalSEOFinding,
)


def test_scoring_weights_sum_to_one():
    """Verify that rubric dimension weights sum to exactly 1.0 (100%)."""
    total_weight = sum(w for _, _, w in TechnicalSEOScoringEngine.DIMENSIONS)
    assert round(total_weight, 4) == 1.0


def test_scoring_healthy_site():
    """Verify high scores for healthy pages without negative findings."""
    pages = [
        TechnicalPageRecord(
            page_id="p1",
            requested_url="https://example.com/",
            final_url="https://example.com/",
            canonical_url="https://example.com/",
            http_status=200,
            title="Healthy SEO Page",
            viewport_meta="width=device-width, initial-scale=1.0",
        )
    ]

    overall, scores = TechnicalSEOScoringEngine.calculate_scores(
        pages=pages,
        findings=[],
        performance_measured=True,
    )

    assert overall is not None
    assert overall >= 90.0
    crawl_score = next(s for s in scores if s.dimension_name == "crawlability")
    assert crawl_score.score == 100.0


def test_scoring_penalties():
    """Verify deduction for critical findings."""
    pages = [
        TechnicalPageRecord(
            page_id="p1",
            requested_url="https://example.com/",
            final_url="https://example.com/",
            http_status=500,
        )
    ]
    findings = [
        TechnicalSEOFinding(
            finding_id="TS-CRW-500",
            title="تعذر الوصول للخادم 500",
            category="crawlability",
            description="خادم الموقع يعيد رمز خطأ داخلي.",
            severity="critical",
            page_url="https://example.com/",
            observation_type="observed",
            confidence_category="measured",
            potential_technical_impact="يمنع محركات البحث من الزحف.",
            recommended_action="إصلاح الخادم.",
        )
    ]

    overall, scores = TechnicalSEOScoringEngine.calculate_scores(
        pages=pages,
        findings=findings,
        performance_measured=True,
    )

    crawl_score = next(s for s in scores if s.dimension_name == "crawlability")
    assert crawl_score.score <= 75.0
