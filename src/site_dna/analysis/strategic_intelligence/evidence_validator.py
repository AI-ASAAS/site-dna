"""Deterministic Evidence Validator for Site DNA Phase 11."""

import re
from typing import Any

from site_dna.schemas.strategic_intelligence import (
    ConflictRecord,
    DuplicateFindingGroup,
    RoadmapAction,
    UnifiedFinding,
)

_FINANCIAL_OR_ROI_PATTERN = re.compile(
    r"(\b\d+%\s*(increase|boost|uplift|growth|revenue|conversion)|earn\s*\$[\d,]+|\$[\d,]+\s*(more|increase)|زيادة\s*\d+%|أرباح\s*إضافية)",
    re.IGNORECASE,
)


class StrategicEvidenceValidator:
    """Strictly validates cross-agent references, rejects hallucinations, and verifies DAG integrity."""

    def __init__(self):
        self.quarantined_claims: list[dict[str, Any]] = []

    def validate_action(self, action: RoadmapAction, valid_finding_ids: set[str]) -> bool:
        """Validate that an action item only references real findings and contains no fabricated ROI."""
        # 1. Reject financial or ROI hallucinations
        full_text = f"{action.title} {action.description} {' '.join(action.acceptance_criteria)}"
        if _FINANCIAL_OR_ROI_PATTERN.search(full_text):
            self.quarantined_claims.append(
                {
                    "item_id": action.action_id,
                    "reason": "Rejected ungrounded financial or ROI uplift prediction.",
                    "snippet": full_text[:150],
                }
            )
            return False

        # 2. Verify related finding references
        for fid in action.related_finding_ids:
            if fid not in valid_finding_ids:
                self.quarantined_claims.append(
                    {
                        "item_id": action.action_id,
                        "reason": f"Action references non-existent finding ID: '{fid}'.",
                    }
                )
                return False

        return True

    def validate_duplicate_group(self, group: DuplicateFindingGroup, valid_finding_ids: set[str]) -> bool:
        """Verify that all members of a duplicate group exist and are valid."""
        for f in group.findings:
            if f.unified_finding_id not in valid_finding_ids:
                return False
        return len(group.findings) >= 2

    def validate_conflicts(self, conflicts: list[ConflictRecord], valid_finding_ids: set[str]) -> list[ConflictRecord]:
        """Filter out conflicts that reference non-existent findings."""
        valid_conflicts = []
        for c in conflicts:
            valid_ids = [fid for fid in c.finding_ids if fid in valid_finding_ids]
            if len(valid_ids) >= 1:
                valid_conflicts.append(c)
        return valid_conflicts

    def validate_plan_acyclicity(self, actions: list[RoadmapAction]) -> bool:
        """Confirm that the action backlog has no circular dependencies."""
        action_map = {a.action_id: a for a in actions}
        visited: dict[str, int] = {}

        def dfs(node: str) -> bool:
            visited[node] = 1
            action = action_map.get(node)
            if action:
                for dep in action.dependencies:
                    if dep in action_map:
                        if visited.get(dep, 0) == 1:
                            return False  # Cycle detected
                        if visited.get(dep, 0) == 0 and not dfs(dep):
                            return False
            visited[node] = 2
            return True

        for a in actions:
            if visited.get(a.action_id, 0) == 0:
                if not dfs(a.action_id):
                    return False
        return True
