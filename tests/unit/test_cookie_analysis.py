"""Unit tests for CookieSecurityAnalyzer (Phase 09)."""

from site_dna.analysis.security_privacy.cookie_analyzer import CookieSecurityAnalyzer
from site_dna.schemas.security_privacy import SecurityPageRecord
from tests.fixtures.security_privacy.test_fixtures import (
    FIXTURE_A_COOKIES,
    FIXTURE_D_VULN_COOKIES,
)


def test_cookie_analyzer_safe_cookies():
    """Verify safe cookie attributes evaluation."""
    analyzer = CookieSecurityAnalyzer()
    p1 = SecurityPageRecord(
        page_url="https://secure.example.com/",
        scheme="https",
        status_code=200,
        cookies=FIXTURE_A_COOKIES,
    )
    res = analyzer.analyze([p1])
    assert res.total_cookies_observed == 2
    assert res.secure_cookies_count == 2
    assert res.same_site_configured_count == 2
    assert res.same_site_none_insecure_count == 0
    assert res.apparent_session_cookies_missing_flags == 0


def test_cookie_analyzer_vulnerable_cookies():
    """Verify detection of SameSite=None without Secure and session cookies missing HttpOnly."""
    analyzer = CookieSecurityAnalyzer()
    p1 = SecurityPageRecord(
        page_url="https://vulnerable.example.com/",
        scheme="https",
        status_code=200,
        cookies=FIXTURE_D_VULN_COOKIES,
    )
    res = analyzer.analyze([p1])
    assert res.total_cookies_observed == 2
    assert res.secure_cookies_count == 0
    assert res.same_site_none_insecure_count == 2
    assert res.apparent_session_cookies_missing_flags >= 1

    # Check risk flags generated on the session cookie
    sess_rec = next(r for r in res.cookie_records if r.name == "session_id")
    assert any("Secure" in f for f in sess_rec.risk_flags)
    assert any("HttpOnly" in f for f in sess_rec.risk_flags)
