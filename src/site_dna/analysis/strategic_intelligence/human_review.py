"""Human Review Workflow Generator for Site DNA Phase 11."""

from typing import Any

from site_dna.schemas.strategic_intelligence import (
    ConflictRecord,
    HumanReviewTask,
    RootCauseCandidate,
    UnifiedFinding,
)


class HumanReviewGenerator:
    """Generates structured review tasks for decisions requiring human cognitive, business, or security judgment."""

    def generate_review_tasks(
        self,
        findings: list[UnifiedFinding],
        conflicts: list[ConflictRecord],
        root_causes: list[RootCauseCandidate],
    ) -> list[HumanReviewTask]:
        """Synthesize human review items."""
        tasks: list[HumanReviewTask] = []

        # 1. Tasks for unresolved conflicts requiring stakeholder decision
        for c in conflicts:
            if c.manual_review_required:
                tasks.append(
                    HumanReviewTask(
                        related_item_ids=[c.conflict_id] + c.finding_ids,
                        review_reason=f"Tradeoff Decision: {c.conflict_type.replace('_', ' ').title()}",
                        review_reason_ar=f"قرار موازنة استراتيجية: {c.description_ar or c.description}",
                        supporting_evidence_ids=c.supporting_evidence_ids,
                        question_for_reviewer=f"How should the team resolve the tension between {c.conflict_type}?",
                        question_for_reviewer_ar=f"كيف يوجّه الفريق التقني بحسم التعارض بين متطلبات المجالين؟",
                        recommended_options=[
                            c.proposed_resolution,
                            "Prioritize security/accessibility baseline strictly.",
                            "Defer changes pending deeper user research.",
                        ],
                        status="pending",
                    )
                )

        # 2. Tasks for findings explicitly flagged as manual_review_required (e.g. from Phase 10)
        manual_findings = [f for f in findings if f.verification_state == "manual_review_required"]
        for mf in manual_findings[:5]:  # Bound to top 5 to prevent review fatigue
            tasks.append(
                HumanReviewTask(
                    related_item_ids=[mf.unified_finding_id],
                    review_reason=f"Manual Verification Required: {mf.title}",
                    review_reason_ar=f"فحص بشري مطلوب: {mf.title_ar or mf.title}",
                    supporting_evidence_ids=mf.evidence_ids,
                    question_for_reviewer=f"Please verify {mf.title} using assistive technology or appropriate manual testing tools.",
                    question_for_reviewer_ar=f"يرجى التحقق اليدوي من {mf.title_ar or mf.title} باستخدام الأدوات المساعدة أو المراجعة المباشرة.",
                    recommended_options=[
                        "Confirm as verified barrier requiring remediation.",
                        "Mark as acceptable / not applicable in current context.",
                        "Request supplementary technical evidence.",
                    ],
                    status="pending",
                )
            )

        # 3. Tasks for speculative root causes
        for rc in root_causes:
            if rc.confidence == "possible_candidate":
                tasks.append(
                    HumanReviewTask(
                        related_item_ids=[rc.cause_id] + rc.related_finding_ids,
                        review_reason=f"Verify Root Cause Hypothesis: {rc.title}",
                        review_reason_ar=f"التحقق من فرضية السبب الجذري: {rc.title_ar or rc.title}",
                        supporting_evidence_ids=rc.evidence_ids,
                        question_for_reviewer="Does the internal architecture or design system corroborate this hypothesized root cause?",
                        question_for_reviewer_ar="هل تؤكد بنية النظام أو دليل الهوية الداخلي هذه الفرضية للسبب الجذري؟",
                        recommended_options=[
                            "Confirm root cause hypothesis and apply centralized fix.",
                            "Refute hypothesis; treat findings as separate issues.",
                        ],
                        status="pending",
                    )
                )

        return tasks
