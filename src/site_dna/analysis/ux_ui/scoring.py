"""Explainable UX/UI scoring engine implementing the Phase 05 rubric."""

from typing import Optional

from site_dna.schemas.ux_ui import UXFinding, UXScoreExplanation

UX_DIMENSIONS = {
    "Navigation & Information Architecture": {
        "weight": 0.20,
        "categories": {"navigation", "information_architecture", "user_journey"},
        "desc_ar": "وضوح بنية التنقل، وضوح التسميات، سهولة الوصول للصفحات، وترابط المسارات.",
    },
    "Interaction & CTA Clarity": {
        "weight": 0.20,
        "categories": {"interaction", "cta_clarity"},
        "desc_ar": "بروز أزرار الإجراء الرئيسي، معقولية مساحات النقر، وتمايز العناصر التفاعلية.",
    },
    "Content Usability": {
        "weight": 0.15,
        "categories": {"content_usability"},
        "desc_ar": "قابلية المحتوى للمسح السريع، وضوح العناوين، توازن الفقرات، ودعم الاتجاه العربي.",
    },
    "Mobile Experience": {
        "weight": 0.20,
        "categories": {"responsive"},
        "desc_ar": "سلامة العرض على الجوال، انعدام الفائض الأفقي، وملاءمة أهداف اللمس بالإبهام.",
    },
    "Forms & Task Support": {
        "weight": 0.10,
        "categories": {"forms"},
        "desc_ar": "وضوح تسميات الحقول، تفادي الاعتماد الحصري على Placeholder، ووضوح أزرار الإرسال.",
    },
    "Accessibility Checks": {
        "weight": 0.15,
        "categories": {"accessibility"},
        "desc_ar": "وسوم الوصول للصور والأزرار، تدرج العناوين الهرمي، ونسب التباين اللوني WCAG AA.",
    },
}

SEVERITY_DEDUCTIONS = {
    "critical": 20.0,
    "high": 12.0,
    "medium": 6.0,
    "low": 3.0,
    "informational": 0.0,
}


class UXScoringEngine:
    """Calculates explainable usability scores with transparent deductions across UX dimensions."""

    @staticmethod
    def calculate_scores(
        findings: list[UXFinding],
        has_forms: bool = True,
        pages_count: int = 1,
    ) -> tuple[Optional[float], list[UXScoreExplanation]]:
        """Compute weighted dimension scores and overall index per documented rubric."""
        explanations: list[UXScoreExplanation] = []
        assessed_weighted_sum = 0.0
        assessed_weights_total = 0.0

        for dim_name, config in UX_DIMENSIONS.items():
            weight = config["weight"]
            categories = config["categories"]

            # If the site has zero forms, don't penalize it on Forms & Task Support
            if dim_name == "Forms & Task Support" and not has_forms:
                explanations.append(
                    UXScoreExplanation(
                        dimension_name=dim_name,
                        weight=weight,
                        score=None,
                        status="not_assessed",
                        explanation="لم يتم تقييم هذا البعد لعدم وجود نماذج مدخلات في العينة المستكشفة (موقع تعريفي/محتوى).",
                        key_positive_factors=[],
                        key_negative_factors=[],
                        supporting_finding_ids=[],
                    )
                )
                continue

            relevant_findings = [f for f in findings if f.category in categories and f.is_validated]
            supporting_ids = [f.finding_id for f in relevant_findings]

            total_deduction = sum(SEVERITY_DEDUCTIONS.get(f.severity, 6.0) for f in relevant_findings)
            score = max(0.0, min(100.0, 100.0 - total_deduction))

            negatives = [f.title for f in relevant_findings]
            positives = []
            if not negatives:
                positives.append(f"أداء وتوافق ممتاز مع معايير {config['desc_ar']}")
            elif score >= 75.0:
                positives.append(f"تجربة متماسكة بوجه عام مع وجود ملاحظات تحسين طفيفة في {dim_name}")

            explanation_text = (
                f"تم احتساب النتيجة ({round(score, 1)}/100) استناداً إلى {len(relevant_findings)} ملاحظة موثقة بالأدلة. "
                + config["desc_ar"]
            )

            explanations.append(
                UXScoreExplanation(
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
