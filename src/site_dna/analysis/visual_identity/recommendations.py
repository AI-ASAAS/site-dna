"""Actionable, prioritized design recommendation engine based on validated findings."""

from site_dna.schemas.visual_identity import VisualFinding, VisualRecommendation


class RecommendationEngine:
    """Derives focused, prioritized UI/UX design recommendations from validated findings."""

    @staticmethod
    def generate_recommendations(
        findings: list[VisualFinding],
        max_recommendations: int = 10,
    ) -> list[VisualRecommendation]:
        """Convert validated findings into prioritized, actionable engineering recommendations."""
        recommendations: list[VisualRecommendation] = []
        rec_counter = 1

        # Process higher severity findings first
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "informational": 4}
        sorted_findings = sorted(
            [f for f in findings if f.is_validated],
            key=lambda x: severity_order.get(x.severity, 2),
        )

        for finding in sorted_findings:
            if len(recommendations) >= max_recommendations:
                break

            # Determine effort & impact
            if finding.category == "contrast":
                effort = "small"
                impact = "high"
                priority = "P1"
                action = f"تعديل قيم الألوان في CSS ({finding.suggested_action})"
            elif finding.category == "responsive_visual":
                effort = "medium"
                impact = "high"
                priority = "P1"
                action = f"معالجة انكسار العرض التجاوبي وضبط محددات العرض ({finding.suggested_action})"
            elif finding.category == "visual_hierarchy":
                effort = "small"
                impact = "high"
                priority = "P1" if finding.severity in ("critical", "high") else "P2"
                action = f"تعزيز التمايز البصري لعناصر التوجيه ({finding.suggested_action})"
            elif finding.category == "typography":
                effort = "small"
                impact = "medium"
                priority = "P2"
                action = f"توحيد هرمية وأوزان الخطوط ({finding.suggested_action})"
            elif finding.category == "color":
                effort = "medium"
                impact = "medium"
                priority = "P2"
                action = f"إعادة هيكلة لوحة الألوان وتوحيد استخدام المتغيرات ({finding.suggested_action})"
            else:
                effort = "medium"
                impact = "low"
                priority = "P3"
                action = finding.suggested_action

            rec = VisualRecommendation(
                recommendation_id=f"REC-{rec_counter:02d}",
                related_finding_ids=[finding.finding_id],
                evidence_ids=finding.evidence_ids,
                title=f"تحسين: {finding.title}",
                problem_statement=finding.description,
                proposed_correction=action,
                affected_page_or_component=finding.page_url or "عناصر الواجهة العامة",
                expected_visual_improvement=finding.potential_impact.replace("تشتيت", "تعزيز").replace(
                    "صعوبة", "تسهيل"
                ),
                estimated_effort=effort,
                expected_impact=impact,
                priority=priority,
            )
            recommendations.append(rec)
            rec_counter += 1

        return recommendations
