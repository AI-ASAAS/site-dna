"""Cross-Agent Relationship Graph Engine for Site DNA Phase 11."""

from collections import defaultdict

from site_dna.schemas.strategic_intelligence import DuplicateFindingGroup, FindingRelationship, UnifiedFinding


class RelationshipGraphEngine:
    """Models semantic relationships between findings, detects cycles, and organizes adjacency."""

    def __init__(self):
        self.relationships: list[FindingRelationship] = []
        self._adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)

    def add_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        description: str,
        description_ar: str = "",
        confidence: float = 0.8,
        is_candidate: bool = False,
    ) -> None:
        """Add a validated relationship edge."""
        if source_id == target_id:
            # Self-references are prohibited
            return

        rel = FindingRelationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=rel_type,  # type: ignore
            description=description,
            description_ar=description_ar or None,
            confidence=confidence,
            is_candidate=is_candidate,
        )
        self.relationships.append(rel)
        self._adjacency[source_id].append((target_id, rel_type))

    def detect_dependency_cycles(self) -> list[list[str]]:
        """Detect any cycles formed by dependency or blocking edges."""
        dep_graph: dict[str, list[str]] = defaultdict(list)
        for r in self.relationships:
            if r.relationship_type in ("depends_on", "blocks"):
                dep_graph[r.source_id].append(r.target_id)

        visited: dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited
        cycles: list[list[str]] = []

        def dfs(node: str, path: list[str]):
            visited[node] = 1
            path.append(node)
            for neighbor in dep_graph[node]:
                if visited.get(neighbor, 0) == 1:
                    idx = path.index(neighbor)
                    cycles.append(path[idx:] + [neighbor])
                elif visited.get(neighbor, 0) == 0:
                    dfs(neighbor, path)
            path.pop()
            visited[node] = 2

        all_nodes = list(dep_graph.keys())
        for n in all_nodes:
            if visited.get(n, 0) == 0:
                dfs(n, [])

        return cycles

    def build_relationships_from_findings_and_groups(
        self,
        findings: list[UnifiedFinding],
        groups: list[DuplicateFindingGroup],
    ) -> list[FindingRelationship]:
        """Automatically synthesize relationships between duplicate groups and related items."""
        # 1. Duplicate relationships from duplicate groups
        for g in groups:
            canon = g.findings[0]
            for f in g.findings[1:]:
                self.add_relationship(
                    source_id=f.unified_finding_id,
                    target_id=canon.unified_finding_id,
                    rel_type="duplicate_of",
                    description=f"Duplicate issue detected across {f.source_agent} and {canon.source_agent}: {g.deduplication_reason}",
                    description_ar=f"مشكلة مكررة مرصودة بين {f.source_agent} و{canon.source_agent}: {g.deduplication_reason_ar or ''}",
                    confidence=g.confidence,
                )

        # 2. Category & page-based candidate relationships
        by_page: dict[str, list[UnifiedFinding]] = defaultdict(list)
        for f in findings:
            if f.page_url:
                by_page[f.page_url].append(f)

        for page_url, p_findings in by_page.items():
            if len(p_findings) > 1:
                # Pairwise potential shared causes if category or tags match
                for i in range(len(p_findings)):
                    for j in range(i + 1, min(i + 4, len(p_findings))):
                        fa = p_findings[i]
                        fb = p_findings[j]
                        if fa.category == fb.category and fa.source_phase != fb.source_phase:
                            self.add_relationship(
                                source_id=fa.unified_finding_id,
                                target_id=fb.unified_finding_id,
                                rel_type="related_to",
                                description=f"Related {fa.category} findings co-occurring on page {page_url}",
                                description_ar=f"مشكلات متقاربة في تصنيف {fa.category} تظهر معاً في نفس الصفحة {page_url}",
                                confidence=0.7,
                                is_candidate=True,
                            )

        return self.relationships
