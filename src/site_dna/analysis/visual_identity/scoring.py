"""Explainable visual identity scoring engine implementing the Phase 04 rubric."""

from typing import Optional

from site_dna.schemas.visual_identity import VisualFinding, VisualScoreExplanation

# Dimension configuration: name -> (weight, category_filter)
DIMENSIONS = {
    "Color System & Harmony": {
        "weight": 0.20,
        "categories": {"color", "contrast"},
        "desc_ar": "وضوح لوحة الألوان وتناسقها اللوني ونسب تباين النصوص الإرشادية.",
    },
    "Typography & Readability": {
        "weight": 0.20,
        "categories": {"typography"},
        "desc_ar": "التدرج الطباعي، تناسق الخطوط، مقروئية النصوص ودعم الاتجاه العربي.",
    },
    "Visual Hierarchy": {
        "weight": 0.20,
        "categories": {"visual_hierarchy", "spacing", "alignment"},
        "desc_ar": "بروز العناوين الرئيسية، تمييز أزرار الإجراء، وتوازن المساحات البيضاء.",
    },
    "Cross-Page & Component Consistency": {
        "weight": 0.25,
        "categories": {"component_consistency", "branding"},
        "desc_ar": "اتساق المكونات المتكررة (الترويسة، الأزرار، البطاقات، التذييل) عبر الصفحات.",
    },
    "Responsive Visual Consistency": {
        "weight": 0.15,
        "categories": {"responsive_visual"},
        "desc_ar": "التكيف البصري بين سطح المكتب والجوال وسلامة التخطيط من الفائض الأفقي.",
    },
}

SEVERITY_DEDUCTIONS = {
    "critical": 20.0,
    "high": 12.0,
    "medium": 6.0,
    "low": 3.0,
    "informational": 0.0,
}


class ScoringEngine:
    """Calculates explainable scores and transparent deductions across visual dimensions."""

    @staticmethod
    def calculate_scores(
        findings: list[VisualFinding],
        is_multipage: bool = True,
        pages_count: int = 1,
    ) -> tuple[Optional[float], list[VisualScoreExplanation]]:
        """Calculate weighted dimension scores and overall index per documented rubric."""
        explanations: list[VisualScoreExplanation] = []
        assessed_weighted_sum = 0.0
        assessed_weights_total = 0.0

        for dim_name, config in DIMENSIONS.items():
            weight = config["weight"]
            categories = config["categories"]

            # Handle single-page constraint for Cross-Page Consistency
            if dim_name == "Cross-Page & Component Consistency" and not is_multipage:
                explanations.append(
                    VisualScoreExplanation(
                        dimension_name=dim_name,
                        weight=weight,
                        score=None,
                        status="not_assessed",
                        explanation="لم يتم تقييم هذا البعد نظراً لتوافر صفحة واحدة فقط للموقع المستكشف.",
                        key_positive_factors=[],
                        key_negative_factors=[],
                        supporting_finding_ids=[],
                    )
                )
                continue

            # Filter relevant findings
            relevant_findings = [f for f in findings if f.category in categories and f.is_validated]
            supporting_ids = [f.finding_id for f in relevant_findings]

            total_deduction = sum(SEVERITY_DEDUCTIONS.get(f.severity, 6.0) for f in relevant_findings)
            score = max(0.0, min(100.0, 100.0 - total_deduction))

            # Build positives and negatives
            negatives = [f.title for f in relevant_findings]
            positives = []
            if not negatives:
                positives.append(f"التزام ممتاز بمعايير {config['desc_ar']}")
            elif score >= 75.0:
                positives.append(f"توازن جيد مع وجود ملاحظات تحسين طفيفة في {dim_name}")

            explanation_text = (
                f"تم احتساب النتيجة ({round(score, 1)}/100) بناءً على {len(relevant_findings)} ملاحظات مرصودة. "
                + config["desc_ar"]
            )

            explanations.append(
                VisualScoreExplanation(
                    dimension_name=dim_name,
                    weight=weight,
                    score=round(score, 1),
                    status="assessed",
                    explanation=explanation_text,
                    key_positive_factors=positives,
                    key_negative_factors=negatives,
                    supporting_finding_ids=supporting_ids,
                )
            )

            assessed_weighted_sum += score * weight
            assessed_weights_total += weight

        # Overall Score calculation
        assessed_count = sum(1 for e in explanations if e.status == "assessed")
        overall_score: Optional[float] = None

        if assessed_count >= 3 and assessed_weights_total > 0:
            overall_score = round(assessed_weighted_sum / assessed_weights_total, 1)

        return overall_score, explanations
