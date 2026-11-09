"""Unit tests for ReportIntegrityValidator (Zero-Hallucination & Evidence Grounding)."""

from site_dna.reporting.report_validator import ReportIntegrityValidator
from site_dna.schemas.final_report import FinalReportContext, ReportFindingItem


def test_validator_passes_on_grounded_context():
    """Verify clean grounded context passes validation without violations."""
    ctx = FinalReportContext(
        target_url="https://clear-saas.example.com",
        crawl_run_id="crawl-test",
        mode="comprehensive",
        executive_summary_md="The website demonstrates strong foundational design and responsive layouts.",
        executive_summary_ar="يظهر الموقع تصميماً أساسياً متيناً وتجاوباً جيداً مع مختلف الشاشات.",
        findings=[
            ReportFindingItem(
                finding_id="f-1",
                source_agent="security_privacy",
                severity="high",
                title="Missing CSP Header",
                title_ar="غياب ترويسة سياسة أمان المحتوى CSP",
                description="The site does not implement Content-Security-Policy.",
            )
        ],
    )
    validator = ReportIntegrityValidator()
    result = validator.validate(ctx)
    assert result["is_valid"] is True
    assert len(result["violations"]) == 0


def test_validator_catches_speculative_roi_claims():
    """Verify validator flags prohibited speculative ROI or business claims."""
    ctx = FinalReportContext(
        target_url="https://clear-saas.example.com",
        crawl_run_id="crawl-test",
        mode="comprehensive",
        executive_summary_md="Implementing these recommendations will increase conversion rate by 45% and guarantee 200% ROI.",
        executive_summary_ar="سيرتفع معدل التحويل بنسبة 45% ويضمن عائداً استثمارياً بنسبة 200%.",
    )
    validator = ReportIntegrityValidator()
    result = validator.validate(ctx)
    assert result["is_valid"] is False
    assert any("ROI" in v or "conversion rate" in v or "عائد" in v for v in result["violations"])


def test_validator_catches_ungrounded_compliance_certification():
    """Verify validator flags fraudulent claims of legal/regulatory certification."""
    ctx = FinalReportContext(
        target_url="https://clear-saas.example.com",
        crawl_run_id="crawl-test",
        mode="comprehensive",
        executive_summary_md="The site is 100% legally compliant with GDPR, HIPAA, and WCAG certified.",
        executive_summary_ar="الموقع حاصل على شهادة رسمية بالامتثال القانوني الكامل لنظام حماية البيانات.",
    )
    validator = ReportIntegrityValidator()
    result = validator.validate(ctx)
    assert result["is_valid"] is False
    assert any("certified" in v.lower() or "شهادة" in v for v in result["violations"])
