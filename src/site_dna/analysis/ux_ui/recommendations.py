"""Recommendation engine generating prioritized, actionable UX/UI improvements."""

from site_dna.schemas.ux_ui import (
    RecommendationEffort,
    RecommendationImpact,
    RecommendationPriority,
    UXFinding,
    UXRecommendation,
)


class UXRecommendationEngine:
    """Derives actionable, prioritized UX recommendations from validated findings."""

    @staticmethod
    def generate_recommendations(
        findings: list[UXFinding],
        max_recommendations: int = 10,
    ) -> list[UXRecommendation]:
        """Convert validated findings into prioritized recommendations with validation methods."""
        recommendations: list[UXRecommendation] = []
        validated = [f for f in findings if f.is_validated]

        # Sort findings by severity priority: critical -> high -> medium -> low -> informational
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}
        sorted_findings = sorted(validated, key=lambda f: severity_order.get(f.severity, 3))

        for idx, f in enumerate(sorted_findings[:max_recommendations], 1):
            rec_id = f"REC-UX-{idx:02d}"

            # Determine priority and effort
            if f.severity == "critical":
                priority: RecommendationPriority = "P1"
                impact: RecommendationImpact = "high"
                effort: RecommendationEffort = "medium"
            elif f.severity == "high":
                priority = "P1"
                impact = "high"
                effort = "small"
            elif f.severity == "medium":
                priority = "P2"
                impact = "medium"
                effort = "small"
            else:
                priority = "P3"
                impact = "low"
                effort = "small"

            val_method = (
                f"فحص صفحة '{f.source_page}' بعد التعديل والتأكد من إزالة المشكلة برمجياً وبصرياً عبر محاكاة الجوال."
            )

            rec = UXRecommendation(
                recommendation_id=rec_id,
                related_finding_ids=[f.finding_id],
                evidence_ids=f.evidence_ids,
                title=f"معالجة: {f.title}",
                problem_statement=f.description,
                affected_component=f.element_reference or f.source_page,
                source_evidence=f"الصفحة: {f.source_page} | النافذة: {f.viewport}",
                proposed_solution=f.recommended_action or "تنفيذ التعديل المقترح وفق المعايير الإرشادية.",
                expected_improvement=f.potential_user_impact or "تحسين انسيابية التجربة وتقليل معدل الارتداد.",
                estimated_effort=effort,
                expected_impact=impact,
                priority=priority,
                validation_method=val_method,
            )
            recommendations.append(rec)

        return recommendations
