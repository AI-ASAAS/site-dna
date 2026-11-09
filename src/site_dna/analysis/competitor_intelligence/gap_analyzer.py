"""Competitive Gap Analysis Engine for Site DNA Phase 08."""

import uuid

from site_dna.core.logging import get_logger
from site_dna.schemas.competitor_intelligence import (
    CompetitiveGap,
    CompetitorSourceRecord,
    FeatureComparisonRecord,
    PricingRecord,
    TrustAssessment,
)

logger = get_logger("analysis.competitor_intelligence.gap_analyzer")


class CompetitiveGapAnalyzer:
    """Identifies evidence-backed gaps between primary and competitor website representations."""

    def identify_gaps(
        self,
        primary_site: CompetitorSourceRecord,
        competitor_sites: list[CompetitorSourceRecord],
        feature_matrix: list[FeatureComparisonRecord],
        pricing_records: list[PricingRecord],
        trust_assessments: list[TrustAssessment],
    ) -> list[CompetitiveGap]:
        """Analyze differences in observed features, pricing clarity, and trust signals."""
        gaps: list[CompetitiveGap] = []

        # 1. Feature Representation Gaps
        for feat in feature_matrix:
            comp_observed = [
                comp_id
                for comp_id, info in feat.competitor_statuses.items()
                if info.get("status") in ("observed_present", "claimed")
            ]
            if comp_observed and feat.primary_status == "not_found_in_sample":
                gaps.append(
                    CompetitiveGap(
                        gap_id=f"gap-{uuid.uuid4().hex[:8]}",
                        title=f"Feature Not Highlighted on Primary Site: {feat.feature_name}",
                        gap_type="offering_presentation_gap",
                        description=(
                            f"Competitor(s) {', '.join(comp_observed)} publicly highlight '{feat.feature_name}' on their websites, "
                            f"whereas this capability was not found in the analyzed pages of the primary website."
                        ),
                        description_ar=(
                            f"يبرز المنافسون ({', '.join(comp_observed)}) ميزة '{feat.feature_name_ar}' في صفحاتهم، "
                            f"بينما لم يتم العثور على ذكر لهذه الميزة في الصفحات المفحوصة للموقع المستهدف (ملاحظة: هذا لا يؤكد غياب الميزة لدى الشركة بل غياب إبرازها بالموقع)."
                        ),
                        observed_difference=f"Mentioned on {len(comp_observed)} competitor(s), absent in primary site sample.",
                        primary_status="not_found_in_sample",
                        competitor_status="observed_present",
                        supporting_evidence_ids=[
                            feat.competitor_statuses[c]["evidence_id"]
                            for c in comp_observed
                            if feat.competitor_statuses[c].get("evidence_id")
                        ],
                        affected_competitors=comp_observed,
                        strategic_implication="Prospective customers evaluating both websites may perceive a feature deficiency.",
                        validation_required="Verify internally whether this capability is offered and should be added to the marketing website.",
                    )
                )

            # Check potential differentiation where primary has feature and competitors do not
            if feat.primary_status == "observed_present" and not comp_observed:
                gaps.append(
                    CompetitiveGap(
                        gap_id=f"gap-{uuid.uuid4().hex[:8]}",
                        title=f"Potential Competitive Advantage: {feat.feature_name}",
                        gap_type="potential_differentiation",
                        description=(
                            f"Primary website prominently features '{feat.feature_name}', "
                            f"which was not found in the collected pages of the evaluated competitors."
                        ),
                        description_ar=(
                            f"يمتلك الموقع ميزة تفضيلية محتملة بإبراز '{feat.feature_name_ar}'، "
                            f"حيث لم يتم رصدها في الصفحات المفحوصة للمنافسين."
                        ),
                        observed_difference="Featured on primary site, not found in competitor samples.",
                        primary_status="observed_present",
                        competitor_status="not_found_in_sample",
                        supporting_evidence_ids=[feat.primary_evidence_id] if feat.primary_evidence_id else [],
                        affected_competitors=[c.site_id for c in competitor_sites],
                        strategic_implication="Valuable differentiation anchor to emphasize in value propositions and ad copy.",
                        validation_required="Confirm if competitors offer this under alternative branding or unindexed product suites.",
                    )
                )

        # 2. Pricing Transparency Gaps
        p_pricing = [pr for pr in pricing_records if pr.site_id == primary_site.site_id]
        comp_with_prices = [
            pr.site_id for pr in pricing_records if pr.site_id != primary_site.site_id and pr.amount is not None
        ]
        p_has_prices = any(pr.amount is not None for pr in p_pricing)

        if comp_with_prices and not p_has_prices:
            gaps.append(
                CompetitiveGap(
                    gap_id=f"gap-{uuid.uuid4().hex[:8]}",
                    title="Self-Serve Pricing Transparency Gap",
                    gap_type="content_gap",
                    description=(
                        f"Competitor(s) {', '.join(comp_with_prices)} publish self-serve pricing tiers, "
                        f"while the primary website relies on custom inquiries without published pricing numbers."
                    ),
                    description_ar=(
                        f"يقدم المنافسون ({', '.join(comp_with_prices)}) باقات تسعيرية علنية معلنة، "
                        f"في حين يعتمد الموقع المستهدف على التواصل المباشر دون نشر أرقام الأسعار."
                    ),
                    observed_difference="Self-serve published pricing vs. contact-sales only.",
                    primary_status="contact_sales",
                    competitor_status="published_pricing",
                    supporting_evidence_ids=[],
                    affected_competitors=comp_with_prices,
                    strategic_implication="Price-sensitive buyers seeking quick self-serve purchase may favor transparent competitors.",
                    validation_required="Evaluate if business model allows introducing a transparent starter tier or calculator.",
                )
            )

        # 3. Trust Signal Gaps
        p_trust = next((t for t in trust_assessments if t.site_id == primary_site.site_id), None)
        if p_trust and p_trust.named_testimonials_count == 0:
            comps_with_social_proof = [
                t.site_id
                for t in trust_assessments
                if t.site_id != primary_site.site_id and t.named_testimonials_count > 0
            ]
            if comps_with_social_proof:
                gaps.append(
                    CompetitiveGap(
                        gap_id=f"gap-{uuid.uuid4().hex[:8]}",
                        title="Social Proof and Customer Testimonial Gap",
                        gap_type="trust_signal_gap",
                        description=(
                            "Competitors display named testimonials and customer endorsements, "
                            "which were not observed on the primary website's inspected pages."
                        ),
                        description_ar=(
                            "يعرض المنافسون آراء عملاء وشعارات شركاء موثقة، "
                            "بينما تفتقر الصفحات المفحوصة للموقع المستهدف لعناصر الإثبات الاجتماعي المباشرة."
                        ),
                        observed_difference="Lack of visible customer testimonials and case studies.",
                        primary_status="not_found_in_sample",
                        competitor_status="observed_present",
                        supporting_evidence_ids=[],
                        affected_competitors=comps_with_social_proof,
                        strategic_implication="Diminishes initial trust for first-time visitors comparing options.",
                        validation_required="Collect and publish client logos and verified case studies.",
                    )
                )

        return gaps
