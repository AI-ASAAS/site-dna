"""Scoring Engine for Site DNA Phase 09 — Security, Privacy & Trust Intelligence."""

from typing import Optional

from site_dna.schemas.security_privacy import (
    BrowserIsolationAssessment,
    ClientSideObservation,
    CookieSecurityAssessment,
    CSPAssessment,
    HTTPSAssessment,
    MixedContentAssessment,
    PrivacySignalAssessment,
    SecurityHeaderAssessment,
    SecurityScore,
    TrustSignalAssessment,
)


class SecurityScoringEngine:
    """Computes transparent, evidence-weighted observable security posture scores."""

    def compute_scores(
        self,
        https_assessment: HTTPSAssessment,
        headers_assessment: SecurityHeaderAssessment,
        csp_assessment: CSPAssessment,
        cookie_assessment: CookieSecurityAssessment,
        mixed_content_assessment: MixedContentAssessment,
        browser_isolation_assessment: BrowserIsolationAssessment,
        client_side_observation: ClientSideObservation,
        privacy_signal_assessment: PrivacySignalAssessment,
        trust_signal_assessment: TrustSignalAssessment,
    ) -> SecurityScore:
        """Calculate dimension scores (0-100) and overall weighted posture score."""

        # 1. HTTPS & Transport Signals (Weight: 20%)
        transport_score = 0.0
        if https_assessment.is_https:
            transport_score += 60.0
            if https_assessment.hsts_present:
                transport_score += 30.0
                if https_assessment.hsts_preload:
                    transport_score += 10.0
                elif https_assessment.hsts_include_subdomains:
                    transport_score += 5.0
            if not https_assessment.mixed_scheme_observed:
                transport_score = min(100.0, transport_score + 5.0)
        else:
            transport_score = 0.0

        # 2. HTTP Security Headers (Weight: 25%)
        # Deduce score from present recommended headers and CSP strength
        headers_score = 0.0
        total_chk = headers_assessment.total_headers_checked or 8
        present_cnt = headers_assessment.present_headers_count
        base_header_pct = (present_cnt / total_chk) * 70.0
        csp_contrib = (csp_assessment.defense_in_depth_score / 100.0) * 30.0
        headers_score = min(100.0, max(0.0, base_header_pct + csp_contrib))

        # 3. Cookie Configuration (Weight: 15%)
        cookie_score: Optional[float] = None
        if cookie_assessment.total_cookies_observed > 0:
            tot_c = cookie_assessment.total_cookies_observed
            sec_ratio = cookie_assessment.secure_cookies_count / tot_c
            ho_ratio = cookie_assessment.http_only_cookies_count / tot_c
            ss_ratio = cookie_assessment.same_site_configured_count / tot_c

            cookie_score = (sec_ratio * 40.0) + (ho_ratio * 35.0) + (ss_ratio * 25.0)
            if cookie_assessment.same_site_none_insecure_count > 0:
                cookie_score -= 20.0
            if cookie_assessment.apparent_session_cookies_missing_flags > 0:
                cookie_score -= 15.0
            cookie_score = min(100.0, max(0.0, cookie_score))
        else:
            # If site sets no cookies, award neutral/good score (no cookie risks)
            cookie_score = 85.0

        # 4. Client-Side & Resource Observations (Weight: 15%)
        client_score = 80.0
        if mixed_content_assessment.has_mixed_content:
            client_score -= min(40.0, mixed_content_assessment.insecure_references_count * 15.0)
        if browser_isolation_assessment.framing_protection_status == "none":
            client_score -= 15.0
        if not browser_isolation_assessment.is_safe_referrer:
            client_score -= 10.0
        if client_side_observation.unsafe_patterns_observed:
            client_score -= 15.0
        client_score = min(100.0, max(0.0, client_score))

        # 5. Privacy & Consent Signals (Weight: 15%)
        privacy_score = 20.0
        if privacy_signal_assessment.privacy_policy_found:
            privacy_score += 40.0
        if privacy_signal_assessment.cookie_policy_found:
            privacy_score += 15.0
        if privacy_signal_assessment.user_rights_mentioned:
            privacy_score += 15.0
        if privacy_signal_assessment.privacy_contact_found:
            privacy_score += 10.0
        privacy_score = min(100.0, max(0.0, privacy_score))

        # 6. Digital Trust Transparency (Weight: 10%)
        trust_score = 30.0
        if trust_signal_assessment.https_indicator:
            trust_score += 30.0
        if trust_signal_assessment.terms_of_service_found:
            trust_score += 20.0
        if trust_signal_assessment.security_contact_found or trust_signal_assessment.vulnerability_disclosure_policy:
            trust_score += 20.0
        trust_score = min(100.0, max(0.0, trust_score))

        # Overall weighted calculation
        overall = (
            (transport_score * 0.20)
            + (headers_score * 0.25)
            + (cookie_score * 0.15)
            + (client_score * 0.15)
            + (privacy_score * 0.15)
            + (trust_score * 0.10)
        )
        overall = round(min(100.0, max(0.0, overall)), 1)

        return SecurityScore(
            overall_score=overall,
            https_transport_score=round(transport_score, 1),
            security_headers_score=round(headers_score, 1),
            cookie_security_score=round(cookie_score, 1),
            client_side_resources_score=round(client_score, 1),
            privacy_consent_score=round(privacy_score, 1),
            digital_trust_score=round(trust_score, 1),
            evidence_coverage_percentage=90.0,
        )
