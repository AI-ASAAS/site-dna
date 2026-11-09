"""Pydantic schemas for Site DNA Phase 10 — Web Accessibility, Inclusive Experience & WCAG 2.2 Intelligence."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# Core Assessment Literals & Categories
AssessmentState = Literal[
    "confirmed_failure",
    "potential_issue",
    "passed_specific_check",
    "manual_review_required",
    "not_applicable",
    "not_assessed",
]

AccessibilityCategory = Literal[
    "semantics_names",
    "keyboard_focus",
    "visual_contrast",
    "forms_interaction",
    "navigation_structure",
    "language_media",
]

FindingSeverity = Literal["critical", "high", "medium", "low"]
PriorityLevel = Literal["P1", "P2", "P3"]
ConformanceLevel = Literal["A", "AA", "AAA"]
ReviewTaskStatus = Literal[
    "pending_manual_review",
    "manually_verified_pass",
    "manually_verified_fail",
    "not_applicable",
    "unable_to_test",
]


class AccessibilityAnalysisRequest(BaseModel):
    """Request payload to initiate or configure accessibility analysis."""

    crawl_run_id: str = Field(..., description="ID of completed discovery crawl run")
    visual_run_id: Optional[str] = Field(None, description="Optional ID of visual capture run")
    ux_run_id: Optional[str] = Field(None, description="Optional ID of UX/UI analysis run")
    language: str = Field(default="ar", description="Language ('ar' or 'en')")
    max_pages: int = Field(default=8, ge=1, le=50, description="Max representative pages to evaluate")
    deterministic_only: bool = Field(default=False, description="Run deterministic checks only (skip AI)")
    include_automated_rules: bool = Field(default=True, description="Execute automated rule engine")
    save_results: bool = Field(default=True, description="Persist analysis artifacts to disk")


class AccessibilityPageRecord(BaseModel):
    """Normalized record of a page inspected during accessibility evaluation."""

    page_url: str
    page_title: Optional[str] = None
    status_code: int = 200
    document_language: Optional[str] = None
    document_direction: Optional[Literal["rtl", "ltr", "auto"]] = None
    viewport: Optional[dict[str, Any]] = None
    screenshot_path: Optional[str] = None
    dom_snapshot_ref: Optional[str] = None
    accessibility_tree_ref: Optional[str] = None
    interactive_elements_count: int = 0
    form_controls_count: int = 0
    images_count: int = 0
    links_count: int = 0
    headings_count: int = 0
    landmarks_count: int = 0
    is_representative_sample: bool = False
    sample_reason: Optional[str] = None


class AccessibilitySamplingRecord(BaseModel):
    """Representative sampling plan documenting page coverage and limitations."""

    sampled_pages_count: int = 0
    total_pages_discovered: int = 0
    sampled_pages: list[AccessibilityPageRecord] = []
    selection_strategy: str = "representative_heuristics"
    excluded_pages_count: int = 0
    coverage_limitations: list[str] = []
    coverage_limitations_ar: list[str] = []

    @property
    def sampling_limitations_ar(self) -> str:
        return "\n".join(self.coverage_limitations_ar)


class AccessibleNameRecord(BaseModel):
    """Individual accessible name relationship record."""

    element_ref: str
    tag_name: str
    role: Optional[str] = None
    accessible_name: Optional[str] = None
    name_source: Literal[
        "native_label",
        "aria_label",
        "aria_labelledby",
        "text_content",
        "alt_attribute",
        "title_attribute",
        "missing",
        "conflicting",
    ]
    visible_text: Optional[str] = None
    name_matches_visible: bool = True
    has_conflicting_labels: bool = False
    evidence_id: str

    @property
    def element_html(self) -> str:
        return self.element_ref

    @property
    def computed_name(self) -> str:
        return self.accessible_name or ""

    @property
    def naming_source(self) -> str:
        return "label_for" if self.name_source == "native_label" else self.name_source


class SemanticAssessment(BaseModel):
    """Evaluation of semantic HTML, landmarks, and structural elements."""

    has_main_landmark: bool = False
    nav_landmarks_count: int = 0
    headings_hierarchy_valid: bool = True
    heading_levels_present: list[int] = []
    buttons_vs_divs_ratio: float = 1.0
    non_semantic_clickables_count: int = 0
    data_tables_with_headers: int = 0
    unheaded_tables_count: int = 0
    semantic_score: float = 100.0
    evidence_ids: list[str] = []


class ImagesMediaAssessment(BaseModel):
    """Evaluation of non-text content, image alternatives, and media."""

    total_images: int = 0
    decorative_images_count: int = 0
    informative_images_count: int = 0
    missing_alt_count: int = 0
    functional_icon_buttons_without_name: int = 0
    svg_elements_without_title: int = 0
    videos_count: int = 0
    videos_with_captions_observed: int = 0
    manual_media_reviews_needed: int = 0
    evidence_ids: list[str] = []


class KeyboardFocusAssessment(BaseModel):
    """Evaluation of keyboard accessibility, focus indicators, and traps."""

    focusable_elements_count: int = 0
    tab_order_sequential: bool = True
    positive_tabindex_count: int = 0
    keyboard_traps_detected: int = 0
    skip_link_present: bool = False
    focus_indicators_visible: bool = True
    focus_obscured_by_sticky_elements: int = 0
    focus_restoration_supported: bool = True
    evidence_ids: list[str] = []


class ContrastMeasurement(BaseModel):
    """Specific color contrast calculation for a rendered element."""

    element_ref: str
    selector: str
    text_sample: str
    foreground_color: str
    background_color: str
    contrast_ratio: float
    is_large_text: bool = False
    required_ratio: float = 4.5
    meets_threshold: bool = True
    is_complex_background: bool = False
    evidence_id: str = ""
    font_size_px: float = 14.0
    passes_wcag_aa_normal: bool = True
    passes_wcag_aa_large: bool = True


class ContrastAssessment(BaseModel):
    """Overall visual and color contrast evaluation."""

    measured_text_elements_count: int = 0
    contrast_violations_aa_normal: int = 0
    contrast_violations_aa_large: int = 0
    contrast_passes_count: int = 0
    complex_backgrounds_needing_review: int = 0
    worst_contrast_ratio: Optional[float] = None
    sample_measurements: list[ContrastMeasurement] = []
    evidence_ids: list[str] = []


class ReflowZoomAssessment(BaseModel):
    """Evaluation of narrow viewport reflow, 400% zoom, and text spacing."""

    horizontal_overflow_at_320px: bool = False
    text_clipping_observed: bool = False
    user_scalable_disabled: bool = False
    content_overlap_observed: bool = False
    two_dimensional_scrolling_required: bool = False
    evidence_ids: list[str] = []


class TargetSizeAssessment(BaseModel):
    """Evaluation of pointer targets (WCAG 2.2 SC 2.5.8)."""

    total_interactive_targets: int = 0
    targets_below_24px: int = 0
    targets_with_sufficient_spacing: int = 0
    target_size_exceptions_applied: int = 0
    confirmed_target_size_failures: int = 0
    evidence_ids: list[str] = []

    @property
    def evaluated_targets_count(self) -> int:
        return self.total_interactive_targets

    @property
    def targets_meeting_24px_threshold(self) -> int:
        return max(0, self.total_interactive_targets - self.targets_below_24px)


class ARIAAssessment(BaseModel):
    """Audit of WAI-ARIA roles, states, and authoring practices."""

    aria_roles_used: list[str] = []
    invalid_roles: list[str] = []
    invalid_aria_roles: list[str] = []
    unsupported_aria_attributes: list[str] = []
    broken_aria_references: list[str] = []
    misused_aria_hidden: int = 0
    live_regions_present: int = 0
    evidence_ids: list[str] = []


class FormAccessibilityAssessment(BaseModel):
    """Audit of form controls, labels, error feedback, and instructions."""

    total_form_inputs: int = 0
    inputs_with_explicit_labels: int = 0
    unlabeled_inputs: int = 0
    required_fields_indicated_programmatically: int = 0
    error_messages_programmatically_associated: int = 0
    has_accessible_authentication_considerations: bool = False
    evidence_ids: list[str] = []


class LanguageDirectionAssessment(BaseModel):
    """Audit of document language, text direction, and Arabic RTL accessibility."""

    html_lang_declared: bool = True
    declared_language: Optional[str] = None
    declared_direction: Optional[Literal["rtl", "ltr", "auto"]] = None
    bilingual_arabic_english_support: bool = False
    mixed_direction_spans_isolated: bool = True
    evidence_ids: list[str] = []


class AutomatedRuleResult(BaseModel):
    """Result emitted by automated accessibility rules engine."""

    rule_id: str
    engine: str = "axe-core-compatible"
    ruleset_version: str = "4.10.0"
    impact: Literal["critical", "serious", "moderate", "minor"]
    wcag_tags: list[str] = []
    selector: str
    html_snippet: str
    failure_summary: str
    failure_summary_ar: str
    evidence_id: str


class WCAGCriterionAssessment(BaseModel):
    """Mapping of evaluated evidence to a specific WCAG 2.2 success criterion."""

    criterion_id: str
    criterion_name: str
    criterion_name_ar: str
    conformance_level: ConformanceLevel
    applicability: bool = True
    test_method: Literal["automated", "semi_automated", "manual_required", "not_testable_passively"]
    status: AssessmentState
    evidence_ids: list[str] = []
    limitations: str = ""
    limitations_ar: str = ""


class ManualReviewTask(BaseModel):
    """Structured human review task for issues that cannot be conclusively automated."""

    review_id: str
    page_url: str
    component_reference: str
    wcag_criterion: str
    review_question: str
    review_question_ar: str
    why_automation_is_insufficient: str
    why_automation_is_insufficient_ar: str
    manual_steps: list[str] = []
    manual_steps_ar: list[str] = []
    expected_accessible_behavior: str
    expected_accessible_behavior_ar: str
    available_evidence_ids: list[str] = []
    review_status: ReviewTaskStatus = "pending_manual_review"
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[str] = None


class AccessibilityFinding(BaseModel):
    """Individual accessibility barrier or finding grounded in observable evidence."""

    finding_id: str
    title: str
    title_ar: str
    description: str
    description_ar: str
    page_url: str = "https://example.com"
    component_reference: str = "document"
    category: AccessibilityCategory = "semantics"
    wcag_criteria: list[str] = []
    evidence_ids: list[str] = []
    test_method: str = "deterministic_observation"
    assessment_state: AssessmentState
    severity: FindingSeverity
    confidence: float = 0.95
    user_impact: str = "Potential accessibility limitation"
    user_impact_ar: str = "أثر سلبي محتمل على سهولة الوصول"
    recommended_fix: str = "Follow WCAG 2.2 guidelines"
    recommended_fix_ar: str = "إصلاح المشكلة وفق معايير WCAG 2.2"
    verification_method: str = "manual_or_automated_retest"
    verification_method_ar: str = "إعادة الفحص الآلي واليدوي"
    manual_review_required: bool = False
    limitations: str = ""
    limitations_ar: str = ""


class AccessibilityRecommendation(BaseModel):
    """Actionable remediation action prioritized by barrier severity."""

    recommendation_id: str
    title: str
    title_ar: str
    related_finding_ids: list[str] = []
    priority: PriorityLevel
    affected_pages: list[str] = []
    wcag_criteria: list[str] = []
    evidence_ids: list[str] = []
    observed_barrier: str
    observed_barrier_ar: str
    user_impact: str
    user_impact_ar: str
    recommended_remediation: str
    recommended_remediation_ar: str
    code_snippet: Optional[str] = None
    implementation_guidance: str
    implementation_guidance_ar: str
    verification_steps: list[str] = []
    verification_steps_ar: list[str] = []
    manual_validation_needed: bool = False
    estimated_effort: Literal["low", "medium", "high"] = "medium"


class AccessibilityScore(BaseModel):
    """Accessibility evidence assessment score across 6 weighted dimensions."""

    overall_score: Optional[float] = None
    semantics_names_score: float = 100.0
    keyboard_focus_score: float = 100.0
    visual_contrast_score: float = 100.0
    forms_interaction_score: float = 100.0
    navigation_structure_score: float = 100.0
    language_media_score: float = 100.0
    evidence_coverage_percentage: float = 100.0
    rubric_version: str = "1.0.0"
    score_label: str = "Moderate"
    score_label_ar: str = "متوسط"
    conformance_disclaimer: str = (
        "This is an automated evidence-based accessibility score. It is not an official "
        "WCAG conformance certification or legal compliance determination."
    )
    conformance_disclaimer_ar: str = (
        "هذا التقييم هو مؤشر استرشادي مستند إلى الأدلة التقنية المرصودة آلياً. "
        "ولا يمثل شهادة مطابقة رسمية لمعايير WCAG ولا إقراراً بامتثال قانوني."
    )


class AccessibilityStatistics(BaseModel):
    """Execution telemetry and metric aggregates."""

    pages_evaluated: int = 0
    total_elements_inspected: int = 0
    confirmed_failures_count: int = 0
    potential_issues_count: int = 0
    manual_review_tasks_count: int = 0
    automated_rules_count: int = 0
    wcag_criteria_evaluated: int = 0
    duration_ms: float = 0.0


class AccessibilityContext(BaseModel):
    """Runtime context passed across accessibility intelligence analyzers."""

    accessibility_run_id: str
    crawl_run_id: str
    visual_run_id: Optional[str] = None
    ux_run_id: Optional[str] = None
    target_url: str
    site_origin: str
    page_records: list[AccessibilityPageRecord] = []
    sampling_record: AccessibilitySamplingRecord = Field(default_factory=AccessibilitySamplingRecord)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AccessibilityReport(BaseModel):
    """Comprehensive analytical audit report for Phase 10 Accessibility Intelligence."""

    accessibility_run_id: str
    crawl_run_id: str
    visual_run_id: Optional[str] = None
    ux_run_id: Optional[str] = None
    target_url: str
    site_origin: str
    analysis_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    analysis_status: Literal["completed", "completed_deterministic_only", "blocked_ai", "failed"] = "completed"
    model_name: str = "gemini-3.6-flash"
    sampling: AccessibilitySamplingRecord
    semantics: SemanticAssessment
    accessible_names: list[AccessibleNameRecord] = []
    images_media: ImagesMediaAssessment
    keyboard_focus: KeyboardFocusAssessment
    contrast: ContrastAssessment
    reflow_zoom: ReflowZoomAssessment
    target_size: TargetSizeAssessment
    aria: ARIAAssessment
    forms: FormAccessibilityAssessment
    language_direction: LanguageDirectionAssessment
    wcag_criteria: list[WCAGCriterionAssessment] = []
    automated_rule_results: list[AutomatedRuleResult] = []
    manual_review_tasks: list[ManualReviewTask] = []
    scores: AccessibilityScore
    findings: list[AccessibilityFinding] = []
    recommendations: list[AccessibilityRecommendation] = []
    statistics: AccessibilityStatistics
    error: Optional[str] = None
