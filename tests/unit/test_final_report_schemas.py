"""Unit tests for Phase 12 Final Reporting schemas and models."""

import pytest
from pydantic import ValidationError

from site_dna.schemas.final_report import (
    FinalReportMetadata,
    FinalReportRequest,
    ReportEvidenceItem,
    ReportFindingItem,
    ReportProvenance,
    ReportRecommendationItem,
    ReportRoadmapWaveItem,
)


def test_final_report_request_validation():
    """Verify FinalReportRequest accepts crawl_run_id and analysis_run_id aliases."""
    req1 = FinalReportRequest(crawl_run_id="run-123", mode="comprehensive", language="ar")
    assert req1.crawl_run_id == "run-123"
    assert req1.mode == "comprehensive"
    assert req1.paper_size == "A4"

    req2 = FinalReportRequest(analysis_run_id="run-456", mode="executive")
    assert req2.crawl_run_id == "run-456"

    with pytest.raises(ValidationError):
        FinalReportRequest(mode="comprehensive")


def test_final_report_metadata_properties():
    """Verify FinalReportMetadata properties and defaults."""
    meta = FinalReportMetadata(
        target_url="https://example.com",
        crawl_run_id="crawl-test",
        mode="comprehensive",
        status="completed",
        overall_score=75.5,
        page_count=6,
        pdf_size_bytes=102400,
        sha256_checksum="a" * 64,
        total_findings_count=15,
        total_actions_count=8,
        pdf_path="runs/crawl-test/reports/final/rep-1/report.pdf",
    )
    assert meta.analysis_run_id == "crawl-test"
    assert meta.total_findings == 15
    assert meta.total_recommendations == 8
    assert meta.validation_passed is True
    assert meta.artifacts.pdf == "runs/crawl-test/reports/final/rep-1/report.pdf"


def test_provenance_and_evidence_item_schemas():
    """Verify ReportProvenance and ReportEvidenceItem schema serialization."""
    prov = ReportProvenance(
        stage_id="security_privacy",
        agent_id="phase_09_security",
        source_run_id="sec-001",
        artifact_path="analysis/security/analysis.json",
        artifact_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    )
    assert prov.stage_id == "security_privacy"
    assert prov.agent_id == "phase_09_security"

    ev = ReportEvidenceItem(
        evidence_id="ev-01",
        stage_id="technical_seo",
        source_agent="technical_seo",
        source_file="analysis.json",
        observation_type="core_web_vitals",
        target_url="https://example.com",
        details={"lcp": 2400, "cls": 0.05},
    )
    assert ev.evidence_id == "ev-01"
    assert ev.details["lcp"] == 2400


def test_report_finding_and_recommendation_schemas():
    """Verify finding, recommendation, and wave item schemas."""
    finding = ReportFindingItem(
        finding_id="find-01",
        title="Missing Image Alt Attributes",
        title_ar="غياب النصوص البديلة للصور",
        description="Found 5 images without alt attributes.",
        description_ar="تم العثور على 5 صور تفتقر للنص البديل.",
        domain="accessibility",
        severity="critical",
        source_agent="accessibility",
    )
    assert finding.severity == "critical"

    rec = ReportRecommendationItem(
        action_id="act-01",
        title="Implement CSP Header",
        title_ar="تفعيل ترويسة سياسة أمان المحتوى CSP",
        description="Add Content-Security-Policy header to HTTP responses.",
        priority="P0",
        effort="medium",
        owner_role="Security Engineer",
    )
    assert rec.priority == "P0"

    wave = ReportRoadmapWaveItem(
        wave_number=1,
        name="Critical Remediation",
        name_ar="الموجة 1: المعالجة الحرجة للأمان والوصول",
        timeframe="Weeks 1-2",
        description="Immediate p0 actions",
        actions=[rec],
    )
    assert wave.wave_number == 1
    assert len(wave.actions) == 1
