"""Competitive Recommendation Prioritization Engine for Site DNA Phase 08."""

import uuid

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import (
    CompetitiveOpportunity,
    CompetitiveRecommendation,
    CompetitorSourceRecord,
)

logger = get_logger("analysis.competitor_intelligence.recommendations")


class CompetitorRecommendationEngine:
    """Prioritizes strategic remediations and differentiation initiatives based on benchmark outcomes."""

    def generate_recommendations(
        self,
        primary_site: CompetitorSourceRecord,
        opportunities: list[CompetitiveOpportunity],
    ) -> list[CompetitiveRecommendation]:
        """Generate P1/P2/P3 prioritized competitive recommendations."""
        recommendations: list[CompetitiveRecommendation] = []

        for opp in opportunities:
            rec_id = f"rec-cmp-{uuid.uuid4().hex[:8]}"

            priority = (
                "p1"
                if opp.estimated_impact == "high" and opp.estimated_effort == "small"
                else ("p2" if opp.estimated_impact == "high" else "p3")
            )

            recommendations.append(
                CompetitiveRecommendation(
                    recommendation_id=rec_id,
                    priority=priority,
                    title=opp.title,
                    title_ar=opp.title_ar,
                    description=f"Actionable response to competitive observation: {opp.strategic_interpretation}",
                    description_ar=f"إجراء استراتيجي مبني على الرصد الميداني للمنافسين: {opp.strategic_interpretation}",
                    category=opp.opportunity_type,
                    affected_competitor_ids=opp.affected_competitors,
                    expected_benefit="Closes observable feature communication gaps and enhances customer acquisition conversion.",
                    suggested_action=opp.suggested_action,
                    effort=opp.estimated_effort,
                    impact=opp.estimated_impact,
                    supporting_finding_ids=[],
                    evidence_ids=opp.supporting_evidence_ids,
                    limitations=[
                        "Based on public website observations within crawl scope.",
                        opp.validation_required,
                    ],
                )
            )

        if not recommendations:
            recommendations.append(
                CompetitiveRecommendation(
                    recommendation_id=f"rec-cmp-{uuid.uuid4().hex[:8]}",
                    priority="p2",
                    title="Monitor Emerging Competitor Messaging Cycles",
                    title_ar="المراقبة المستمرة لتحديثات الخطاب التسويقي للمنافسين",
                    description="Establish quarterly competitive website audits to detect new feature announcements.",
                    description_ar="جدولة عمليات فحص دورية ربع سنوية لرصد المزايا والخدمات الجديدة فور نشرها في مواقع المنافسين.",
                    category="Continuous Intelligence",
                    affected_competitor_ids=[],
                    expected_benefit="Early detection of competitor repositioning and product roadmap shifts.",
                    suggested_action="Schedule recurring Site DNA audits for key competitors.",
                    effort="small",
                    impact="medium",
                    supporting_finding_ids=[],
                    evidence_ids=[],
                    limitations=["Continuous monitoring requires automated scheduled runs."],
                )
            )

        return recommendations
