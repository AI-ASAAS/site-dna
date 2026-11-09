"""Explainable scoring engine for Site DNA Content & Marketing Intelligence."""

from typing import Optional

from site_dna.schemas.content_marketing import (
    ContentFinding,
    ContentScore,
    PageContentRecord,
)


class ContentScoringEngine:
    """Calculates weighted, evidence-grounded rubric scores across 7 content dimensions."""

    DIMENSIONS = [
        ("value_proposition", "وضوح القيمة المقترحة (Value Proposition Clarity)", 0.20),
        ("messaging_clarity", "وضوح ودقة الرسائل التسويقية (Messaging Clarity & Specificity)", 0.20),
        ("service_content", "اكتمال شرح الخدمات والمنتجات (Product/Service Explanation)", 0.15),
        ("cta_action", "وضوح عبارات اتخاذ الإجراء (CTA Copy & Action Clarity)", 0.15),
        ("trust_claims", "الشفافية والمصداقية والادعاءات (Trust & Claim Transparency)", 0.10),
        ("brand_voice", "نبرة الصوت واتساق الهوية (Brand Voice & Consistency)", 0.10),
        ("audience_alignment", "ملاءمة المحتوى للجمهور المستهدف (Audience & Purpose Alignment)", 0.10),
    ]

    SEVERITY_DEDUCTIONS = {
        "critical": 25.0,
        "high": 15.0,
        "medium": 8.0,
        "low": 3.0,
    }

    @classmethod
    def calculate_scores(
        cls,
        findings: list[ContentFinding],
        pages: list[PageContentRecord],
    ) -> tuple[Optional[float], list[ContentScore]]:
        """Calculate dimension scores and normalized overall score."""
        if not pages:
            return None, []

        scores: list[ContentScore] = []
        active_weight_sum = 0.0
        weighted_score_sum = 0.0

        findings_by_category: dict[str, list[ContentFinding]] = {}
        for f in findings:
            cat = f.category
            findings_by_category.setdefault(cat, []).append(f)

        has_services = any(p.page_type in ("services", "products") or p.service_descriptions for p in pages)

        for dim_key, dim_title_ar, weight in cls.DIMENSIONS:
            # Check for neutral dimensions
            if dim_key == "service_content" and not has_services:
                scores.append(
                    ContentScore(
                        dimension_name=dim_key,
                        dimension_name_ar=dim_title_ar,
                        weight=weight,
                        score=None,
                        status="not_assessed",
                        rationale="لم يتم رصد صفحات أو أقسام مخصصة للخدمات أو المنتجات في الموقع؛ عومل البعد بحياد دون خصم.",
                        evidence_count=0,
                    )
                )
                continue

            # Calculate deductions
            cat_findings = findings_by_category.get(dim_key, [])
            deductions = sum(cls.SEVERITY_DEDUCTIONS.get(f.severity, 5.0) for f in cat_findings)
            raw_score = max(0.0, min(100.0, 100.0 - deductions))

            status = "assessed"
            rationale = (
                f"احتُسبت الدرجة ({raw_score:.1f}/100) استناداً إلى {len(cat_findings)} ملاحظة موثقة بالأدلة."
                if cat_findings
                else f"درجة مثالية ({raw_score:.1f}/100) لخلو البعد من أي ملاحظات سلبية موثقة."
            )

            scores.append(
                ContentScore(
                    dimension_name=dim_key,
                    dimension_name_ar=dim_title_ar,
                    weight=weight,
                    score=raw_score,
                    status=status,
                    rationale=rationale,
                    evidence_count=len(cat_findings),
                )
            )

            active_weight_sum += weight
            weighted_score_sum += raw_score * weight

        overall_score = None
        if active_weight_sum > 0:
            overall_score = round(weighted_score_sum / active_weight_sum, 1)

        return overall_score, scores
