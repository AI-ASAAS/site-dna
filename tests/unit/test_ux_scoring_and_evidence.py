"""Unit tests for UXScoringEngine, UXEvidenceValidator, and UXRecommendationEngine."""

from site_dna.analysis.ux_ui.evidence_validator import UXEvidenceValidator
from site_dna.analysis.ux_ui.recommendations import UXRecommendationEngine
from site_dna.analysis.ux_ui.scoring import UXScoringEngine
from site_dna.schemas.ux_ui import UXFinding
from site_dna.schemas.visual import VisualEvidenceRecord


def test_ux_scoring_engine_weights_and_neutral_forms():
    """Verify explainable score calculations and neutral handling of zero-form sites."""
    findings = [
        UXFinding(
            finding_id="F1",
            title="فائض أفقي على شاشات الجوال",
            category="responsive",
            severity="critical",
            confidence="confirmed_measurement",
            finding_type="deterministic_rule",
            source_page="https://example.com/",
            viewport="mobile",
            description="محتوى عريض",
            suggested_action="إصلاح الـ CSS",
            is_validated=True,
        )
    ]

    # Site with zero forms
    score_no_forms, explanations_no_forms = UXScoringEngine.calculate_scores(
        findings=findings,
        has_forms=False,
        pages_count=1,
    )
    assert score_no_forms is not None
    assert 0.0 <= score_no_forms <= 100.0

    forms_exp = next(e for e in explanations_no_forms if e.dimension_name == "Forms & Task Support")
    assert forms_exp.status == "not_assessed"
    assert forms_exp.score is None


def test_ux_evidence_validator_quarantine():
    """Verify that unverified claims or fake page URLs are quarantined."""
    evidence_index = {
        "EV-01": VisualEvidenceRecord(
            evidence_id="EV-01",
            crawl_run_id="crawl-1",
            visual_run_id="vis-1",
            evidence_category="dom_element",
            confidence_category="observed",
            field_reference="dom",
            observed_value="button element",
            collection_method="dom_inspection",
            page_url="https://valid.com/",
            viewport_profile="desktop",
        )
    }
    valid_pages = {"https://valid.com/"}
    validator = UXEvidenceValidator(evidence_index=evidence_index, valid_page_urls=valid_pages)

    good_finding = UXFinding(
        finding_id="F-OK",
        title="Valid Finding",
        category="interaction",
        severity="medium",
        confidence="confirmed_measurement",
        finding_type="deterministic_rule",
        source_page="https://valid.com/",
        viewport="desktop",
        description="Valid description",
        suggested_action="Fix",
        evidence_ids=["EV-01"],
    )
    bad_page_finding = UXFinding(
        finding_id="F-BAD-URL",
        title="Hallucinated Page Finding",
        category="interaction",
        severity="high",
        confidence="confirmed_measurement",
        finding_type="deterministic_rule",
        source_page="https://fake-site.com/ghost",
        viewport="desktop",
        description="Fake",
        suggested_action="Fix",
    )
    bad_ev_finding = UXFinding(
        finding_id="F-BAD-EV",
        title="Hallucinated Evidence ID Finding",
        category="interaction",
        severity="high",
        confidence="high_confidence_ai",
        finding_type="ai_interpretation",
        source_page="https://valid.com/",
        viewport="desktop",
        description="Fake",
        suggested_action="Fix",
        evidence_ids=["EV-GHOST-999"],
    )

    summary = validator.validate_findings([good_finding, bad_page_finding, bad_ev_finding])
    assert len(summary.validated_findings) == 1
    assert summary.validated_findings[0].finding_id == "F-OK"
    assert len(summary.rejected_findings) == 2
    assert "F-BAD-URL" in summary.quarantine_reasons
    assert "F-BAD-EV" in summary.quarantine_reasons


def test_ux_recommendation_engine_prioritization():
    """Verify priority mapping (critical/high -> P1, medium -> P2, low -> P3)."""
    findings = [
        UXFinding(
            finding_id="F-MED",
            title="ملاحظة متوسطة الأثر",
            category="interaction",
            severity="medium",
            confidence="confirmed_measurement",
            finding_type="deterministic_rule",
            source_page="https://example.com/",
            viewport="desktop",
            description="Desc",
            suggested_action="Action",
            is_validated=True,
        ),
        UXFinding(
            finding_id="F-CRIT",
            title="مشكلة حرجة في التجاوب",
            category="responsive",
            severity="critical",
            confidence="confirmed_measurement",
            finding_type="deterministic_rule",
            source_page="https://example.com/",
            viewport="mobile",
            description="Desc",
            suggested_action="Action",
            is_validated=True,
        ),
    ]

    recs = UXRecommendationEngine.generate_recommendations(findings=findings)
    assert len(recs) == 2
    assert recs[0].priority == "P1"
    assert recs[0].related_finding_ids == ["F-CRIT"]
    assert recs[1].priority == "P2"
    assert recs[1].related_finding_ids == ["F-MED"]
