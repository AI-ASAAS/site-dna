"""Pydantic schemas and data contracts for Site DNA Phase 08 — Competitor Intelligence."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

FindingSeverity = Literal["critical", "high", "medium", "low"]
ObservationType = Literal[
    "observed",
    "derived",
    "external_measurement",
    "ai_interpretation",
    "heuristic",
    "not_assessed",
]
ConfidenceCategory = Literal["observed", "measured", "inferred"]
RecommendationPriority = Literal["p1", "p2", "p3"]
RecommendationEffort = Literal["small", "medium", "large"]
RecommendationImpact = Literal["high", "medium", "low"]
RelevanceCategory = Literal["direct", "indirect", "adjacent", "not_comparable", "unknown"]
ComparisonFeatureStatus = Literal[
    "observed_present",
    "observed_absent_in_inspected_scope",
    "claimed",
    "not_found_in_sample",
    "not_assessed",
    "not_comparable",
]
AnalysisExecutionStatus = Literal["completed", "partial", "ai_blocked", "failed", "cancelled"]


class CompetitorAnalysisRequest(BaseModel):
    """Input request for multi-site competitor benchmarking."""

    primary_run_id: Optional[str] = Field(default=None, description="Existing primary website analysis run ID")
    primary_url: Optional[str] = Field(default=None, description="Primary website URL if run_id not provided")
    competitor_urls: list[str] = Field(
        default_factory=list,
        description="List of 1 to 5 competitor website URLs to benchmark against",
    )
    competitor_run_ids: Optional[list[str]] = Field(
        default=None,
        description="Optional list of existing run IDs for competitors",
    )
    language: str = Field(default="ar", description="Preferred report language ('ar' or 'en')")
    max_pages_per_site: int = Field(default=5, ge=1, le=10, description="Crawl budget per website")
    comparison_objectives: Optional[list[str]] = Field(
        default=None,
        description="Optional focal objectives (e.g. ['pricing', 'positioning', 'ux'])",
    )
    market_context: Optional[str] = Field(default=None, description="Optional market or industry focus")
    product_focus: Optional[str] = Field(default=None, description="Optional specific product/service focus")
    save_results: bool = Field(default=True, description="Whether to persist results on disk")
    offline_mode: bool = Field(default=False, description="Run in offline mode without AI requests")
    deterministic_only: bool = Field(default=False, description="Skip AI strategic interpretation")


class CompetitorSourceRecord(BaseModel):
    """Metadata regarding a website source participating in the benchmark."""

    site_id: str = Field(description="Unique identifier in comparison (e.g. 'primary', 'comp_1')")
    url: str = Field(description="Original website URL")
    canonical_origin: str = Field(description="Normalized scheme and host origin")
    display_name: str = Field(description="Human-friendly site title or brand name")
    is_primary: bool = Field(default=False, description="True if this is the primary site being audited")
    crawl_run_id: Optional[str] = Field(default=None, description="Crawl run identifier")
    visual_run_id: Optional[str] = Field(default=None, description="Visual capture run identifier")
    collection_status: Literal["success", "partial", "failed", "cached", "not_attempted"] = "not_attempted"
    pages_collected: int = Field(default=0, ge=0)
    capture_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error_message: Optional[str] = None


class CompetitorRelevance(BaseModel):
    """Relevance and comparability evaluation for a competitor."""

    site_id: str
    url: str
    relevance_category: RelevanceCategory = "unknown"
    relevance_score: float = Field(default=50.0, ge=0.0, le=100.0)
    reason: str
    reason_ar: str
    observed_categories: list[str] = Field(default_factory=list)
    declared_audience: Optional[str] = None
    declared_geography: Optional[str] = None
    user_retained_exploratory: bool = False


class CompetitorProfile(BaseModel):
    """Public business and offering profile extracted from website evidence."""

    site_id: str
    website_url: str
    display_name: str
    business_description: str
    business_description_ar: str
    offering_categories: list[str] = Field(default_factory=list)
    declared_audience: Optional[str] = None
    declared_geographic_scope: Optional[str] = None
    business_model_candidates: list[str] = Field(default_factory=list)
    published_value_proposition: Optional[str] = None
    public_contact_channels: list[str] = Field(default_factory=list)
    observed_trust_signals: list[str] = Field(default_factory=list)
    published_pricing_available: bool = False
    source_evidence_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class OfferingRecord(BaseModel):
    """Individual product, service or solution capability record."""

    offering_id: str
    site_id: str
    name: str
    category: str
    description: str
    claimed_benefits: list[str] = Field(default_factory=list)
    source_url: str
    evidence_id: str


class FeatureComparisonRecord(BaseModel):
    """Comparative row in feature / capability matrix across sites."""

    feature_id: str
    feature_name: str
    feature_name_ar: str
    category: str
    primary_status: ComparisonFeatureStatus = "not_assessed"
    primary_evidence_id: Optional[str] = None
    primary_explanation: Optional[str] = None
    competitor_statuses: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Map of site_id -> {status, evidence_id, explanation, last_observed}",
    )
    importance: Literal["core", "secondary", "niche"] = "core"


class PricingRecord(BaseModel):
    """Published pricing plan and comparability observation."""

    plan_id: str
    site_id: str
    plan_name: str
    amount: Optional[float] = None
    currency: Optional[str] = None
    billing_interval: Optional[str] = None  # monthly, annual, custom, contact_sales
    unit_basis: Optional[str] = None  # per_user, flat, usage_based, unknown
    usage_limits: list[str] = Field(default_factory=list)
    is_contact_sales: bool = False
    comparability_status: Literal["comparable", "not_comparable", "contact_sales", "not_published"] = "not_published"
    source_url: str = ""
    observation_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    notes: str = ""


class PositioningAssessment(BaseModel):
    """Public positioning and brand promise analysis."""

    site_id: str
    core_value_proposition: str
    claimed_differentiators: list[str] = Field(default_factory=list)
    target_customer_language: list[str] = Field(default_factory=list)
    primary_benefits: list[str] = Field(default_factory=list)
    brand_tone: str
    main_cta_strategy: str
    evidence_ids: list[str] = Field(default_factory=list)


class MessagingBenchmark(BaseModel):
    """Benchmarking of key messaging components across websites."""

    dimension: str
    dimension_ar: str
    primary_observation: str
    competitor_observations: dict[str, str] = Field(default_factory=dict)
    key_difference: str
    key_difference_ar: str


class VisualBenchmark(BaseModel):
    """Visual design and brand presentation comparison."""

    dimension: str
    primary_metrics: dict[str, Any] = Field(default_factory=dict)
    competitor_metrics: dict[str, dict[str, Any]] = Field(default_factory=dict)
    observations: str
    matched_viewport: str = "desktop_1440"


class UXBenchmark(BaseModel):
    """UX and usability comparison based on verified findings."""

    dimension: str
    primary_findings_count: int = 0
    competitor_findings_counts: dict[str, int] = Field(default_factory=dict)
    observed_patterns: list[str] = Field(default_factory=list)


class TechnicalBenchmark(BaseModel):
    """Technical SEO and performance metric comparison."""

    metric_name: str
    primary_value: Optional[Any] = None
    competitor_values: dict[str, Optional[Any]] = Field(default_factory=dict)
    comparable: bool = True
    measurement_condition: str = "same_origin_crawl"


class TrustAssessment(BaseModel):
    """Visible trust and credibility elements on site."""

    site_id: str
    named_testimonials_count: int = 0
    case_studies_count: int = 0
    security_compliance_claims: list[str] = Field(default_factory=list)
    visible_contact_info: bool = False
    evidence_ids: list[str] = Field(default_factory=list)


class CompetitiveGap(BaseModel):
    """Structured gap identified between primary and competitor website evidence."""

    gap_id: str
    title: str
    gap_type: Literal[
        "offering_presentation_gap",
        "messaging_gap",
        "content_gap",
        "ux_gap",
        "visual_gap",
        "technical_gap",
        "trust_signal_gap",
        "potential_differentiation",
        "not_assessed",
    ]
    description: str
    description_ar: str
    observed_difference: str
    primary_status: str
    competitor_status: str
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    affected_competitors: list[str] = Field(default_factory=list)
    strategic_implication: str
    validation_required: str


class CompetitiveOpportunity(BaseModel):
    """Strategic actionable opportunity inferred from competitive analysis."""

    opportunity_id: str
    title: str
    title_ar: str
    opportunity_type: str
    primary_site: str
    affected_competitors: list[str] = Field(default_factory=list)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    observed_difference: str
    strategic_interpretation: str
    suggested_action: str
    suggested_action_ar: str
    estimated_impact: RecommendationImpact = "medium"
    estimated_effort: RecommendationEffort = "medium"
    confidence_category: ConfidenceCategory = "inferred"
    validation_required: str


class CompetitiveFinding(BaseModel):
    """Standardized finding record adhering to Site DNA evidence principles."""

    finding_id: str
    title: str
    category: str
    description: str
    description_ar: str
    primary_site_id: str
    competitor_site_ids: list[str] = Field(default_factory=list)
    source_evidence_ids: list[str] = Field(default_factory=list)
    observation_type: ObservationType = "observed"
    severity: FindingSeverity = "medium"
    confidence_category: ConfidenceCategory = "observed"
    comparison_scope: str = "multi_site"
    potential_impact: str = ""
    recommended_action: str = ""
    limitations: str = ""


class CompetitiveRecommendation(BaseModel):
    """Prioritized remediation and optimization recommendation."""

    recommendation_id: str
    priority: RecommendationPriority = "p2"
    title: str
    title_ar: str
    description: str
    description_ar: str
    category: str
    affected_competitor_ids: list[str] = Field(default_factory=list)
    expected_benefit: str
    suggested_action: str
    effort: RecommendationEffort = "medium"
    impact: RecommendationImpact = "medium"
    supporting_finding_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class CompetitiveScore(BaseModel):
    """Evidence-dependent transparent benchmark scoring."""

    overall_score: Optional[float] = None
    dimension_scores: dict[str, Optional[float]] = Field(default_factory=dict)
    dimension_weights: dict[str, float] = Field(
        default_factory=lambda: {
            "positioning": 0.20,
            "product_offering": 0.20,
            "content_messaging": 0.15,
            "ux_ui": 0.15,
            "visual_identity": 0.15,
            "technical_seo": 0.15,
        }
    )
    site_scores: dict[str, dict[str, Optional[float]]] = Field(default_factory=dict)
    coverage_percentages: dict[str, float] = Field(default_factory=dict)
    not_assessed_reasons: dict[str, str] = Field(default_factory=dict)
    rubric_version: str = "1.0"


class CompetitorAnalysisStatistics(BaseModel):
    """Operational statistics for benchmark execution."""

    total_competitors_analyzed: int = 0
    total_pages_analyzed: int = 0
    total_features_compared: int = 0
    total_gaps_identified: int = 0
    total_opportunities: int = 0
    total_recommendations: int = 0
    total_model_calls: int = 0
    execution_duration_ms: float = 0.0
    ai_status: str = "operational"


class CompetitorAnalysisContext(BaseModel):
    """Complete consolidated context passed to analyzers and agents."""

    comparison_run_id: str
    primary_site: CompetitorSourceRecord
    competitor_sites: list[CompetitorSourceRecord]
    comparison_objectives: list[str] = Field(default_factory=list)
    market_context: Optional[str] = None
    source_run_ids: list[str] = Field(default_factory=list)
    source_timestamps: dict[str, str] = Field(default_factory=dict)
    coverage: dict[str, Any] = Field(default_factory=dict)
    collection_limitations: list[str] = Field(default_factory=list)
    model: str = "gemini-3.6-flash"
    analysis_settings: dict[str, Any] = Field(default_factory=dict)


class CompetitorIntelligenceReport(BaseModel):
    """Final comprehensive deliverable for Competitor Intelligence."""

    comparison_run_id: str
    status: AnalysisExecutionStatus = "completed"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    primary_site: CompetitorSourceRecord
    competitor_sites: list[CompetitorSourceRecord] = Field(default_factory=list)
    relevance_assessments: list[CompetitorRelevance] = Field(default_factory=list)
    profiles: list[CompetitorProfile] = Field(default_factory=list)
    feature_matrix: list[FeatureComparisonRecord] = Field(default_factory=list)
    pricing_comparison: list[PricingRecord] = Field(default_factory=list)
    positioning_assessments: list[PositioningAssessment] = Field(default_factory=list)
    messaging_benchmarks: list[MessagingBenchmark] = Field(default_factory=list)
    visual_benchmarks: list[VisualBenchmark] = Field(default_factory=list)
    ux_benchmarks: list[UXBenchmark] = Field(default_factory=list)
    technical_benchmarks: list[TechnicalBenchmark] = Field(default_factory=list)
    trust_assessments: list[TrustAssessment] = Field(default_factory=list)
    gaps: list[CompetitiveGap] = Field(default_factory=list)
    opportunities: list[CompetitiveOpportunity] = Field(default_factory=list)
    findings: list[CompetitiveFinding] = Field(default_factory=list)
    recommendations: list[CompetitiveRecommendation] = Field(default_factory=list)
    scores: CompetitiveScore = Field(default_factory=CompetitiveScore)
    statistics: CompetitorAnalysisStatistics = Field(default_factory=CompetitorAnalysisStatistics)
    report_markdown: str = ""
    limitations: list[str] = Field(default_factory=list)

    @property
    def overall_score(self) -> Optional[float]:
        return self.scores.overall_score if self.scores else None

    @property
    def analysis_run_id(self) -> str:
        return self.comparison_run_id
