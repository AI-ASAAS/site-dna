"""Unit tests for Browser Isolation Analyzer in Site DNA Phase 09."""

from site_dna.analysis.security_privacy.browser_isolation import BrowserIsolationAnalyzer
from site_dna.schemas.security_privacy import SecurityPageRecord


def test_browser_isolation_robust_configuration():
    """Verify isolation detection when COOP, COEP, CORP, and Permissions-Policy are present."""
    analyzer = BrowserIsolationAnalyzer()

    headers = {
        "cross-origin-opener-policy": "same-origin",
        "cross-origin-embedder-policy": "require-corp",
        "cross-origin-resource-policy": "same-site",
        "permissions-policy": "camera=(), microphone=(), geolocation=()",
        "referrer-policy": "strict-origin-when-cross-origin",
        "content-security-policy": "frame-ancestors 'none'",
    }

    page = SecurityPageRecord(
        page_url="https://secure.example.com/",
        scheme="https",
        status_code=200,
        headers=headers,
    )

    assessment = analyzer.analyze([page])

    assert assessment.has_coop is True
    assert assessment.coop_value == "same-origin"
    assert assessment.has_coep is True
    assert assessment.has_corp is True
    assert assessment.has_permissions_policy is True
    assert assessment.has_referrer_policy is True
    assert assessment.is_safe_referrer is True
    assert assessment.framing_protection_status == "protected_csp"


def test_browser_isolation_missing_headers():
    """Verify isolation audit on pages lacking modern isolation headers."""
    analyzer = BrowserIsolationAnalyzer()

    page = SecurityPageRecord(
        page_url="https://basic.example.com/",
        scheme="https",
        status_code=200,
        headers={"content-type": "text/html"},
    )

    assessment = analyzer.analyze([page])

    assert assessment.has_coop is False
    assert assessment.has_coep is False
    assert assessment.has_corp is False
    assert assessment.framing_protection_status == "none"
