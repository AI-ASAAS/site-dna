"""Unit tests for Security Scoring Engine in Site DNA Phase 09."""

from site_dna.analysis.security_privacy.scoring import SecurityScoringEngine
from site_dna.schemas.security_privacy import (
    BrowserIsolationAssessment,
    ClientSideObservation,
    CookieSecurityAssessment,
    CSPAssessment,
    HTTPSAssessment,
    MixedContentAssessment,
    PrivacySignalAssessment,
    SecurityHeaderAssessment,
    TrustSignalAssessment,
)


def test_scoring_weights_sum_to_100_and_range_check():
    """Verify that scoring dimensions are bounded [0, 100] and properly weighted."""
    engine = SecurityScoringEngine()

    https_ast = HTTPSAssessment(
        status="https_observed",
        status_ar="تم رصد اتصال آمن",
        final_scheme="https",
        is_https=True,
        hsts_present=True,
        hsts_preload=True,
        mixed_scheme_observed=False,
    )
    headers_ast = SecurityHeaderAssessment(
        total_headers_checked=8,
        present_headers_count=8,
        missing_headers_count=0,
    )
    csp_ast = CSPAssessment(
        is_enforced=True,
        defense_in_depth_score=100.0,
    )
    cookie_ast = CookieSecurityAssessment(
        total_cookies_observed=2,
        secure_cookies_count=2,
        http_only_cookies_count=2,
        same_site_configured_count=2,
    )
    mixed_ast = MixedContentAssessment(
        has_mixed_content=False,
        insecure_references_count=0,
    )
    isolation_ast = BrowserIsolationAssessment(
        framing_protection_status="protected_csp",
        is_safe_referrer=True,
    )
    client_ast = ClientSideObservation(
        unsafe_patterns_observed=[],
    )
    privacy_ast = PrivacySignalAssessment(
        privacy_policy_found=True,
        cookie_policy_found=True,
        user_rights_mentioned=True,
        privacy_contact_found=True,
    )
    trust_ast = TrustSignalAssessment(
        https_indicator=True,
        terms_of_service_found=True,
        security_contact_found=True,
    )

    score = engine.compute_scores(
        https_assessment=https_ast,
        headers_assessment=headers_ast,
        csp_assessment=csp_ast,
        cookie_assessment=cookie_ast,
        mixed_content_assessment=mixed_ast,
        browser_isolation_assessment=isolation_ast,
        client_side_observation=client_ast,
        privacy_signal_assessment=privacy_ast,
        trust_signal_assessment=trust_ast,
    )

    assert 0.0 <= score.overall_score <= 100.0
    assert 0.0 <= score.https_transport_score <= 100.0
    assert 0.0 <= score.security_headers_score <= 100.0
    assert 0.0 <= score.cookie_security_score <= 100.0
    assert 0.0 <= score.client_side_resources_score <= 100.0
    assert 0.0 <= score.privacy_consent_score <= 100.0
    assert 0.0 <= score.digital_trust_score <= 100.0
    # Perfect posture should score high (> 80)
    assert score.overall_score >= 80.0


def test_scoring_poor_posture():
    """Verify that insecure HTTP sites score poorly."""
    engine = SecurityScoringEngine()

    score = engine.compute_scores(
        https_assessment=HTTPSAssessment(
            status="http_only_observed",
            status_ar="تم رصد اتصال غير مشفر فقط",
            final_scheme="http",
            is_https=False,
        ),
        headers_assessment=SecurityHeaderAssessment(total_headers_checked=8, present_headers_count=0),
        csp_assessment=CSPAssessment(is_enforced=False, defense_in_depth_score=0.0),
        cookie_assessment=CookieSecurityAssessment(
            total_cookies_observed=3,
            secure_cookies_count=0,
            http_only_cookies_count=0,
            same_site_none_insecure_count=2,
            apparent_session_cookies_missing_flags=2,
        ),
        mixed_content_assessment=MixedContentAssessment(has_mixed_content=True, insecure_references_count=5),
        browser_isolation_assessment=BrowserIsolationAssessment(
            framing_protection_status="none", is_safe_referrer=False
        ),
        client_side_observation=ClientSideObservation(unsafe_patterns_observed=["eval()", "document.write()"]),
        privacy_signal_assessment=PrivacySignalAssessment(privacy_policy_found=False),
        trust_signal_assessment=TrustSignalAssessment(https_indicator=False),
    )

    assert score.overall_score < 40.0
    assert score.https_transport_score == 0.0
