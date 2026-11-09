"""Unit tests for SecurityHeadersAnalyzer (Phase 09)."""

from site_dna.analysis.security_privacy.security_headers import SecurityHeadersAnalyzer
from site_dna.schemas.security_privacy import SecurityPageRecord
from tests.fixtures.security_privacy.test_fixtures import (
    FIXTURE_A_STRONG_HEADERS,
    FIXTURE_B_MISSING_HEADERS,
)


def test_security_headers_analyzer_strong_configuration():
    """Verify detection of well-configured security response headers."""
    analyzer = SecurityHeadersAnalyzer()
    p1 = SecurityPageRecord(
        page_url="https://secure.example.com/",
        scheme="https",
        status_code=200,
        headers=FIXTURE_A_STRONG_HEADERS,
    )
    res = analyzer.analyze([p1])
    assert res.present_headers_count >= 6
    assert res.has_hsts is True
    assert res.has_csp is True
    assert res.has_x_content_type_options is True
    assert res.has_framing_protection is True
    assert res.overall_headers_posture == "strong"


def test_security_headers_analyzer_framing_protection_via_csp():
    """Verify that CSP frame-ancestors satisfies framing protection even if X-Frame-Options is absent."""
    analyzer = SecurityHeadersAnalyzer()
    headers_no_xfo = {
        "content-security-policy": "default-src 'self'; frame-ancestors 'self'",
        "x-content-type-options": "nosniff",
    }
    p1 = SecurityPageRecord(
        page_url="https://secure.example.com/",
        scheme="https",
        status_code=200,
        headers=headers_no_xfo,
    )
    res = analyzer.analyze([p1])
    assert res.has_framing_protection is True
    xfo_rec = next(r for r in res.header_records if r.header_name == "x-frame-options")
    assert xfo_rec.is_properly_configured is True
    assert "CSP frame-ancestors" in xfo_rec.status_ar


def test_security_headers_analyzer_missing_headers():
    """Verify handling when all security headers are absent."""
    analyzer = SecurityHeadersAnalyzer()
    p1 = SecurityPageRecord(
        page_url="https://bare.example.com/",
        scheme="http",
        status_code=200,
        headers=FIXTURE_B_MISSING_HEADERS,
    )
    res = analyzer.analyze([p1])
    assert res.present_headers_count == 0
    assert res.missing_headers_count == len(res.header_records)
    assert res.overall_headers_posture == "weak"
