"""Unit tests for Phase 11 Prioritization and Roadmap Sequencing."""

from site_dna.analysis.strategic_intelligence.dependency_planner import DependencyPlanner
from site_dna.analysis.strategic_intelligence.prioritization import StrategicPrioritizer
from site_dna.analysis.strategic_intelligence.roadmap_builder import RoadmapBuilder
from site_dna.schemas.strategic_intelligence import RoadmapAction, UnifiedFinding


def test_five_dimension_prioritization_scoring():
    """Verify that prioritization computes a deterministic 0-100 score across 5 weighted dimensions."""
    prioritizer = StrategicPrioritizer()

    f_crit = UnifiedFinding(
        unified_finding_id="uf-sec-1",
        source_phase="security_privacy",
        source_agent="Security Analyst",
        source_finding_id="sec-1",
        source_run_id="run-1",
        primary_site_id="https://example.com",
        category="vulnerability",
        title="Active XSS vulnerability in query parameter",
        description="Reflected input without escaping",
        original_severity="critical",
        normalized_impact_category="critical_blocker",
        page_url="https://example.com/search",
    )

    assessment = prioritizer.assess_finding_priority(f_crit, total_site_pages=1)
    assert assessment.priority_level in ("P0", "P1")
    assert 0 <= assessment.composite_score <= 100
    assert assessment.dimension_scores["impact"] >= 80


def test_dependency_dag_cycle_breaking():
    """Verify that circular action dependencies are safely detected and broken."""
    planner = DependencyPlanner()

    a1 = RoadmapAction(
        action_id="act-1",
        title="Action 1",
        description="First action",
        category="core",
        dependencies=["act-2"],
        verification_method="manual",
    )
    a2 = RoadmapAction(
        action_id="act-2",
        title="Action 2",
        description="Second action",
        category="core",
        dependencies=["act-1"],
        verification_method="manual",
    )

    # Dependency planner should gracefully resolve waves without infinite recursion or hanging
    sequenced = planner.resolve_dependencies_and_waves([a1, a2])
    assert len(sequenced) == 2


def test_roadmap_builder_generates_four_waves():
    """Verify that roadmap builder produces exactly waves 1 through 4."""
    builder = RoadmapBuilder()

    actions = [
        RoadmapAction(
            action_id=f"act-{i}",
            title=f"Action {i}",
            description=f"Description {i}",
            category="core",
            priority="P0" if i == 0 else "P2",
            wave_number=1 if i == 0 else 2,
            verification_method="automated test",
        )
        for i in range(5)
    ]

    waves = builder.build_waves(actions)
    assert len(waves) == 4
    wave_nums = [w.wave_number for w in waves]
    assert wave_nums == [1, 2, 3, 4]
