"""Prioritized recommendation engine for content and copywriting optimization."""

from site_dna.schemas.content_marketing import (
    ContentFinding,
    ContentRecommendation,
    RecommendationEffort,
    RecommendationImpact,
    RecommendationPriority,
)


class ContentRecommendationEngine:
    """Generates actionable, prioritized content recommendations linked to validated findings."""

    @staticmethod
    def generate_recommendations(
        findings: list[ContentFinding],
        max_recommendations: int = 10,
    ) -> list[ContentRecommendation]:
        """Convert findings into prioritized actionable recommendations."""
        recommendations: list[ContentRecommendation] = []
        rec_counter = 0

        # Sort findings by severity (critical, high, medium, low)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.severity, 4))

        for f in sorted_findings:
            if rec_counter >= max_recommendations:
                break

            rec_counter += 1
            rec_id = f"CR-{rec_counter:02d}"
            f.recommendation_id = rec_id

            priority: RecommendationPriority = "p2"
            impact: RecommendationImpact = "medium"
            effort: RecommendationEffort = "small"

            if f.severity in ("critical", "high"):
                priority = "p1"
                impact = "high"
                effort = "medium"
            elif f.severity == "low":
                priority = "p3"
                impact = "low"
                effort = "small"

            rec_change = f"معالجة المشكلة: {f.title}."
            if "CTA" in f.title or "اتخاذ إجراء" in f.title:
                rec_change = "استبدال النص الحالي بعبارة تحث على إجراء محدد توضح القيمة المباشرة للزائر (مثل: 'ابدأ تجربتك المجانية' أو 'احجز استشارتك')."
            elif "H1" in f.title or "عنوان رئيسي" in f.title:
                rec_change = "إضافة عنوان H1 صريح ومباشر في أعلى الصفحة يشرح ما تقدمه المنصة والقيمة المحورية للعميل."
            elif "إحصائي" in f.title or "تفوق" in f.title or "ادعاء" in f.title:
                rec_change = (
                    "إسناد الأرقام والادعاءات التسويقية بروابط أو مصادر إثباتية داخلية لتعزيز المصداقية لدى الزوار."
                )
            elif "خدمات" in f.title:
                rec_change = (
                    "إثراء صفحة الخدمات بفقرات موجزة توضح مخرجات كل خدمة والجمهور المستهدف والخطوة التالية للطلب."
                )

            recommendations.append(
                ContentRecommendation(
                    recommendation_id=rec_id,
                    title=f"معالجة: {f.title}",
                    related_finding_ids=[f.finding_id],
                    affected_page=f.page_url,
                    affected_content=f.source_excerpt,
                    evidence_ids=f.evidence_ids[:3],
                    recommended_change=rec_change,
                    rationale=f.description,
                    expected_communication_benefit=f.potential_communication_impact
                    or "تحسين استيعاب الزائر للرسالة التسويقية ورفع جودة التواصل الرقمي.",
                    estimated_effort=effort,
                    estimated_impact=impact,
                    priority=priority,
                    verification_method="inspection",
                )
            )

        return recommendations
