"""Unit tests for TechnicalSEOEvidenceValidator."""

from site_dna.analysis.technical_seo.evidence_validator import TechnicalSEOEvidenceValidator
from site_dna.schemas.technical_seo import TechnicalPageRecord, TechnicalSEOFinding


def test_evidence_validator_grounded_finding():
    """Verify that finding with grounded facts and known URL is approved."""
    pages = [
        TechnicalPageRecord(
            page_id="p1",
            requested_url="https://example.com/",
            final_url="https://example.com/",
            http_status=200,
            title="Example Title",
            headings=[{"level": 1, "text": "Example Domain"}],
        )
    ]
    finding = TechnicalSEOFinding(
        finding_id="TS-MET-001",
        title="وسم العنوان سليم",
        category="metadata",
        description="عنوان الصفحة هو Example Title",
        severity="info",
        page_url="https://example.com/",
        observation_type="observed",
        confidence_category="measured",
        potential_technical_impact="إيجابي",
        recommended_action="الحفاظ على العنوان",
        evidence_ids=["EV-001"],
    )

    validated, quarantined = TechnicalSEOEvidenceValidator.validate_findings(
        [finding], pages, {"EV-001": {"url": "https://example.com/"}}
    )

    assert len(validated) == 1
    assert len(quarantined) == 0


def test_evidence_validator_quarantines_hallucination():
    """Verify that finding claiming Google index status or non-existent URL is quarantined."""
    pages = [
        TechnicalPageRecord(
            page_id="p1",
            requested_url="https://example.com/",
            final_url="https://example.com/",
            http_status=200,
            title="Example Title",
        )
    ]
    hallucinated_finding = TechnicalSEOFinding(
        finding_id="TS-HAL-001",
        title="Google has indexed this page",
        category="indexability",
        description="The page is guaranteed to rank first because it is indexed by google.",
        severity="info",
        page_url="https://example.com/",
        observation_type="ai_interpretation",
        confidence_category="inferred",
        potential_technical_impact="Unknown",
        recommended_action="None",
    )

    validated, quarantined = TechnicalSEOEvidenceValidator.validate_findings([hallucinated_finding], pages, {})

    assert len(validated) == 0
    assert len(quarantined) == 1
    assert quarantined[0].finding_id == "TS-HAL-001"
