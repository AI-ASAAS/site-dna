"""Unit tests for CSPAnalyzer (Phase 09)."""

from site_dna.analysis.security_privacy.csp_analyzer import CSPAnalyzer
from site_dna.schemas.security_privacy import SecurityPageRecord
from tests.fixtures.security_privacy.test_fixtures import (
    FIXTURE_A_STRONG_HEADERS,
    FIXTURE_C_WEAK_CSP_HEADERS,
)


def test_csp_analyzer_enforced_policy():
    """Verify parsing and scoring of a strong enforced CSP."""
    analyzer = CSPAnalyzer()
    p1 = SecurityPageRecord(
        page_url="https://secure.example.com/",
        scheme="https",
        status_code=200,
        headers=FIXTURE_A_STRONG_HEADERS,
    )
    res = analyzer.analyze([p1])
    assert res.is_enforced is True
    assert res.is_report_only is False
    assert res.has_default_src is True
    assert res.has_object_src is True
    assert res.has_frame_ancestors is True
    assert res.allows_unsafe_inline is False
    assert res.allows_unsafe_eval is False
    assert res.defense_in_depth_score >= 80.0


def test_csp_analyzer_report_only_and_weaknesses():
    """Verify detection of Report-Only CSP, unsafe-inline, and unsafe-eval."""
    analyzer = CSPAnalyzer()
    p1 = SecurityPageRecord(
        page_url="https://weak.example.com/",
        scheme="https",
        status_code=200,
        headers=FIXTURE_C_WEAK_CSP_HEADERS,
    )
    res = analyzer.analyze([p1])
    assert res.is_enforced is False
    assert res.is_report_only is True
    assert res.allows_unsafe_inline is True
    assert res.allows_unsafe_eval is True
    assert res.allows_broad_wildcards is True
    assert res.defense_in_depth_score < 50.0
