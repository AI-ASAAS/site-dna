"""Unit tests for Phase 11 Strategic Evidence Validator."""

from site_dna.analysis.strategic_intelligence.evidence_validator import StrategicEvidenceValidator
from site_dna.schemas.strategic_intelligence import MeasurementPlan, RoadmapAction


def test_validator_rejects_financial_roi_hallucination():
    """Verify validator flags any invented dollar values or financial return rates."""
    validator = StrategicEvidenceValidator()

    bad_action = RoadmapAction(
        action_id="act-bad-1",
        title="Revenue Boost Implementation",
        description="Earn $500,000 extra revenue and 45% uplift",
        category="conversion_architecture",
        verification_method="manual test",
    )

    is_valid = validator.validate_action(bad_action, valid_finding_ids=set())
    assert is_valid is False
    assert len(validator.quarantined_claims) >= 1
    assert any("financial" in q["reason"].lower() or "roi" in q["reason"].lower() for q in validator.quarantined_claims)


def test_validator_detects_dangling_action_dependencies():
    """Verify validator flags actions referencing non-existent finding IDs."""
    validator = StrategicEvidenceValidator()

    action = RoadmapAction(
        action_id="act-real",
        title="Real Action",
        description="Action with phantom finding reference",
        category="security",
        related_finding_ids=["uf-non-existent-999"],
        verification_method="audit",
    )

    is_valid = validator.validate_action(action, valid_finding_ids={"uf-real-1", "uf-real-2"})
    assert is_valid is False
    assert len(validator.quarantined_claims) >= 1


def test_validator_detects_cycles_in_plan():
    """Verify validator flags cyclical action dependencies."""
    validator = StrategicEvidenceValidator()

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

    assert validator.validate_plan_acyclicity([a1, a2]) is False


def test_measurement_plan_null_baseline_enforcement():
    """Verify measurement plan uses None for baseline when real analytics traffic is unverified."""
    plan = MeasurementPlan(
        name="Core Web Vitals LCP",
        name_ar="زمن أكبر رسم للمحتوى (LCP)",
        purpose="Track visual loading stability",
        data_source="synthetic_lighthouse",
        measurement_method="Synthetic browser runs",
        limitations="Synthetic proxy metrics only.",
        baseline_value=None,
        baseline_status="null_baseline",
    )
    assert plan.baseline_value is None
    assert plan.baseline_status == "null_baseline"
