"""Unit tests for WCAG Criteria Mapping, 6-Dimension Scoring, and Evidence Validation."""

from site_dna.analysis.accessibility.evidence_validator import AccessibilityEvidenceValidator
from site_dna.analysis.accessibility.manual_review import ManualReviewGenerator
from site_dna.analysis.accessibility.scoring import AccessibilityScoringEngine
from site_dna.analysis.accessibility.wcag_criteria import WCAGCriteriaMapper
from site_dna.schemas.accessibility import (
    AccessibilityFinding,
    ContrastAssessment,
    FormAccessibilityAssessment,
    ImagesMediaAssessment,
    KeyboardFocusAssessment,
    LanguageDirectionAssessment,
    SemanticAssessment,
)


def test_wcag_criteria_mapper():
    mapper = WCAGCriteriaMapper()
    semantics = SemanticAssessment()
    keyboard = KeyboardFocusAssessment()
    contrast = ContrastAssessment()
    forms = FormAccessibilityAssessment()
    lang_dir = LanguageDirectionAssessment()
    media = ImagesMediaAssessment()

    criteria = mapper.map_criteria(
        semantics=semantics,
        keyboard=keyboard,
        contrast=contrast,
        forms=forms,
        language=lang_dir,
        images_media=media,
    )
    assert len(criteria) >= 20

    # Ensure Level A and AA are both present
    levels = {c.conformance_level for c in criteria}
    assert "A" in levels
    assert "AA" in levels


def test_scoring_engine_dimension_weights():
    engine = AccessibilityScoringEngine()
    # Check weights configuration
    assert abs(sum(engine.DIMENSION_WEIGHTS.values()) - 1.0) < 0.0001
    assert engine.DIMENSION_WEIGHTS["semantics_names"] == 0.20
    assert engine.DIMENSION_WEIGHTS["keyboard_focus"] == 0.20
    assert engine.DIMENSION_WEIGHTS["visual_contrast"] == 0.20
    assert engine.DIMENSION_WEIGHTS["forms_interaction"] == 0.15
    assert engine.DIMENSION_WEIGHTS["navigation_structure"] == 0.15
    assert engine.DIMENSION_WEIGHTS["language_media"] == 0.10


def test_manual_review_generator():
    generator = ManualReviewGenerator()
    tasks = generator.generate_tasks(
        has_complex_images=True,
        has_interactive_widgets=True,
        has_auth_forms=True,
    )
    assert len(tasks) >= 3
    # Check that manual review questions and Arabic guidance are populated
    for t in tasks:
        assert t.review_question_ar != ""
        assert t.why_automation_is_insufficient_ar != ""
        assert len(t.manual_steps_ar) > 0


def test_evidence_validator():
    validator = AccessibilityEvidenceValidator()
    known_ids = {"ev-001", "ev-002", "ev-003"}

    valid_finding = AccessibilityFinding(
        finding_id="f-01",
        title="Missing main",
        title_ar="غياب وسم main",
        description="No main element",
        description_ar="لا يوجد وسم main",
        user_impact_ar="صعوبة وصول",
        recommended_fix_ar="إضافة main",
        severity="high",
        confidence=0.9,
        assessment_state="confirmed_failure",
        wcag_criteria=["1.3.1"],
        evidence_ids=["ev-001", "ev-002"],
    )

    # Valid finding passes
    assert validator.validate_finding(valid_finding, known_ids) is True

    # Hallucinated evidence ID fails
    invalid_finding = valid_finding.model_copy(update={"evidence_ids": ["ev-999-hallucinated"]})
    assert validator.validate_finding(invalid_finding, known_ids) is False
