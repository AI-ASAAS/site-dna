"""Unit tests for RecommendationEngine (priorities, effort, impact)."""

from site_dna.analysis.visual_identity.recommendations import RecommendationEngine
from site_dna.schemas.visual_identity import VisualFinding


def test_recommendations_generation_from_findings():
    """Verify that validated findings produce prioritized recommendations."""
    findings = [
        VisualFinding(
            finding_id="FIND-01",
            title="ضعف تباين لوني حرج",
            category="contrast",
            severity="high",
            confidence="confirmed_by_measurement",
            finding_type="derived_calculation",
            page_url="https://site.com/",
            description="نسبة التباين 2.1:1 أقل من المعيار.",
            potential_impact="صعوبة في قراءة النصوص للمستخدمين.",
            suggested_action="زيادة التباين ليكون أعلى من 4.5:1.",
            is_validated=True,
        ),
        VisualFinding(
            finding_id="FIND-02",
            title="تعدد عائلات الخطوط",
            category="typography",
            severity="medium",
            confidence="confirmed_by_measurement",
            finding_type="derived_calculation",
            page_url="https://site.com/",
            description="تم رصد 4 خطوط مختلفة.",
            potential_impact="تشتيت التماسك الطباعي.",
            suggested_action="حصر الخطوط في عائلة واحدة.",
            is_validated=True,
        ),
    ]

    recs = RecommendationEngine.generate_recommendations(findings, max_recommendations=5)
    assert len(recs) == 2

    # Contrast finding should produce P1 priority recommendation
    p1_rec = next(r for r in recs if r.priority == "P1")
    assert p1_rec.related_finding_ids == ["FIND-01"]
    assert p1_rec.estimated_effort == "small"
    assert p1_rec.expected_impact == "high"

    # Typography finding should produce P2 priority recommendation
    p2_rec = next(r for r in recs if r.priority == "P2")
    assert p2_rec.related_finding_ids == ["FIND-02"]
    assert p2_rec.estimated_effort == "small"
    assert p2_rec.expected_impact == "medium"


def test_recommendations_ignore_unvalidated():
    """Verify that unvalidated findings do not generate recommendations."""
    findings = [
        VisualFinding(
            finding_id="FIND-03",
            title="Unvalidated finding",
            category="branding",
            severity="critical",
            confidence="hypothesized",
            finding_type="derived_calculation",
            page_url="https://site.com/",
            description="Hallucinated issue.",
            potential_impact="None",
            suggested_action="None",
            is_validated=False,
        )
    ]

    recs = RecommendationEngine.generate_recommendations(findings)
    assert len(recs) == 0
