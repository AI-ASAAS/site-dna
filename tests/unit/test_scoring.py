"""Unit tests for ScoringEngine (rubric weights, deductions, single-page redistribution)."""

from site_dna.analysis.visual_identity.scoring import (
    DIMENSIONS,
    SEVERITY_DEDUCTIONS,
    ScoringEngine,
)
from site_dna.schemas.visual_identity import VisualFinding


def test_scoring_weights_sum():
    """Verify that all configured visual dimension weights sum to exactly 1.0."""
    total_weight = sum(dim["weight"] for dim in DIMENSIONS.values())
    assert abs(total_weight - 1.0) < 0.0001


def test_scoring_severity_deductions_values():
    """Verify severity deduction scale adheres strictly to the Phase 04 rubric."""
    assert SEVERITY_DEDUCTIONS["critical"] == 20.0
    assert SEVERITY_DEDUCTIONS["high"] == 12.0
    assert SEVERITY_DEDUCTIONS["medium"] == 6.0
    assert SEVERITY_DEDUCTIONS["low"] == 3.0


def test_scoring_flawless_multipage():
    """Verify that a site with zero findings receives a perfect 100.0 score."""
    overall, explanations = ScoringEngine.calculate_scores(findings=[], is_multipage=True)
    assert overall == 100.0
    assert len(explanations) == 5
    assert all(e.score == 100.0 for e in explanations)
    assert all(e.status == "assessed" for e in explanations)


def test_scoring_single_page_redistribution():
    """Verify single-page sites set cross-page consistency to not_assessed and reweight."""
    overall, explanations = ScoringEngine.calculate_scores(findings=[], is_multipage=False)
    assert overall == 100.0
    cross_page_exp = next(e for e in explanations if e.dimension_name == "Cross-Page & Component Consistency")
    assert cross_page_exp.status == "not_assessed"
    assert cross_page_exp.score is None


def test_scoring_deductions_and_unvalidated():
    """Verify deductions are applied per severity, and unvalidated findings are excluded."""
    findings = [
        VisualFinding(
            finding_id="F1",
            title="High contrast issue",
            category="contrast",
            severity="high",  # -12
            confidence="confirmed_by_measurement",
            finding_type="derived_calculation",
            page_url="https://test.com",
            description="Low contrast description",
            is_validated=True,
        ),
        VisualFinding(
            finding_id="F2",
            title="Medium color issue",
            category="color",
            severity="medium",  # -6
            confidence="confirmed_by_measurement",
            finding_type="derived_calculation",
            page_url="https://test.com",
            description="Medium color description",
            is_validated=True,
        ),
        VisualFinding(
            finding_id="F3",
            title="Unvalidated hallucination",
            category="color",
            severity="critical",  # Should be ignored because is_validated=False
            confidence="hypothesized",
            finding_type="derived_calculation",
            page_url="https://test.com",
            description="Hallucination description",
            is_validated=False,
        ),
    ]

    overall, explanations = ScoringEngine.calculate_scores(findings=findings, is_multipage=True)
    color_dim = next(e for e in explanations if e.dimension_name == "Color System & Harmony")
    # Color dim: 100 - (12 + 6) = 82.0
    assert color_dim.score == 82.0
    assert "F1" in color_dim.supporting_finding_ids
    assert "F2" in color_dim.supporting_finding_ids
    assert "F3" not in color_dim.supporting_finding_ids
