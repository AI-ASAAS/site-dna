"""Pydantic schemas and data contracts for Site DNA Content & Marketing Intelligence."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

VerificationStatus = Literal[
    "observed_only",
    "supported_onsite",
    "contradicted_by_collected_evidence",
    "externally_verified",
    "not_assessed",
]

FindingSeverity = Literal["critical", "high", "medium", "low"]
ObservationType = Literal["observed", "derived", "heuristic", "ai_interpretation", "not_assessed"]
ConfidenceCategory = Literal["observed", "measured", "inferred"]
RecommendationPriority = Literal["p1", "p2", "p3"]
RecommendationEffort = Literal["small", "medium", "large"]
RecommendationImpact = Literal["high", "medium", "low"]
AnalysisExecutionStatus = Literal["completed", "partial", "ai_blocked", "failed", "cancelled"]


class ContentAnalysisRequest(BaseModel):
    """Input request parameters for Content & Marketing Intelligence audit."""

    crawl_run_id: str = Field(description="Existing crawl run identifier (e.g. 98b5cd6a-3225-4c00-9b75-0d13061d85f1)")
    visual_run_id: Optional[str] = Field(default=None, description="Optional associated visual capture run ID")
    language: Optional[str] = Field(default="ar", description="Preferred report language ('ar' or 'en')")
    max_pages: Optional[int] = Field(default=8, ge=1, le=50, description="Maximum pages to analyze")
    save_results: Optional[bool] = Field(default=True, description="Whether to persist report and JSON artifacts")
    offline_mode: bool = Field(default=False, description="Force offline analysis mode without calling AI Studio")
    deterministic_only: bool = Field(default=False, description="Run only deterministic Layer B algorithms")


class PageContentRecord(BaseModel):
    """Normalized structured content record for a single crawled website page."""

    page_id: str = Field(description="Unique safe page identifier")
    page_url: str = Field(description="Canonical page URL")
    page_type: str = Field(
        default="unknown",
        description="Page classification: home, about, services, products, pricing, contact, blog, faq, other",
    )
    page_title: Optional[str] = Field(default=None, description="Page title")
    meta_description: Optional[str] = Field(default=None, description="Meta description tag")
    language: Optional[str] = Field(default=None, description="Declared or detected language code")
    dir: Optional[str] = Field(default=None, description="Text direction (rtl, ltr)")
    headings: list[dict[str, Any]] = Field(default_factory=list, description="Ordered headings with level and text")
    main_content: str = Field(default="", description="Clean main visible text excerpt")
    paragraphs: list[dict[str, Any]] = Field(default_factory=list, description="Extracted paragraph structures")
    service_descriptions: list[str] = Field(default_factory=list, description="Identified service descriptions")
    product_descriptions: list[str] = Field(default_factory=list, description="Identified product descriptions")
    cta_candidates: list[dict[str, Any]] = Field(default_factory=list, description="Buttons and CTA link elements")
    navigation_labels: list[str] = Field(default_factory=list, description="Internal navigation anchor texts")
    trust_signal_candidates: list[str] = Field(default_factory=list, description="Visible trust signal excerpts")
    word_count: int = Field(default=0, ge=0, description="Total word count in main content")
    source_evidence_ids: list[str] = Field(default_factory=list, description="Referenced Layer A evidence IDs")
    extraction_limitations: list[str] = Field(default_factory=list, description="Extraction boundary notices")


class ContentInventory(BaseModel):
    """Structured inventory of discovered website content assets."""

    total_pages: int = Field(default=0, ge=0)
    page_types_distribution: dict[str, int] = Field(default_factory=dict)
    total_word_count: int = Field(default=0, ge=0)
    average_word_count_per_page: float = Field(default=0.0, ge=0.0)
    languages_detected: list[str] = Field(default_factory=list)
    pages: list[PageContentRecord] = Field(default_factory=list)
    missing_descriptions_count: int = Field(default=0, ge=0)
    headings_summary: dict[str, int] = Field(default_factory=dict)


class TrustClaimRecord(BaseModel):
    """Provenance record for a factual or marketing assertion made on the website."""

    claim_id: str = Field(description="Unique claim identifier, e.g. CLM-01")
    claim_text: str = Field(description="Exact observed statement or assertion")
    claim_type: str = Field(
        default="general_marketing_claim",
        description="Type: feature_claim, benefit_claim, performance_claim, pricing_claim, availability_claim, testimonial_claim, credential_claim, comparative_claim, guarantee_claim, general_marketing_claim",
    )
    page_url: str = Field(description="URL where claim was observed")
    source_evidence_ids: list[str] = Field(default_factory=list)
    supporting_onsite_references: list[str] = Field(default_factory=list)
    verification_status: VerificationStatus = Field(default="observed_only")
    review_required: bool = Field(default=False, description="Flag for sensitive/unsubstantiated claims")


class ValuePropositionAssessment(BaseModel):
    """Structured evaluation of website value proposition and core offering."""

    offering_summary: Optional[str] = Field(default=None, description="What the business offers")
    target_audience: Optional[str] = Field(default=None, description="Identified or implied target audience")
    problem_addressed: Optional[str] = Field(default=None, description="Problem or need addressed")
    core_benefits: list[str] = Field(default_factory=list, description="Communicated user/business benefits")
    claimed_differentiators: list[str] = Field(default_factory=list, description="Claimed unique selling points")
    clarity_rating: str = Field(default="moderate", description="clear, moderate, vague, unclear")
    is_understandable_without_context: bool = Field(default=True)
    evidence_ids: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)


class MessagingAssessment(BaseModel):
    """Evaluation of homepage and headline marketing communication."""

    hero_headline: Optional[str] = Field(default=None)
    hero_subheadline: Optional[str] = Field(default=None)
    headline_clarity: str = Field(default="clear", description="clear, moderate, ambiguous, absent")
    jargon_level: str = Field(default="low", description="low, moderate, excessive")
    absolute_claims_count: int = Field(default=0, ge=0)
    repeated_phrases: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class ServiceContentAssessment(BaseModel):
    """Evaluation of product and service description completeness."""

    total_services_identified: int = Field(default=0, ge=0)
    total_products_identified: int = Field(default=0, ge=0)
    descriptions_completeness: str = Field(default="adequate", description="comprehensive, adequate, sparse, missing")
    unexplained_offerings: list[str] = Field(default_factory=list)
    next_step_clarity: bool = Field(default=True)
    evidence_ids: list[str] = Field(default_factory=list)


class CTAContentAssessment(BaseModel):
    """Evaluation of Call-to-Action copy, action clarity, and alignment."""

    total_ctas_observed: int = Field(default=0, ge=0)
    unique_cta_labels: list[str] = Field(default_factory=list)
    generic_ctas_count: int = Field(default=0, ge=0)
    primary_cta_identified: bool = Field(default=False)
    inconsistent_destinations_count: int = Field(default=0, ge=0)
    evidence_ids: list[str] = Field(default_factory=list)


class BrandVoiceAssessment(BaseModel):
    """Evaluation of tone, terminology, and writing style."""

    observed_tone: str = Field(
        default="professional", description="formal, professional, conversational, casual, mixed"
    )
    primary_language: str = Field(default="ar")
    dialect_detected: Optional[str] = Field(default=None)
    is_bilingual: bool = Field(default=False)
    cross_page_tone_consistency: str = Field(
        default="consistent", description="consistent, slight_variation, inconsistent, not_assessed"
    )
    evidence_ids: list[str] = Field(default_factory=list)


class ContentGap(BaseModel):
    """Detected content or messaging gap within the analyzed pages."""

    gap_id: str = Field(description="Unique gap identifier, e.g. GAP-01")
    gap_type: str = Field(
        description="unclear_offering, missing_term_explanation, contextless_cta, sparse_service_detail, missing_next_step, unanswered_question, unsupported_assertion"
    )
    description: str = Field(description="Description of the communication gap")
    page_url: str = Field(description="Page where gap was noted")
    severity: FindingSeverity = Field(default="medium")
    evidence_ids: list[str] = Field(default_factory=list)


class ContentFinding(BaseModel):
    """Evidence-backed finding for content, messaging, or copywriting issue."""

    finding_id: str = Field(description="Unique finding identifier, e.g. CF-01")
    title: str = Field(description="Concise finding headline")
    category: str = Field(
        description="value_proposition, messaging_clarity, service_content, cta_action, trust_claims, brand_voice, content_gap"
    )
    description: str = Field(description="Detailed finding explanation")
    page_url: str = Field(description="URL of source page")
    source_excerpt: Optional[str] = Field(default=None, description="Exact quoted text from website")
    evidence_ids: list[str] = Field(default_factory=list, description="Ground truth evidence IDs")
    observation_type: ObservationType = Field(default="observed")
    severity: FindingSeverity = Field(default="medium")
    confidence_category: ConfidenceCategory = Field(default="observed")
    potential_communication_impact: Optional[str] = Field(default=None)
    recommendation_id: Optional[str] = Field(default=None)


class ContentRecommendation(BaseModel):
    """Actionable, prioritized recommendation for content improvement."""

    recommendation_id: str = Field(description="Unique recommendation ID, e.g. CR-01")
    title: str = Field(description="Recommendation headline")
    related_finding_ids: list[str] = Field(default_factory=list)
    affected_page: str = Field(description="Page URL or target section")
    affected_content: Optional[str] = Field(default=None, description="Specific copy or component affected")
    evidence_ids: list[str] = Field(default_factory=list)
    recommended_change: str = Field(description="Exact improvement proposed")
    rationale: str = Field(description="Evidence-based reasoning")
    expected_communication_benefit: str = Field(description="Expected benefit to audience comprehension")
    estimated_effort: RecommendationEffort = Field(default="small")
    estimated_impact: RecommendationImpact = Field(default="medium")
    priority: RecommendationPriority = Field(default="p2")
    verification_method: str = Field(default="inspection")


class CopyRewriteProposal(BaseModel):
    """Grounded copy rewrite suggestion that strictly preserves verified facts."""

    proposal_id: str = Field(description="Unique rewrite proposal ID, e.g. PRP-01")
    element_type: str = Field(
        description="headline_h1, hero_copy, service_description, product_intro, cta_label, value_proposition, trust_reassurance, faq_question"
    )
    source_page: str = Field(description="Source page URL")
    source_evidence_id: Optional[str] = Field(default=None)
    original_excerpt: Optional[str] = Field(default=None, description="Original website copy excerpt")
    identified_communication_issue: str = Field(description="Why original copy could be improved")
    proposed_replacement: str = Field(description="Suggested improved copy")
    explanation_of_change: str = Field(description="Detailed explanation of copywriting strategy applied")
    facts_preserved: list[str] = Field(default_factory=list, description="Explicit verified facts retained")
    information_requiring_confirmation: list[str] = Field(
        default_factory=list, description="Placeholders or assumptions requiring business validation"
    )
    is_suggestion: bool = Field(default=True, description="Strictly True to indicate non-published proposal")


class ContentScore(BaseModel):
    """Score for a specific content and messaging dimension with rationale."""

    dimension_name: str = Field(description="English dimension identifier")
    dimension_name_ar: str = Field(description="Arabic dimension title")
    weight: float = Field(ge=0.0, le=1.0, description="Normalized weight in overall calculation")
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Score 0-100 or None if unassessed")
    status: str = Field(default="assessed", description="assessed, not_assessed, insufficient_evidence")
    rationale: str = Field(default="", description="Explanatory rationale grounded in findings")
    evidence_count: int = Field(default=0, ge=0)


class ContentAnalysisStatistics(BaseModel):
    """Operational statistics and metrics for the content analysis execution."""

    pages_analyzed: int = Field(default=0, ge=0)
    total_words_analyzed: int = Field(default=0, ge=0)
    claims_inventoried: int = Field(default=0, ge=0)
    ctas_analyzed: int = Field(default=0, ge=0)
    findings_count: int = Field(default=0, ge=0)
    recommendations_count: int = Field(default=0, ge=0)
    rewrite_proposals_count: int = Field(default=0, ge=0)
    model_calls_count: int = Field(default=0, ge=0)
    model_name: str = Field(default="gemini-3.6-flash")
    execution_duration_ms: float = Field(default=0.0, ge=0.0)
    ai_status: AnalysisExecutionStatus = Field(default="completed")


class ContentMarketingReport(BaseModel):
    """Comprehensive Content & Marketing Intelligence audit report."""

    schema_version: str = Field(default="1.0")
    analysis_run_id: str = Field(description="Unique content analysis identifier, e.g. cnt-123456789abc")
    crawl_run_id: str = Field(description="Source crawl run identifier")
    visual_run_id: Optional[str] = Field(default=None, description="Optional associated visual capture run ID")
    target_origin: str = Field(description="Canonical website domain")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    analysis_status: AnalysisExecutionStatus = Field(default="completed")
    overall_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    scores: list[ContentScore] = Field(default_factory=list)
    content_inventory: ContentInventory = Field(default_factory=ContentInventory)
    value_proposition: ValuePropositionAssessment = Field(default_factory=ValuePropositionAssessment)
    messaging: MessagingAssessment = Field(default_factory=MessagingAssessment)
    services_and_products: ServiceContentAssessment = Field(default_factory=ServiceContentAssessment)
    ctas: CTAContentAssessment = Field(default_factory=CTAContentAssessment)
    trust_and_claims: list[TrustClaimRecord] = Field(default_factory=list)
    brand_voice: BrandVoiceAssessment = Field(default_factory=BrandVoiceAssessment)
    content_gaps: list[ContentGap] = Field(default_factory=list)
    findings: list[ContentFinding] = Field(default_factory=list)
    quarantined_findings: list[ContentFinding] = Field(default_factory=list)
    recommendations: list[ContentRecommendation] = Field(default_factory=list)
    rewrite_proposals: list[CopyRewriteProposal] = Field(default_factory=list)
    statistics: ContentAnalysisStatistics = Field(default_factory=ContentAnalysisStatistics)
    report_markdown_path: Optional[str] = Field(default=None)
    analysis_json_path: Optional[str] = Field(default=None)
