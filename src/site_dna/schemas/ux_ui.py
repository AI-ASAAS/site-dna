"""Pydantic schemas for Site DNA Phase 05 AI UX/UI & Usability Intelligence."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

UXAnalysisStatus = Literal["completed", "partial", "ai_blocked", "failed", "cancelled"]
FindingSeverity = Literal["critical", "high", "medium", "low", "informational"]
FindingConfidence = Literal["confirmed_by_measurement", "high_confidence_ai", "hypothesized", "uncertain"]
ObservationType = Literal["observed", "derived", "heuristic", "ai_interpretation", "not_assessed"]
RecommendationEffort = Literal["small", "medium", "large"]
RecommendationImpact = Literal["high", "medium", "low"]
RecommendationPriority = Literal["P1", "P2", "P3"]
ScoreStatus = Literal["assessed", "not_assessed", "insufficient_evidence"]
JourneyStatus = Literal["graph_derived", "browser_tested", "hypothetical", "not_testable"]


class UXAnalysisRequest(BaseModel):
    """Input payload to trigger UX/UI intelligence analysis."""

    visual_run_id: Optional[str] = Field(
        default=None, description="Existing visual run identifier (e.g. vis-e6b6128de9b5)"
    )
    visual_manifest_file: Optional[str] = Field(default=None, description="Path to visual manifest.json")
    crawl_run_id: Optional[str] = Field(default=None, description="Optional associated crawl run identifier")
    language: str = Field(default="ar", description="Language for generated report ('ar' or 'en')")
    max_pages: int = Field(default=8, ge=1, le=50, description="Maximum pages to include in UX analysis")
    max_images: Optional[int] = Field(
        default=None, ge=1, le=30, description="Maximum screenshots to inspect with vision"
    )
    save_results: bool = Field(default=True, description="Whether to save analysis artifacts to disk")
    offline_mode: bool = Field(default=False, description="Run purely offline without calling external APIs")


class UXEvidenceReference(BaseModel):
    """Traceable pointer to an underlying Phase 02/03 evidence record."""

    evidence_id: str
    evidence_category: str
    field_reference: str
    page_url: str
    viewport_profile: str = "desktop"
    screenshot_reference: Optional[str] = None
    checksum: Optional[str] = None


class UXObservation(BaseModel):
    """Granular observation combining measured properties, derived metrics, and AI observations."""

    observation_id: str = Field(default_factory=lambda: f"OBS-UX-{uuid4().hex[:8]}")
    category: str = Field(
        description="navigation, interaction, cta_clarity, forms, responsive, accessibility, content_usability, user_journey, other"
    )
    page_url: str
    viewport_profile: str = "desktop"
    observation_type: ObservationType = "observed"
    field_reference: str
    observed_value: Any
    description: str
    evidence_ids: list[str] = Field(default_factory=list)


class UXFinding(BaseModel):
    """Structured, evidence-backed usability finding or issue identified during UX audit."""

    finding_id: str = Field(description="Unique finding identifier (e.g. UX-FIND-01)")
    title: str
    category: str = Field(
        description="navigation, information_architecture, interaction, cta_clarity, forms, responsive, accessibility, content_usability, user_journey, other"
    )
    description: str
    source_page: str
    viewport: str = "desktop"
    element_reference: Optional[str] = None
    evidence_ids: list[str] = Field(default_factory=list)
    observation_type: ObservationType = "ai_interpretation"
    severity: FindingSeverity = "medium"
    confidence_category: FindingConfidence = "high_confidence_ai"
    potential_user_impact: str = ""
    recommended_action: str = ""
    is_validated: bool = True
    rejection_reason: Optional[str] = None


class UXRecommendation(BaseModel):
    """Actionable, prioritized design and usability recommendation addressing validated findings."""

    recommendation_id: str = Field(description="Unique recommendation identifier (e.g. REC-UX-01)")
    related_finding_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    title: str
    problem_statement: str
    affected_component: str
    source_evidence: str
    proposed_solution: str
    expected_improvement: str
    estimated_effort: RecommendationEffort = "medium"
    expected_impact: RecommendationImpact = "medium"
    priority: RecommendationPriority = "P2"
    validation_method: str = ""


class UXNavigationAssessment(BaseModel):
    """Detailed structural assessment of website navigation and information architecture."""

    links_count: int = 0
    unique_destinations_count: int = 0
    reachable_pages: list[str] = Field(default_factory=list)
    isolated_pages: list[str] = Field(default_factory=list)
    max_navigation_depth: int = 0
    has_breadcrumbs: bool = False
    has_footer_nav: bool = False
    ambiguous_labels: list[dict[str, Any]] = Field(default_factory=list)
    duplicate_labels: list[dict[str, Any]] = Field(default_factory=list)
    graph_edges: list[dict[str, str]] = Field(default_factory=list)
    findings: list[UXFinding] = Field(default_factory=list)


class UXInteractionAssessment(BaseModel):
    """Assessment of interactive elements, affordances, and call-to-action distinction."""

    total_buttons: int = 0
    total_links: int = 0
    cta_candidates: list[dict[str, Any]] = Field(default_factory=list)
    interactive_elements: list[dict[str, Any]] = Field(default_factory=list)
    small_touch_targets: list[dict[str, Any]] = Field(default_factory=list)
    unlabeled_controls: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[UXFinding] = Field(default_factory=list)


class UXFormAssessment(BaseModel):
    """Assessment of form usability, fields, labeling, and submission affordances."""

    forms_detected: int = 0
    total_fields: int = 0
    unlabeled_fields: list[dict[str, Any]] = Field(default_factory=list)
    placeholder_only_fields: list[dict[str, Any]] = Field(default_factory=list)
    missing_submit_buttons: list[str] = Field(default_factory=list)
    form_summaries: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[UXFinding] = Field(default_factory=list)


class UXResponsiveAssessment(BaseModel):
    """Assessment of responsive usability, touch target geometry, and viewport adaptability."""

    horizontal_overflow_detected: bool = False
    overflow_pages: list[str] = Field(default_factory=list)
    clipped_elements_count: int = 0
    mobile_navigation_collapsed: bool = False
    undersized_touch_targets: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[UXFinding] = Field(default_factory=list)


class UXAccessibilityAssessment(BaseModel):
    """Automated accessibility audit covering WCAG-actionable criteria."""

    accessible_name_issues: list[dict[str, Any]] = Field(default_factory=list)
    heading_hierarchy_valid: bool = True
    heading_issues: list[str] = Field(default_factory=list)
    contrast_issues: list[dict[str, Any]] = Field(default_factory=list)
    keyboard_focusable_count: int = 0
    missing_aria_labels: list[dict[str, Any]] = Field(default_factory=list)
    findings: list[UXFinding] = Field(default_factory=list)


class UXContentAssessment(BaseModel):
    """Assessment of content structure, scanability, and Arabic RTL formatting."""

    heading_count: int = 0
    average_paragraph_length: float = 0.0
    rtl_supported: bool = True
    scanability_score: float = 100.0
    repeated_labels: list[str] = Field(default_factory=list)
    findings: list[UXFinding] = Field(default_factory=list)


class UXJourney(BaseModel):
    """Structured representation of a common user task route across the website."""

    journey_id: str = Field(description="Unique journey identifier (e.g. JRN-01)")
    goal: str
    starting_page: str
    target_page: str
    route: list[str] = Field(default_factory=list)
    transitions_count: int = 0
    missing_steps: list[str] = Field(default_factory=list)
    status: JourneyStatus = "graph_derived"
    potential_friction: str = ""
    supporting_link_text: list[str] = Field(default_factory=list)


class UXScoreExplanation(BaseModel):
    """Explainable scoring for a single UX/UI usability pillar."""

    dimension_name: str
    weight: float = Field(ge=0.0, le=1.0)
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    status: ScoreStatus = "assessed"
    explanation: str
    key_positive_factors: list[str] = Field(default_factory=list)
    key_negative_factors: list[str] = Field(default_factory=list)
    supporting_finding_ids: list[str] = Field(default_factory=list)


class UXAnalysisStatistics(BaseModel):
    """Quantitative execution statistics for the UX/UI audit run."""

    pages_analyzed: int = 0
    viewports_analyzed: int = 0
    screenshots_processed: int = 0
    interactive_elements_audited: int = 0
    forms_audited: int = 0
    journeys_mapped: int = 0
    total_findings: int = 0
    validated_findings: int = 0
    rejected_findings: int = 0
    recommendations_count: int = 0
    duration_ms: float = 0.0
    model_name: str = "gemini-3.6-flash"
    ai_analysis_completed: bool = True
    from_cache: bool = False
    quota_exhausted: bool = False


class UXReport(BaseModel):
    """Comprehensive UX/UI intelligence analysis report."""

    schema_version: str = "1.0"
    analysis_run_id: str = Field(default_factory=lambda: f"ux-{uuid4().hex[:12]}")
    crawl_run_id: str
    visual_run_id: str
    site_url: str
    model_name: str = "gemini-3.6-flash"
    analysis_status: UXAnalysisStatus = "completed"
    ai_analysis_completed: bool = True
    deterministic_analysis_completed: bool = True
    fallback_reason: Optional[str] = None
    from_cache: bool = False
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    summary_arabic: str
    summary_english: str
    overall_score: Optional[float] = None
    score_explanations: list[UXScoreExplanation] = Field(default_factory=list)

    navigation_assessment: UXNavigationAssessment = Field(default_factory=UXNavigationAssessment)
    interaction_assessment: UXInteractionAssessment = Field(default_factory=UXInteractionAssessment)
    forms_assessment: UXFormAssessment = Field(default_factory=UXFormAssessment)
    responsive_assessment: UXResponsiveAssessment = Field(default_factory=UXResponsiveAssessment)
    accessibility_assessment: UXAccessibilityAssessment = Field(default_factory=UXAccessibilityAssessment)
    content_assessment: UXContentAssessment = Field(default_factory=UXContentAssessment)
    user_journeys: list[UXJourney] = Field(default_factory=list)

    findings: list[UXFinding] = Field(default_factory=list)
    rejected_findings: list[UXFinding] = Field(default_factory=list)
    recommendations: list[UXRecommendation] = Field(default_factory=list)
    evidence_index: list[UXEvidenceReference] = Field(default_factory=list)
    limitations_arabic: list[str] = Field(default_factory=list)
    statistics: UXAnalysisStatistics = Field(default_factory=UXAnalysisStatistics)

    report_markdown_path: Optional[str] = None
    analysis_json_path: Optional[str] = None
