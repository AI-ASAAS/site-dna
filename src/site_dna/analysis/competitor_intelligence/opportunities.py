"""Strategic Opportunity Generation Engine for Site DNA Phase 08."""

import uuid

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import (
    CompetitiveGap,
    CompetitiveOpportunity,
    CompetitorSourceRecord,
    PositioningAssessment,
)

logger = get_logger("analysis.competitor_intelligence.opportunities")


class OpportunityEngine:
    """Translates observed competitive gaps and positioning differences into actionable strategic opportunities."""

    def derive_opportunities(
        self,
        primary_site: CompetitorSourceRecord,
        gaps: list[CompetitiveGap],
        positioning_assessments: list[PositioningAssessment],
    ) -> list[CompetitiveOpportunity]:
        """Generate grounded, non-infringing strategic opportunities."""
        opportunities: list[CompetitiveOpportunity] = []

        for gap in gaps:
            opp_id = f"opp-{uuid.uuid4().hex[:8]}"

            if gap.gap_type == "offering_presentation_gap":
                opportunities.append(
                    CompetitiveOpportunity(
                        opportunity_id=opp_id,
                        title=f"Articulate Feature in Marketing Copy: {gap.title.split(':')[-1].strip()}",
                        title_ar=f"إبراز الميزة في الخطاب التسويقي للموقع: {gap.title.split(':')[-1].strip()}",
                        opportunity_type="Feature Communication",
                        primary_site=primary_site.site_id,
                        affected_competitors=gap.affected_competitors,
                        supporting_evidence_ids=gap.supporting_evidence_ids,
                        observed_difference=gap.observed_difference,
                        strategic_interpretation="Clarifying feature parity in web copy prevents prospective clients from disqualifying the solution early.",
                        suggested_action="Create a dedicated capability section or feature card clearly explaining how your platform addresses this workflow.",
                        suggested_action_ar="إضافة قسم مخصص أو بطاقة مزايا تشرح قدرة المنصة على تلبية هذه الاحتياجات بدقة.",
                        estimated_impact="high",
                        estimated_effort="small",
                        confidence_category="measured",
                        validation_required="Confirm feature availability and roadmapped capabilities with internal product team.",
                    )
                )

            elif gap.gap_type == "potential_differentiation":
                opportunities.append(
                    CompetitiveOpportunity(
                        opportunity_id=opp_id,
                        title=f"Double Down on Differentiator: {gap.title.split(':')[-1].strip()}",
                        title_ar=f"التركيز على نقطة التميز التنافسي: {gap.title.split(':')[-1].strip()}",
                        opportunity_type="Market Differentiation",
                        primary_site=primary_site.site_id,
                        affected_competitors=gap.affected_competitors,
                        supporting_evidence_ids=gap.supporting_evidence_ids,
                        observed_difference=gap.observed_difference,
                        strategic_interpretation="Owning an unaddressed capability in the competitive landscape creates high-margin defensibility.",
                        suggested_action="Elevate this capability to the main hero headline, social proof, and comparison collateral.",
                        suggested_action_ar="رفع هذه الميزة إلى العنوان الرئيسي ورسائل التسويق لتوضيح الفارق التنافسي للعملاء.",
                        estimated_impact="high",
                        estimated_effort="small",
                        confidence_category="observed",
                        validation_required="Ensure competitors haven't launched this capability recently under a different marketing term.",
                    )
                )

            elif gap.gap_type == "trust_signal_gap":
                opportunities.append(
                    CompetitiveOpportunity(
                        opportunity_id=opp_id,
                        title="Deploy High-Trust Customer Proof Assets",
                        title_ar="نشر عناصر الإثبات الاجتماعي والمصداقية",
                        opportunity_type="Trust Building",
                        primary_site=primary_site.site_id,
                        affected_competitors=gap.affected_competitors,
                        supporting_evidence_ids=gap.supporting_evidence_ids,
                        observed_difference=gap.observed_difference,
                        strategic_interpretation="Adding verified client logos and metrics accelerates decision-making for conservative buyers.",
                        suggested_action="Publish 2-3 structured customer mini-case studies and security badges in the above-the-fold hero section.",
                        suggested_action_ar="عرض 2-3 دراسات حالة سريعة مع شعارات عملاء موثقة وشارات الأمان في الصفحة الرئيسية.",
                        estimated_impact="medium",
                        estimated_effort="small",
                        confidence_category="observed",
                        validation_required="Acquire marketing authorization from existing enterprise clients before publishing logos.",
                    )
                )

        if not opportunities:
            # Baseline opportunity
            opportunities.append(
                CompetitiveOpportunity(
                    opportunity_id=f"opp-{uuid.uuid4().hex[:8]}",
                    title="Continuous Value Proposition Refinement",
                    title_ar="التحسين المستمر لصياغة القيمة المقترحة",
                    opportunity_type="Messaging Enhancement",
                    primary_site=primary_site.site_id,
                    affected_competitors=[],
                    supporting_evidence_ids=[],
                    observed_difference="Competitive alignment across primary features.",
                    strategic_interpretation="Iterating on headline clarity and CTA reduction compounds conversion rates.",
                    suggested_action="A/B test action-oriented headlines against current copy.",
                    suggested_action_ar="إجراء اختبارات مقارنة للعناوين المحفزة على اتخاذ القرار مقابل العناوين الحالية.",
                    estimated_impact="medium",
                    estimated_effort="small",
                    confidence_category="inferred",
                    validation_required="Monitor bounce rates and session duration via web analytics.",
                )
            )

        return opportunities
