"""Strategic Recommendation Synthesizer for Site DNA Phase 11."""

from site_dna.schemas.strategic_intelligence import (
    ConflictRecord,
    DuplicateFindingGroup,
    RoadmapAction,
    StrategicOpportunity,
    UnifiedFinding,
)


class StrategicRecommendationEngine:
    """Extracts top actionable strategic recommendations from backlog, opportunities, and conflicts."""

    def build_recommendations(
        self,
        actions: list[RoadmapAction],
        opportunities: list[StrategicOpportunity],
        conflicts: list[ConflictRecord],
    ) -> list[dict[str, str]]:
        """Produce top executive recommendations."""
        recs = []

        # P0/P1 top actions
        urgent_actions = [a for a in actions if a.priority in ("P0", "P1")]
        for a in urgent_actions[:4]:
            recs.append(
                {
                    "id": a.action_id,
                    "title": a.title,
                    "title_ar": a.title_ar or a.title,
                    "priority": a.priority,
                    "role": a.suggested_owner_role,
                    "summary": a.description,
                    "summary_ar": a.description_ar or a.description,
                }
            )

        # High-impact opportunities
        for opp in opportunities[:3]:
            recs.append(
                {
                    "id": opp.opportunity_id,
                    "title": opp.title,
                    "title_ar": opp.title_ar or opp.title,
                    "priority": "Strategic",
                    "role": "Product Owner",
                    "summary": opp.strategic_interpretation,
                    "summary_ar": opp.expected_type_of_benefit,
                }
            )

        return recs
