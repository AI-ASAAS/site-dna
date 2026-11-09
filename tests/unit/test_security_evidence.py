"""Unit tests for Security Evidence Validator in Site DNA Phase 09."""

from site_dna.analysis.security_privacy.evidence_validator import SecurityEvidenceValidator
from site_dna.schemas.security_privacy import SecurityFinding


def test_quarantine_prohibited_vulnerability_claims():
    """Verify that ungrounded exploit and compliance claims are quarantined."""
    validator = SecurityEvidenceValidator()

    findings = [
        SecurityFinding(
            finding_id="find-01",
            category="https_transport",
            severity="medium",
            title="HSTS Missing",
            title_ar="غياب ترويسة HSTS",
            description="Strict-Transport-Security header was not found.",
            description_ar="لم يتم العثور على ترويسة Strict-Transport-Security.",
            source_page="https://example.com/",
            evidence_ids=["ev-hsts-01"],
            confidence_category="observed",
            verification_state="confirmed_configuration_issue",
            potential_impact="Downgrade attack risk",
            potential_impact_ar="مخاطر خفض مستوى التشفير",
            recommended_action="Deploy HSTS header with max-age 31536000.",
            recommended_action_ar="تفعيل ترويسة HSTS مع مدة لا تقل عن سنة.",
            limitations="Passive network observation only.",
            limitations_ar="ملاحظة سلبية للشبكة فقط دون اختراق.",
        ),
        SecurityFinding(
            finding_id="find-02",
            category="client_side",
            severity="critical",
            title="SQL Injection Detected",
            title_ar="حقن SQL مرصود",
            description="SQL injection detected in form inputs. Passwords can be stolen.",
            description_ar="تم رصد حقن SQL ويمكن سرقة كلمات المرور.",
            source_page="https://example.com/",
            evidence_ids=["ev-bad"],
            confidence_category="inferred",
            verification_state="potential_risk",
            potential_impact="Database compromised",
            potential_impact_ar="اختراق قاعدة البيانات",
            recommended_action="Fix SQLi.",
            recommended_action_ar="معالجة الحقن.",
            limitations="Passive analysis only.",
            limitations_ar="فحص سلبي فقط.",
        ),
        SecurityFinding(
            finding_id="find-03",
            category="privacy_policy",
            severity="high",
            title="GDPR Violation",
            title_ar="مخالفة نظام GDPR",
            description="The website definitely violates GDPR regulations.",
            description_ar="الموقع ينتهك لوائح حماية البيانات قطعا.",
            source_page="https://example.com/",
            evidence_ids=["ev-gdpr"],
            confidence_category="inferred",
            verification_state="confirmed_configuration_issue",
            potential_impact="Fines",
            potential_impact_ar="غرامات",
            recommended_action="Fix compliance.",
            recommended_action_ar="معالجة الامتثال.",
            limitations="Passive analysis only.",
            limitations_ar="فحص سلبي فقط.",
        ),
    ]

    validated, quarantined = validator.validate_findings(findings, known_evidence_ids={"ev-hsts-01"})

    assert len(validated) == 1
    assert validated[0].finding_id == "find-01"
    assert len(quarantined) == 2
    quarantined_ids = [q["finding_id"] for q in quarantined]
    assert "find-02" in quarantined_ids
    assert "find-03" in quarantined_ids


def test_quarantine_sensitive_token_leakage():
    """Verify that findings containing unredacted auth tokens or cookie values are quarantined."""
    validator = SecurityEvidenceValidator()

    leak_finding = SecurityFinding(
        finding_id="find-leak",
        category="cookie_security",
        severity="high",
        title="Session Token Found",
        title_ar="رمز جلسة مكشوف",
        description="Observed authorization Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0 in response.",
        description_ar="تم رصد رمز جلسة غير معقم.",
        source_page="https://example.com/",
        evidence_ids=["ev-leak"],
        confidence_category="observed",
        verification_state="confirmed_configuration_issue",
        potential_impact="Session hijacking",
        potential_impact_ar="اختطاف الجلسة",
        recommended_action="Sanitize bearer token.",
        recommended_action_ar="تعقيم الرمز.",
        limitations="Passive observation only.",
        limitations_ar="فحص سلبي فقط.",
    )

    validated, quarantined = validator.validate_findings([leak_finding], known_evidence_ids={"ev-leak"})
    assert len(validated) == 0
    assert len(quarantined) == 1
    assert "token" in quarantined[0]["reason"].lower()
