"""Pydantic schemas for Site DNA Phase 07 Technical SEO & Performance Intelligence."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class TechnicalSEOAnalysisRequest(BaseModel):
    """Request model for starting Technical SEO and Performance analysis."""

    crawl_run_id: str = Field(
        ...,
        description="ID of the previous crawl run from Phase 02",
    )
    visual_run_id: Optional[str] = Field(
        default=None,
        description="Optional ID of visual capture run from Phase 03",
    )
    language: str = Field(
        default="ar",
        description="Report output language code ('ar' or 'en')",
    )
    max_pages: Optional[int] = Field(
        default=8,
        ge=1,
        le=50,
        description="Maximum pages to include in the Technical SEO audit",
    )
    include_performance: bool = Field(
        default=False,
        description="Whether to run live browser performance measurements (bounded)",
    )
    include_external_metrics: bool = Field(
        default=False,
        description="Whether to query external metrics adapters (PSI/CrUX, disabled by default)",
    )
    offline_mode: bool = Field(
        default=False,
        description="Run in offline mode without making external AI model requests",
    )
    deterministic_only: bool = Field(
        default=False,
        description="Skip AI interpretation entirely and produce deterministic audit",
    )


class TechnicalPageRecord(BaseModel):
    """Normalized technical audit record for a single crawled website page."""

    page_id: str
    requested_url: str
    final_url: str
    canonical_url: Optional[str] = None
    http_status: int
    response_headers: dict[str, str] = Field(default_factory=dict)
    robots_directives: list[str] = Field(default_factory=list)
    sitemap_membership: bool = False
    title: Optional[str] = None
    meta_description: Optional[str] = None
    headings: list[dict[str, Any]] = Field(default_factory=list)
    html_lang: Optional[str] = None
    hreflang_links: list[dict[str, str]] = Field(default_factory=list)
    viewport_meta: Optional[str] = None
    structured_data: list[Any] = Field(default_factory=list)
    internal_links: list[str] = Field(default_factory=list)
    resource_metadata: dict[str, Any] = Field(default_factory=dict)
    rendered_metadata: dict[str, Any] = Field(default_factory=dict)
    source_evidence_ids: list[str] = Field(default_factory=list)
    collection_status: str = "observed"
    limitations: list[str] = Field(default_factory=list)


class CrawlabilityAssessment(BaseModel):
    """Evaluation of how easily crawlers can discover and navigate pages."""

    status: Literal["permitted", "restricted", "blocked", "unknown"] = "permitted"
    total_internal_links: int = 0
    unique_destinations: int = 0
    broken_links_count: int = 0
    crawl_depth_max: int = 0
    orphaned_pages_detected: int = 0
    evidence_ids: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)


class IndexabilityAssessment(BaseModel):
    """Evaluation of search engine indexing directives across pages."""

    status: Literal[
        "potentially_indexable", "noindex_observed", "conflicting_signals", "crawl_disallowed", "unknown"
    ] = "potentially_indexable"
    noindex_count: int = 0
    x_robots_tag_count: int = 0
    conflicting_directives_count: int = 0
    pages_with_directives: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)


class RobotsAssessment(BaseModel):
    """Robots.txt file presence, accessibility and directive evaluation."""

    is_present: bool = False
    http_status: Optional[int] = None
    crawler_allowed: bool = True
    disallowed_paths: list[str] = Field(default_factory=list)
    sitemap_references: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)


class SitemapAssessment(BaseModel):
    """XML sitemap discovery, structure and URL coverage audit."""

    sitemap_found: bool = False
    sitemap_urls: list[str] = Field(default_factory=list)
    total_entries_count: int = 0
    duplicate_urls_count: int = 0
    cross_origin_entries_count: int = 0
    crawled_urls_in_sitemap: int = 0
    uncrawled_sitemap_urls: int = 0
    evidence_ids: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)


class CanonicalAssessment(BaseModel):
    """Canonical URL consistency and conflict audit."""

    missing_canonical_count: int = 0
    self_referencing_count: int = 0
    cross_page_canonical_count: int = 0
    cross_domain_canonical_count: int = 0
    conflicting_canonicals_count: int = 0
    evidence_ids: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)


class RedirectAssessment(BaseModel):
    """HTTP redirects and status code distribution audit."""

    redirect_count: int = 0
    permanent_redirects_301: int = 0
    temporary_redirects_302: int = 0
    redirect_chains_count: int = 0
    redirect_loops_count: int = 0
    http_to_https_transition: bool = True
    evidence_ids: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)


class MetadataAssessment(BaseModel):
    """HTML titles, meta descriptions, viewport and language tags audit."""

    missing_title_count: int = 0
    missing_description_count: int = 0
    duplicate_titles_count: int = 0
    missing_viewport_count: int = 0
    missing_lang_count: int = 0
    conflicting_metadata_count: int = 0
    evidence_ids: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)


class StructuredDataAssessment(BaseModel):
    """Schema.org and JSON-LD syntax, type validity and completeness audit."""

    total_schemas_found: int = 0
    valid_json_count: int = 0
    syntax_error_count: int = 0
    schema_types: list[str] = Field(default_factory=list)
    missing_required_fields: list[dict[str, Any]] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)


class JavaScriptSEOAssessment(BaseModel):
    """Comparison between initial raw server HTML and rendered DOM."""

    status: Literal["server_html_present", "rendered_only", "consistent", "conflicting", "not_comparable"] = (
        "consistent"
    )
    title_differs: bool = False
    canonical_differs: bool = False
    robots_differs: bool = False
    headings_differ: bool = False
    content_rendered_only: bool = False
    evidence_ids: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)


class MobileSEOAssessment(BaseModel):
    """Technical mobile viewport, configuration and parity audit."""

    viewport_configured: bool = True
    mobile_content_parity: bool = True
    horizontal_overflow_detected: bool = False
    mobile_nav_accessible: bool = True
    evidence_ids: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)


class InternationalSEOAssessment(BaseModel):
    """HTML lang attributes, hreflang annotations and language tags."""

    html_lang_declared: Optional[str] = None
    hreflang_count: int = 0
    reciprocal_annotations_valid: bool = True
    x_default_present: bool = False
    bilingual_parity: Optional[str] = None
    evidence_ids: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)


class PerformanceMeasurement(BaseModel):
    """Explicitly measured performance timing or resource metric."""

    metric_name: str
    value: float
    unit: str = "ms"
    source: Literal["navigation_timing", "playwright_collector", "synthetic_lab", "not_measured"] = "navigation_timing"
    measurement_type: Literal["laboratory", "local_browser", "field"] = "local_browser"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    conditions: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(default_factory=list)


class CoreWebVitalsRecord(BaseModel):
    """Grounded Core Web Vitals observations with explicit source boundaries."""

    lcp_ms: Optional[float] = None
    inp_ms: Optional[float] = None
    cls: Optional[float] = None
    lcp_source: Literal["lab_browser", "crux_field", "psi_api", "not_measured"] = "not_measured"
    inp_source: Literal["crux_field", "synthetic_lab", "not_measured"] = "not_measured"
    cls_source: Literal["lab_browser", "crux_field", "psi_api", "not_measured"] = "not_measured"
    field_vs_lab: Literal["lab", "field", "mixed", "not_assessed"] = "not_assessed"
    assessment_status: Literal["good", "needs_improvement", "poor", "not_assessed"] = "not_assessed"
    notes: list[str] = Field(default_factory=list)


class ExternalMetricRecord(BaseModel):
    """Optional external PageSpeed Insights or CrUX response data."""

    provider: Literal["google_psi", "google_crux", "none"] = "none"
    scope: Literal["url", "origin", "not_available"] = "not_available"
    metrics: dict[str, Any] = Field(default_factory=dict)
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal["available", "disabled", "quota_exceeded", "not_configured"] = "disabled"


class TechnicalSEOFinding(BaseModel):
    """Validated technical SEO or performance observation backed by evidence."""

    finding_id: str
    title: str
    category: str
    description: str
    page_url: str
    source_excerpt: Optional[str] = None
    evidence_ids: list[str] = Field(default_factory=list)
    observation_type: Literal[
        "observed",
        "derived",
        "external_measurement",
        "heuristic",
        "ai_interpretation",
        "not_assessed",
    ] = "observed"
    severity: Literal["critical", "high", "medium", "low", "info"] = "medium"
    confidence_category: Literal["measured", "observed", "derived", "inferred"] = "observed"
    potential_technical_impact: str
    recommended_action: str


class TechnicalSEORecommendation(BaseModel):
    """Actionable technical SEO recommendation with verified fix criteria."""

    recommendation_id: str
    title: str
    related_finding_ids: list[str] = Field(default_factory=list)
    category: str
    affected_urls: list[str] = Field(default_factory=list)
    technical_problem: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    proposed_fix: str
    implementation_guidance: str
    expected_technical_benefit: str
    estimated_impact: Literal["high", "medium", "low"] = "medium"
    estimated_effort: Literal["small", "medium", "large"] = "medium"
    priority: Literal["p1", "p2", "p3"] = "p2"
    verification_method: str = "inspection"
    limitations: list[str] = Field(default_factory=list)


class TechnicalSEOScore(BaseModel):
    """Score breakdown for one of the 6 Technical SEO audit dimensions."""

    dimension_name: str
    dimension_name_ar: str
    weight: float
    score: Optional[float] = None
    status: Literal["assessed", "not_assessed", "neutral"] = "assessed"
    rationale: str
    evidence_count: int = 0


class TechnicalSEOStatistics(BaseModel):
    """Execution telemetry and data coverage metrics for Technical SEO audit."""

    pages_evaluated: int = 0
    pages_eligible: int = 0
    indexing_signals_count: int = 0
    structured_data_count: int = 0
    performance_measurements_count: int = 0
    field_metrics_available: bool = False
    lab_metrics_available: bool = False
    validated_findings_count: int = 0
    quarantined_findings_count: int = 0
    recommendations_count: int = 0
    model_calls_count: int = 0
    model_name: str = "gemini-3.6-flash"
    execution_duration_ms: float = 0.0
    ai_status: str = "completed"


class TechnicalSEOReport(BaseModel):
    """Complete structured output artifact for Phase 07 Technical SEO audit."""

    schema_version: str = "1.0"
    analysis_run_id: str
    crawl_run_id: str
    visual_run_id: Optional[str] = None
    target_origin: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    analysis_status: Literal["completed", "partial", "ai_blocked", "failed"] = "completed"
    overall_score: Optional[float] = None
    scores: list[TechnicalSEOScore] = Field(default_factory=list)
    crawlability: CrawlabilityAssessment = Field(default_factory=CrawlabilityAssessment)
    indexability: IndexabilityAssessment = Field(default_factory=IndexabilityAssessment)
    robots: RobotsAssessment = Field(default_factory=RobotsAssessment)
    sitemap: SitemapAssessment = Field(default_factory=SitemapAssessment)
    canonical: CanonicalAssessment = Field(default_factory=CanonicalAssessment)
    redirects: RedirectAssessment = Field(default_factory=RedirectAssessment)
    metadata: MetadataAssessment = Field(default_factory=MetadataAssessment)
    structured_data: StructuredDataAssessment = Field(default_factory=StructuredDataAssessment)
    javascript_seo: JavaScriptSEOAssessment = Field(default_factory=JavaScriptSEOAssessment)
    mobile_seo: MobileSEOAssessment = Field(default_factory=MobileSEOAssessment)
    international_seo: InternationalSEOAssessment = Field(default_factory=InternationalSEOAssessment)
    performance: list[PerformanceMeasurement] = Field(default_factory=list)
    core_web_vitals: CoreWebVitalsRecord = Field(default_factory=CoreWebVitalsRecord)
    external_metrics: Optional[ExternalMetricRecord] = None
    findings: list[TechnicalSEOFinding] = Field(default_factory=list)
    recommendations: list[TechnicalSEORecommendation] = Field(default_factory=list)
    statistics: TechnicalSEOStatistics = Field(default_factory=TechnicalSEOStatistics)
    report_markdown_path: Optional[str] = None
    analysis_json_path: Optional[str] = None
