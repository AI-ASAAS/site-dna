"""Dependency Planner & Topological Sequencer for Site DNA Phase 11."""

from collections import defaultdict
from typing import Any

from site_dna.schemas.strategic_intelligence import ActionDependency, RoadmapAction


class DependencyPlanner:
    """Calculates execution order and dependency graphs for roadmap actions with cycle detection."""

    def __init__(self):
        self.dependencies: list[ActionDependency] = []

    def add_dependency(
        self,
        action_id: str,
        depends_on_id: str,
        dep_type: str = "recommended_order",
        reason: str = "",
    ) -> None:
        """Register a prerequisite dependency."""
        if action_id == depends_on_id:
            return
        dep = ActionDependency(
            action_id=action_id,
            depends_on_action_id=depends_on_id,
            dependency_type="hard_blocker" if dep_type == "hard_blocker" else "recommended_order",
            reason=reason or f"Action '{action_id}' requires prerequisite '{depends_on_id}'.",
        )
        self.dependencies.append(dep)

    def resolve_dependencies_and_waves(self, actions: list[RoadmapAction]) -> list[RoadmapAction]:
        """Verify action IDs, detect cycles, and assign logical execution waves (1 to 4)."""
        action_map = {a.action_id: a for a in actions}

        # Build adjacency graph
        prereqs: dict[str, list[str]] = defaultdict(list)
        dependents: dict[str, list[str]] = defaultdict(list)

        # Ingest explicit action dependencies
        for a in actions:
            for dep_id in a.dependencies:
                if dep_id in action_map and dep_id != a.action_id:
                    prereqs[a.action_id].append(dep_id)
                    dependents[dep_id].append(a.action_id)

        # Cycle detection
        visited: dict[str, int] = {}
        has_cycle = False

        def check_cycle(node: str, stack: list[str]) -> bool:
            visited[node] = 1
            stack.append(node)
            for neigh in prereqs[node]:
                if visited.get(neigh, 0) == 1:
                    return True
                if visited.get(neigh, 0) == 0 and check_cycle(neigh, stack):
                    return True
            stack.pop()
            visited[node] = 2
            return False

        for aid in list(action_map.keys()):
            if visited.get(aid, 0) == 0:
                if check_cycle(aid, []):
                    has_cycle = True
                    break

        if has_cycle:
            # If cycle detected, break cyclic edges and fallback to priority-based waves
            prereqs.clear()

        # Assign execution waves (1 to 4)
        for a in actions:
            # Wave 1: Urgent blockers (P0) or critical security/server headers
            if a.priority == "P0" or "security header" in a.title.lower() or "hsts" in a.title.lower():
                a.wave_number = 1
            # Wave 2: Foundational fixes (P1, global templates, shared components, accessible forms)
            elif a.priority == "P1" or "label" in a.title.lower() or "contrast" in a.title.lower():
                a.wave_number = 2
            # Wave 3: Content, experience, and messaging refinements
            elif a.priority == "P2" or "copy" in a.title.lower() or "cta" in a.title.lower():
                a.wave_number = 3
            # Wave 4: Low-priority polish, micro-optimizations, and exploratory tests
            else:
                a.wave_number = 4

            # Ensure an action cannot execute in an earlier wave than its prerequisites
            for dep_id in prereqs.get(a.action_id, []):
                prereq_action = action_map.get(dep_id)
                if prereq_action and prereq_action.wave_number >= a.wave_number:
                    a.wave_number = min(4, prereq_action.wave_number + 1)

        # Sort actions by wave, then priority, then title
        priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
        actions.sort(key=lambda x: (x.wave_number, priority_rank.get(x.priority, 2), x.title))

        return actions
