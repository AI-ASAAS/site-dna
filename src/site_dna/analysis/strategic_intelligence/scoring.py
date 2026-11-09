"""Strategic Scoring & Statistics Calculator for Site DNA Phase 11."""

from collections import Counter

from site_dna.schemas.strategic_intelligence import (
    ConflictRecord,
    DuplicateFindingGroup,
    HumanReviewTask,
    RoadmapAction,
    RootCauseCandidate,
    SourceCoverageAssessment,
    StrategicOpportunity,
    StrategicStatistics,
    UnifiedFinding,
)


class StrategicScoringEngine:
    """Calculates coverage metrics, backlog health, and priority distributions without averaging unrelated agent scores."""

    def compute_statistics(
        self,
        coverage: SourceCoverageAssessment,
        raw_findings_count: int,
        unified_findings: list[UnifiedFinding],
        duplicate_groups: list[DuplicateFindingGroup],
        conflicts: list[ConflictRecord],
        root_causes: list[RootCauseCandidate],
        opportunities: list[StrategicOpportunity],
        actions: list[RoadmapAction],
        manual_reviews: list[HumanReviewTask],
    ) -> StrategicStatistics:
        """Compute aggregate statistics and distribution metrics."""
        priority_counts = Counter(a.priority for a in actions)
        wave_counts = Counter(f"Wave {a.wave_number}" for a in actions)
        verified_count = sum(1 for a in actions if a.status == "verified_completed")

        # Compute empirical Strategic Health Index (0-100)
        p0_count = priority_counts.get("P0", 0)
        p1_count = priority_counts.get("P1", 0)
        p2_count = priority_counts.get("P2", 0)
        p3_count = priority_counts.get("P3", 0)
        deductions = (p0_count * 15.0) + (p1_count * 8.0) + (p2_count * 3.0) + (p3_count * 1.0)
        idx_val = round(max(20.0, min(100.0, 100.0 - deductions)), 1)

        if idx_val >= 85.0:
            label_ar = "ممتاز / ناضج استراتيجياً"
        elif idx_val >= 70.0:
            label_ar = "جيد / استقرار ملحوظ"
        elif idx_val >= 50.0:
            label_ar = "متوسط / يتطلب تدخلات هيكلية"
        else:
            label_ar = "حرج / مخاطر وتقاطعات متراكمة"

        return StrategicStatistics(
            source_coverage_percent=coverage.coverage_percentage,
            total_raw_findings=raw_findings_count,
            unified_findings_count=len(unified_findings),
            duplicate_groups_count=len(duplicate_groups),
            conflicts_count=len(conflicts),
            root_cause_candidates_count=len(root_causes),
            strategic_opportunities_count=len(opportunities),
            actions_count=len(actions),
            actions_by_priority=dict(priority_counts),
            actions_by_wave=dict(wave_counts),
            manual_reviews_count=len(manual_reviews),
            verified_actions_count=verified_count,
            strategic_index=idx_val,
            index_label_ar=label_ar,
        )
