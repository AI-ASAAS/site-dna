"""Pydantic schemas for Site DNA Phase 09 — Security, Privacy & Digital Trust Intelligence."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# Core Literals & Categories
ObservationType = Literal["observed", "derived", "heuristic", "ai_interpretation", "not_assessed"]
VerificationState = Literal["confirmed_configuration_issue", "potential_risk", "manual_review_required", "not_assessed"]
FindingSeverity = Literal["critical", "high", "medium", "low", "informational"]
ConfidenceCategory = Literal["observed", "measured", "inferred"]
RecommendationPriority = Literal["p1", "p2", "p3"]
RecommendationEffort = Literal["small", "medium", "large"]
RecommendationImpact = Literal["high", "medium", "low"]
TransportSecurityStatus = Literal[
    "https_observed",
    "http_only_observed",
    "redirect_to_https_observed",
    "redirect_not_verified",
    "tls_error_observed",
    "transport_not_assessed",
]


class SecurityPrivacyAnalysisRequest(BaseModel):
    """Input parameters to trigger a Security, Privacy & Trust audit."""

    crawl_run_id: str = Field(..., description="ID of completed discovery crawl run")
    visual_run_id: Optional[str] = Field(None, description="Optional ID of visual capture run")
    language: str = Field(default="ar", description="Report language ('ar' or 'en')")
    max_pages: int = Field(default=8, ge=1, le=50, description="Maximum pages to assess")
    save_results: bool = Field(default=True, description="Whether to persist results to disk")
    offline_mode: bool = Field(default=False, description="Run in offline deterministic mode without live LLM calls")
    deterministic_only: bool = Field(default=False, description="Skip AI interpretation layer entirely")


class SecurityPageRecord(BaseModel):
    """Normalized security and privacy metadata for a single collected web page."""

    page_url: str
    canonical_url: Optional[str] = None
    scheme: str
    status_code: int
    headers: dict[str, str] = Field(default_factory=dict)
    cookies: list[dict[str, Any]] = Field(default_factory=list)
    mixed_content_resources: list[str] = Field(default_factory=list)
    third_party_origins: list[str] = Field(default_factory=list)
    has_privacy_link: bool = False
    has_cookie_banner: bool = False


class HTTPSAssessment(BaseModel):
    """HTTPS transport and transition audit."""

    status: TransportSecurityStatus
    status_ar: str
    is_https: bool
    final_scheme: str
    hsts_present: bool = False
    hsts_header_value: Optional[str] = None
    hsts_preload: bool = False
    hsts_include_subdomains: bool = False
    hsts_max_age: Optional[int] = None
    http_to_https_redirect_verified: bool = False
    mixed_scheme_observed: bool = False
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    notes_ar: str = ""


class TLSObservation(BaseModel):
    """Observed TLS and certificate metadata without active probing."""

    protocol_version: Optional[str] = None
    cipher_suite: Optional[str] = None
    certificate_subject: Optional[str] = None
    certificate_issuer: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    is_expired: bool = False
    days_to_expiration: Optional[int] = None
    hostname_match: Optional[bool] = None
    trusted_chain: Optional[bool] = None
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    notes_ar: str = ""


class SecurityHeaderRecord(BaseModel):
    """Individual security header observation."""

    header_name: str
    is_present: bool
    observed_value: Optional[str] = None
    is_properly_configured: bool = False
    status_ar: str
    potential_risk: Optional[str] = None
    potential_risk_ar: Optional[str] = None
    remediation_recommendation: Optional[str] = None
    remediation_recommendation_ar: Optional[str] = None
    evidence_ids: list[str] = Field(default_factory=list)


class SecurityHeaderAssessment(BaseModel):
    """Full HTTP security headers audit."""

    total_headers_checked: int = 0
    present_headers_count: int = 0
    missing_headers_count: int = 0
    header_records: list[SecurityHeaderRecord] = Field(default_factory=list)
    has_hsts: bool = False
    has_csp: bool = False
    has_x_content_type_options: bool = False
    has_referrer_policy: bool = False
    has_permissions_policy: bool = False
    has_framing_protection: bool = False  # CSP frame-ancestors or X-Frame-Options
    overall_headers_posture: str = "needs_review"
    overall_headers_posture_ar: str = "يتطلب مراجعة"
    notes: str = ""


class CSPAssessment(BaseModel):
    """Content Security Policy directives and defense-in-depth analysis."""

    is_enforced: bool = False
    is_report_only: bool = False
    raw_policy: Optional[str] = None
    directives: dict[str, list[str]] = Field(default_factory=dict)
    has_default_src: bool = False
    has_script_src: bool = False
    has_object_src: bool = False
    has_base_uri: bool = False
    has_frame_ancestors: bool = False
    allows_unsafe_inline: bool = False
    allows_unsafe_eval: bool = False
    allows_broad_wildcards: bool = False
    defense_in_depth_score: float = 0.0
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    notes_ar: str = ""


class CookieAttributeRecord(BaseModel):
    """Cookie security attributes with STRICT REDACTION of secret values."""

    name: str
    domain: Optional[str] = None
    path: Optional[str] = None
    is_secure: bool = False
    is_http_only: bool = False
    same_site: Optional[Literal["Strict", "Lax", "None", "Unknown"]] = "Unknown"
    is_session: bool = False
    apparent_purpose: Literal["session_auth", "analytics_tracking", "functional_preferences", "unknown"] = "unknown"
    has_secure_prefix: bool = False  # __Secure- or __Host-
    expires: Optional[str] = None
    max_age: Optional[int] = None
    risk_flags: list[str] = Field(default_factory=list)
    risk_flags_ar: list[str] = Field(default_factory=list)
    # RAW VALUE IS INTENTIONALLY OMITTED AND PROHIBITED TO PREVENT SECRET EXPOSURE


class CookieSecurityAssessment(BaseModel):
    """Audit of cookies observed across inspected responses."""

    total_cookies_observed: int = 0
    secure_cookies_count: int = 0
    http_only_cookies_count: int = 0
    same_site_configured_count: int = 0
    same_site_none_insecure_count: int = 0
    apparent_session_cookies_missing_flags: int = 0
    cookie_records: list[CookieAttributeRecord] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    notes_ar: str = ""


class MixedContentRecord(BaseModel):
    """Single observed or candidate mixed-content reference."""

    page_url: str
    insecure_resource_url: str  # Safely stripped of query parameters
    resource_type: Literal["script", "stylesheet", "image", "media", "iframe", "xhr_fetch", "unknown"] = "unknown"
    disposition: Literal["observed_insecure", "upgraded_to_https", "blocked_by_browser", "potential_reference"] = (
        "observed_insecure"
    )
    evidence_ids: list[str] = Field(default_factory=list)


class MixedContentAssessment(BaseModel):
    """Mixed content evaluation for HTTPS pages."""

    has_mixed_content: bool = False
    insecure_references_count: int = 0
    blocked_references_count: int = 0
    upgraded_references_count: int = 0
    records: list[MixedContentRecord] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    notes_ar: str = ""


class BrowserIsolationAssessment(BaseModel):
    """Evaluation of browser isolation headers and context controls."""

    has_coop: bool = False
    coop_value: Optional[str] = None
    has_coep: bool = False
    coep_value: Optional[str] = None
    has_corp: bool = False
    corp_value: Optional[str] = None
    has_permissions_policy: bool = False
    permissions_policy_value: Optional[str] = None
    has_referrer_policy: bool = False
    referrer_policy_value: Optional[str] = None
    is_safe_referrer: bool = False
    framing_protection_status: Literal["protected_csp", "protected_xfo", "both", "none"] = "none"
    framing_protection_status_ar: str = "غير محمية"
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    notes_ar: str = ""


class ClientSideObservation(BaseModel):
    """Defensive client-side structure observations without vulnerability claims."""

    inline_scripts_count: int = 0
    external_scripts_count: int = 0
    scripts_with_sri_count: int = 0
    scripts_lacking_sri_count: int = 0
    frameworks_detected: list[dict[str, str]] = Field(default_factory=list)  # {"name": "react", "version": "18.2.0"}
    has_unpinned_external_scripts: bool = False
    unsafe_patterns_observed: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    notes_ar: str = ""


class ThirdPartyResourceRecord(BaseModel):
    """Observed third-party asset origin and categorization."""

    origin: str
    resource_category: Literal[
        "analytics", "advertising", "tag_manager", "fonts", "cdn_library", "customer_support", "social_media", "other"
    ] = "other"
    pages_observed: list[str] = Field(default_factory=list)
    resource_types: list[str] = Field(default_factory=list)
    requires_privacy_review: bool = False
    evidence_ids: list[str] = Field(default_factory=list)


class ThirdPartyResourceAssessment(BaseModel):
    """Third-party resource and external asset inventory."""

    total_first_party_requests: int = 0
    total_third_party_requests: int = 0
    unique_third_party_origins: int = 0
    third_party_origins_list: list[ThirdPartyResourceRecord] = Field(default_factory=list)
    has_analytics: bool = False
    has_trackers: bool = False
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    notes_ar: str = ""


class PrivacySignalAssessment(BaseModel):
    """Public privacy and data disclosures observed on the website."""

    privacy_policy_found: bool = False
    privacy_policy_url: Optional[str] = None
    cookie_policy_found: bool = False
    cookie_policy_url: Optional[str] = None
    privacy_contact_found: bool = False
    privacy_contact_method: Optional[str] = None
    data_retention_mentioned: bool = False
    third_party_sharing_mentioned: bool = False
    user_rights_mentioned: bool = False  # Access, deletion, rectification
    dpo_or_officer_mentioned: bool = False
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    notes_ar: str = ""


class ConsentObservation(BaseModel):
    """Visible consent management interface signals from DOM/visual evidence."""

    consent_banner_detected: bool = False
    has_accept_button: bool = False
    has_reject_or_customize: bool = False
    has_link_to_cookie_policy: bool = False
    banner_text_summary: Optional[str] = None
    banner_text_summary_ar: Optional[str] = None
    verification_mode: Literal["observed_in_dom", "observed_in_screenshot", "not_found_in_sample", "not_assessed"] = (
        "not_found_in_sample"
    )
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    notes_ar: str = ""


class TrustSignalAssessment(BaseModel):
    """Public digital trust and security communication signals."""

    https_indicator: bool = False
    security_contact_found: bool = False  # security.txt or security page
    security_contact_url: Optional[str] = None
    vulnerability_disclosure_policy: bool = False
    trust_seals_or_certifications_claimed: list[str] = Field(default_factory=list)
    independently_verified_certifications: list[str] = Field(default_factory=list)
    terms_of_service_found: bool = False
    terms_of_service_url: Optional[str] = None
    evidence_ids: list[str] = Field(default_factory=list)
    notes: str = ""
    notes_ar: str = ""


class SecurityFinding(BaseModel):
    """Individual defensive security finding with evidence provenance."""

    finding_id: str
    title: str
    title_ar: str
    category: Literal[
        "https_transport",
        "security_headers",
        "csp",
        "cookie_security",
        "mixed_content",
        "browser_isolation",
        "client_side",
        "third_party_privacy",
        "privacy_policy",
        "consent_interface",
        "digital_trust",
    ]
    description: str
    description_ar: str
    source_page: str
    evidence_ids: list[str] = Field(default_factory=list)
    observation_type: ObservationType = "observed"
    verification_state: VerificationState = "confirmed_configuration_issue"
    severity: FindingSeverity = "medium"
    confidence_category: ConfidenceCategory = "observed"
    potential_impact: str
    potential_impact_ar: str
    recommended_action: str
    recommended_action_ar: str
    limitations: str
    limitations_ar: str


class SecurityRecommendation(BaseModel):
    """Actionable remediation recommendation with verification method."""

    recommendation_id: str
    title: str
    title_ar: str
    related_finding_ids: list[str] = Field(default_factory=list)
    category: str
    category_ar: str
    affected_pages: list[str] = Field(default_factory=list)
    observed_issue: str
    observed_issue_ar: str
    evidence_ids: list[str] = Field(default_factory=list)
    security_or_privacy_implication: str
    security_or_privacy_implication_ar: str
    recommended_configuration_change: str
    recommended_configuration_change_ar: str
    estimated_effort: RecommendationEffort = "medium"
    estimated_impact: RecommendationImpact = "medium"
    priority: RecommendationPriority = "p2"
    verification_method: str
    verification_method_ar: str
    limitations: str
    limitations_ar: str


class SecurityScore(BaseModel):
    """Observable Security & Privacy Posture Score across 6 dimensions."""

    overall_score: Optional[float] = None  # None if insufficient evidence
    https_transport_score: Optional[float] = None  # 20%
    security_headers_score: Optional[float] = None  # 25%
    cookie_security_score: Optional[float] = None  # 15%
    client_side_resources_score: Optional[float] = None  # 15%
    privacy_consent_score: Optional[float] = None  # 15%
    digital_trust_score: Optional[float] = None  # 10%
    evidence_coverage_percentage: float = 0.0
    rubric_version: str = "phase_09_v1"
    score_label: str = "Observable Security & Privacy Posture Score"
    score_label_ar: str = "مؤشر الوضع الأمني والخصوصية المرصود"
    disclaimer: str = (
        "This score represents passive, non-intrusive observation of public web configurations. "
        "It does NOT constitute a penetration test, vulnerability assessment, or security certification."
    )
    disclaimer_ar: str = (
        "يمثل هذا التقييم رصداً خارجياً وسلبياً للإعدادات العامة دون فحص اختراق أو اختبار ثغرات نشط، "
        "ولا يعد شهادة أمنية أو ضماناً لخلو الموقع من العيوب البرمجية."
    )


class SecurityAnalysisStatistics(BaseModel):
    """Execution telemetry and metric accounting."""

    pages_assessed: int = 0
    total_headers_analyzed: int = 0
    total_cookies_analyzed: int = 0
    total_resources_analyzed: int = 0
    total_third_party_origins: int = 0
    findings_count_by_severity: dict[str, int] = Field(default_factory=dict)
    recommendations_count_by_priority: dict[str, int] = Field(default_factory=dict)
    execution_duration_ms: float = 0.0
    ai_calls_made: int = 0
    ai_status: Literal["completed", "offline_deterministic", "quota_blocked", "failed"] = "completed"
    model_identifier: str = "gemini-3.6-flash"


class SecurityAnalysisError(BaseModel):
    """Detailed error record when assessment fails or is partial."""

    error_code: str
    error_message: str
    error_message_ar: str
    occurred_at: str
    details: Optional[dict[str, Any]] = None


class SecurityPrivacyContext(BaseModel):
    """Normalized context payload for Security & Privacy analysis pipeline."""

    security_run_id: str
    source_crawl_run_id: str
    source_visual_run_id: Optional[str] = None
    site_origin: str
    target_url: str
    page_records: list[SecurityPageRecord] = Field(default_factory=list)
    raw_evidence_count: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SecurityPrivacyReport(BaseModel):
    """Complete consolidated Security, Privacy & Trust report."""

    security_run_id: str
    crawl_run_id: str
    visual_run_id: Optional[str] = None
    target_url: str
    site_origin: str
    analysis_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    analysis_status: Literal["completed", "partial", "ai_blocked", "failed"] = "completed"
    model_name: str = "gemini-3.6-flash"

    # Assessments
    https_assessment: HTTPSAssessment
    tls_observations: TLSObservation
    security_headers_assessment: SecurityHeaderAssessment
    csp_assessment: CSPAssessment
    cookie_security_assessment: CookieSecurityAssessment
    mixed_content_assessment: MixedContentAssessment
    browser_isolation_assessment: BrowserIsolationAssessment
    client_side_observation: ClientSideObservation
    third_party_resource_assessment: ThirdPartyResourceAssessment
    privacy_signal_assessment: PrivacySignalAssessment
    consent_observation: ConsentObservation
    trust_signal_assessment: TrustSignalAssessment

    # Strategic Synthesis
    scores: SecurityScore
    findings: list[SecurityFinding] = Field(default_factory=list)
    recommendations: list[SecurityRecommendation] = Field(default_factory=list)
    statistics: SecurityAnalysisStatistics
    error: Optional[SecurityAnalysisError] = None
