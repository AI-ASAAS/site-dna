"""Actionable technical SEO recommendation synthesis engine."""

from site_dna.schemas.technical_seo import (
    TechnicalSEOFinding,
    TechnicalSEORecommendation,
)


class TechnicalSEORecommendationEngine:
    """Transforms validated technical findings into prioritized, actionable technical fixes."""

    PRIORITY_MAP: dict[str, str] = {
        "critical": "p1",
        "high": "p1",
        "medium": "p2",
        "low": "p3",
        "info": "p3",
    }

    IMPACT_MAP: dict[str, str] = {
        "critical": "high",
        "high": "high",
        "medium": "medium",
        "low": "low",
        "info": "low",
    }

    EFFORT_MAP: dict[str, str] = {
        "TS-CRW-01": "small",
        "TS-IDX-NOINDEX": "small",
        "TS-CAN-MISSING": "small",
        "TS-MET-NOTITLE": "small",
        "TS-MET-NODESC": "small",
        "TS-ROB-MISSING": "small",
        "TS-SIT-MISSING": "medium",
        "TS-PRF-SLOW-TTFB": "large",
        "TS-CWV-LCP-SLOW": "large",
        "TS-JS-CONTENT-RENDERED": "large",
    }

    @classmethod
    def generate_recommendations(
        cls,
        findings: list[TechnicalSEOFinding],
        max_recommendations: int = 10,
    ) -> list[TechnicalSEORecommendation]:
        """Generate prioritized technical recommendations tied directly to validated findings."""
        recommendations: list[TechnicalSEORecommendation] = []
        if not findings:
            return recommendations

        # Sort findings by severity (critical, high, medium, low)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
        sorted_findings = sorted(findings, key=lambda f: severity_order.get(f.severity, 3))

        for idx, f in enumerate(sorted_findings[:max_recommendations], 1):
            rec_id = f"TR-{idx:02d}"
            priority = cls.PRIORITY_MAP.get(f.severity, "p2")
            impact = cls.IMPACT_MAP.get(f.severity, "medium")
            effort = cls.EFFORT_MAP.get(f.finding_id, "medium")

            rec = TechnicalSEORecommendation(
                recommendation_id=rec_id,
                title=f"معالجة: {f.title}",
                related_finding_ids=[f.finding_id],
                category=f.category,
                affected_urls=[f.page_url],
                technical_problem=f.description,
                supporting_evidence_ids=f.evidence_ids[:3],
                proposed_fix=f.recommended_action,
                implementation_guidance="تطبيق الإصلاح التقني في الخادم أو كود القوالب HTML، ثم التحقق عبر إرسال طلب فحص مباشر.",
                expected_technical_benefit=f.potential_technical_impact,
                estimated_impact=impact,
                estimated_effort=effort,
                priority=priority,
                verification_method="inspection",
                limitations=[
                    "يتطلب التحقق النهائي فحص الاستجابة الحية عبر أداة فحص العناوين في Google Search Console."
                ],
            )
            recommendations.append(rec)

        return recommendations
