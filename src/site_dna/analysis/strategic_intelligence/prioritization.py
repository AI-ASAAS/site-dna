"""Prioritization Engine for Site DNA Phase 11."""


from site_dna.schemas.strategic_intelligence import PriorityAssessment, PriorityLevel, UnifiedFinding


class StrategicPrioritizer:
    """Computes transparent, explainable priority tiers (P0-P3) based on a 5-dimension rubric without ROI hallucinations."""

    WEIGHT_USER_IMPACT = 0.30
    WEIGHT_URGENCY = 0.25
    WEIGHT_CONFIDENCE = 0.20
    WEIGHT_REACH = 0.15
    WEIGHT_PRACTICALITY = 0.10

    def assess_finding_priority(self, finding: UnifiedFinding, total_site_pages: int = 1) -> PriorityAssessment:
        """Calculate weighted composite score and priority level for a unified finding."""
        # Dimension 1: User or Business Impact (0-100)
        impact_map = {
            "critical_blocker": 100.0,
            "high_friction": 80.0,
            "moderate_impairment": 50.0,
            "minor_observation": 25.0,
            "unknown": 40.0,
        }
        score_impact = impact_map.get(finding.normalized_impact_category, 50.0)

        # Dimension 2: Technical / Security / Accessibility Urgency (0-100)
        score_urgency = 40.0
        if finding.source_phase == "security_privacy":
            if finding.original_severity in ("critical", "high"):
                score_urgency = 95.0
            else:
                score_urgency = 70.0
        elif finding.source_phase == "accessibility":
            if finding.original_severity in ("critical", "serious"):
                score_urgency = 90.0
            else:
                score_urgency = 65.0
        elif finding.source_phase == "technical_seo":
            score_urgency = 60.0

        # Dimension 3: Evidence Confidence (0-100)
        conf_map = {
            "high": 95.0,
            "medium": 70.0,
            "low": 40.0,
            "unverified": 20.0,
        }
        score_confidence = conf_map.get(finding.confidence_category, 70.0)

        # Dimension 4: Reach Across Pages (0-100)
        # If finding affects home page or global header/footer, reach is high
        score_reach = 60.0
        if not finding.page_url or finding.page_url.endswith("/") or "header" in finding.title.lower():
            score_reach = 90.0

        # Dimension 5: Implementation Practicality (0-100)
        # Small configuration fixes have high practicality (easy to fix)
        score_practicality = 75.0
        if "header" in finding.title.lower() or "meta" in finding.title.lower():
            score_practicality = 90.0
        elif "redesign" in finding.description.lower() or "architecture" in finding.description.lower():
            score_practicality = 40.0

        composite = (
            score_impact * self.WEIGHT_USER_IMPACT
            + score_urgency * self.WEIGHT_URGENCY
            + score_confidence * self.WEIGHT_CONFIDENCE
            + score_reach * self.WEIGHT_REACH
            + score_practicality * self.WEIGHT_PRACTICALITY
        )

        # Escalation rules for verified P0 blockers
        is_escalated = False
        escalation_reason = None

        if (
            finding.source_phase == "security_privacy"
            and finding.original_severity == "critical"
            and finding.verification_state == "confirmed_by_evidence"
        ):
            is_escalated = True
            escalation_reason = (
                "Escalated to P0 due to confirmed high-risk security vulnerability with active exploit potential."
            )
            level: PriorityLevel = "P0"
        elif composite >= 82.0:
            level = "P1"
        elif composite >= 60.0:
            level = "P2"
        else:
            level = "P3"

        justification = (
            f"Composite score {composite:.1f}/100 derived from Impact ({score_impact:.0f}), "
            f"Urgency ({score_urgency:.0f}), Confidence ({score_confidence:.0f}), "
            f"Reach ({score_reach:.0f}), Practicality ({score_practicality:.0f})."
        )
        justification_ar = (
            f"درجة الأولوية المركبة {composite:.1f}/100 محسوبة من: الأثر ({score_impact:.0f})، "
            f"الإلحاح التقني ({score_urgency:.0f})، موثوقية الأدلة ({score_confidence:.0f})، "
            f"مدى الانتشار ({score_reach:.0f})، وقابلية التطبيق ({score_practicality:.0f})."
        )

        return PriorityAssessment(
            item_id=finding.unified_finding_id,
            priority_level=level,
            composite_score=round(composite, 1),
            dimension_scores={
                "impact": score_impact,
                "urgency": score_urgency,
                "confidence": score_confidence,
                "reach": score_reach,
                "practicality": score_practicality,
            },
            justification=justification,
            justification_ar=justification_ar,
            is_escalated=is_escalated,
            escalation_reason=escalation_reason,
        )
