"""Unified Action Backlog Generator for Site DNA Phase 11."""

from typing import Any

from site_dna.analysis.strategic_intelligence.prioritization import StrategicPrioritizer
from site_dna.schemas.strategic_intelligence import (
    ActionOwnerRole,
    DuplicateFindingGroup,
    PriorityLevel,
    RoadmapAction,
    UnifiedFinding,
)


class ActionBacklogGenerator:
    """Transforms prioritized findings and canonical duplicate groups into concrete, executable tasks."""

    def __init__(self):
        self.prioritizer = StrategicPrioritizer()

    def generate_backlog(
        self,
        findings: list[UnifiedFinding],
        duplicate_groups: list[DuplicateFindingGroup],
        max_actions: int = 50,
    ) -> list[RoadmapAction]:
        """Synthesize unified roadmap actions."""
        actions: list[RoadmapAction] = []
        handled_finding_ids: set[str] = set()

        # 1. First, create unified actions from duplicate groups (addressing the root cause)
        for g in duplicate_groups:
            finding_ids = [f.unified_finding_id for f in g.findings]
            handled_finding_ids.update(finding_ids)

            # Determine best owner role
            owner: ActionOwnerRole = "Frontend Developer"
            if "contrast" in g.category.lower() or "visual" in g.category.lower():
                owner = "UI/UX Designer"
            elif "security" in g.category.lower() or "header" in g.canonical_title.lower():
                owner = "Security Specialist"
            elif "label" in g.canonical_title.lower() or "a11y" in g.category.lower():
                owner = "Accessibility Specialist"
            elif "seo" in g.category.lower() or "link" in g.canonical_title.lower():
                owner = "SEO Specialist"
            elif "content" in g.category.lower() or "cta" in g.canonical_title.lower():
                owner = "Content Specialist"

            # Compute priority from highest severity in group
            p_assessments = [self.prioritizer.assess_finding_priority(f) for f in g.findings]
            best_assessment = min(p_assessments, key=lambda a: {"P0": 0, "P1": 1, "P2": 2, "P3": 3}[a.priority_level])

            actions.append(
                RoadmapAction(
                    title=f"Resolve Cross-Domain Defect: {g.canonical_title}",
                    title_ar=f"معالجة الخلل التقني المشترك: {g.canonical_title_ar or g.canonical_title}",
                    description=f"Unified remediation addressing findings across {', '.join(g.source_agents)}: {g.deduplication_reason}",
                    description_ar=f"إجراء علاجي موحد لمعالجة الملاحظات المرصودة من: {', '.join(g.source_agents)}. {g.deduplication_reason_ar or ''}",
                    category=g.category,
                    priority=best_assessment.priority_level,
                    wave_number=2,
                    related_finding_ids=finding_ids,
                    related_recommendation_ids=[],
                    evidence_ids=g.all_evidence_ids,
                    affected_pages=g.affected_pages,
                    suggested_owner_role=owner,
                    estimated_effort="medium",
                    impact_category="high_friction",
                    confidence=g.confidence,
                    dependencies=[],
                    acceptance_criteria=[
                        f"Implement fix addressing {g.canonical_title} across all affected templates.",
                        "Verify no regression in related domain checks.",
                        "Re-run automated verification test in browser.",
                    ],
                    acceptance_criteria_ar=[
                        f"تطبيق الإصلاح البرمجي لـ {g.canonical_title_ar or g.canonical_title} عبر كافة القوالب المتأثرة.",
                        "التحقق من عدم حدوث أي تراجع في فحوصات المجالات المرتبطة.",
                        "إعادة فحص العنصر آلياً عبر المتصفح للتأكد من المعالجة.",
                    ],
                    verification_method="Automated browser DOM and style re-test.",
                    verification_method_ar="إعادة فحص شجرة DOM وخصائص الأنماط آلياً عبر المتصفح.",
                    status="proposed",
                )
            )

        # 2. Next, generate distinct actions for high-impact individual findings not in duplicate groups
        for f in findings:
            if f.unified_finding_id in handled_finding_ids:
                continue

            p_eval = self.prioritizer.assess_finding_priority(f)

            # Determine owner role
            owner: ActionOwnerRole = "Frontend Developer"
            if f.source_phase == "security_privacy":
                owner = "Security Specialist"
            elif f.source_phase == "accessibility":
                owner = "Accessibility Specialist"
            elif f.source_phase == "content_marketing":
                owner = "Content Specialist"
            elif f.source_phase == "technical_seo":
                owner = "SEO Specialist"
            elif f.source_phase == "visual_identity":
                owner = "UI/UX Designer"

            actions.append(
                RoadmapAction(
                    title=f"Remediate: {f.title}",
                    title_ar=f"معالجة: {f.title_ar or f.title}",
                    description=f"Specific domain fix ({f.source_agent}): {f.description}",
                    description_ar=f"إصلاح فني متخصص ({f.source_agent}): {f.description_ar or f.description}",
                    category=f.category,
                    priority=p_eval.priority_level,
                    wave_number=1 if p_eval.priority_level == "P0" else 2,
                    related_finding_ids=[f.unified_finding_id],
                    related_recommendation_ids=[],
                    evidence_ids=f.evidence_ids,
                    affected_pages=[f.page_url] if f.page_url else [],
                    suggested_owner_role=owner,
                    estimated_effort="small" if "header" in f.title.lower() else "medium",
                    impact_category=f.normalized_impact_category,
                    confidence=0.9 if f.confidence_category == "high" else 0.7,
                    dependencies=[],
                    acceptance_criteria=[
                        f"Address root condition of {f.title}.",
                        "Verify compliance against domain benchmark.",
                    ],
                    acceptance_criteria_ar=[
                        f"معالجة أسباب {f.title_ar or f.title}.",
                        "التأكد من مطابقة المعايير الفنية المعتمدة للمجال.",
                    ],
                    verification_method=f"Retest via {f.source_agent} verification routine.",
                    verification_method_ar=f"إعادة الفحص الموجه عبر محرك {f.source_agent}.",
                    status="proposed",
                )
            )

            handled_finding_ids.add(f.unified_finding_id)
            if len(actions) >= max_actions:
                break

        return actions
