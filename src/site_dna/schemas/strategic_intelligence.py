"""Pydantic schemas for Site DNA Phase 11 — Strategic Intelligence & Unified Action Roadmap."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional, Union
import uuid

from pydantic import BaseModel, Field, field_validator

# Core type definitions
SourcePhase = Literal[
    "visual_identity",
    "ux_ui",
    "content_marketing",
    "technical_seo",
    "competitor_intelligence",
    "security_privacy",
    "accessibility",
]

FindingSeverity = Literal["critical", "high", "medium", "low", "info"]

NormalizedImpact = Literal[
    "critical_blocker",
    "high_friction",
    "moderate_impairment",
    "minor_observation",
    "unknown",
]

ConfidenceCategory = Literal["high", "medium", "low", "unverified"]

VerificationState = Literal[
    "confirmed_by_evidence",
    "potential_issue",
    "manual_review_required",
    "unverified_interpretation",
    "not_applicable",
]

PriorityLevel = Literal["P0", "P1", "P2", "P3"]

ActionOwnerRole = Literal[
    "Frontend Developer",
    "Backend Developer",
    "UI/UX Designer",
    "Content Specialist",
    "SEO Specialist",
    "Accessibility Specialist",
    "Security Specialist",
    "Product Owner",
    "Manual Review Required",
]

ActionStatus = Literal[
    "proposed",
    "needs_review",
    "approved",
    "planned",
    "in_progress",
    "completed_unverified",
    "verified_completed",
    "rejected",
    "deferred",
]

ConflictType = Literal[
    "performance_vs_visual",
    "conversion_vs_accessibility",
    "seo_vs_ux",
    "security_vs_functionality",
    "marketing_vs_trust",
    "general_tradeoff",
]

RootCauseConfidence = Literal[
    "confirmed_by_evidence",
    "strong_candidate",
    "possible_candidate",
    "not_established",
]

OpportunityCategory = Literal[
    "technical_stability",
    "security_privacy",
    "accessibility",
    "seo_discoverability",
    "ux_friction_reduction",
    "content_clarity",
    "brand_consistency",
    "conversion_experience",
    "competitive_differentiation",
    "performance_optimization",
]

RelationshipType = Literal[
    "duplicate_of",
    "related_to",
    "contributes_to",
    "potential_shared_cause",
    "conflicts_with",
    "depends_on",
    "blocks",
    "requires_manual_review",
]


class UnifiedFinding(BaseModel):
    """Normalized finding model preserving full provenance and original evidence references."""

    unified_finding_id: str = Field(
        default_factory=lambda: f"uf-{uuid.uuid4().hex[:12]}",
        description="Deterministic or stable unified finding ID",
    )
    source_phase: str = Field(..., description="Source phase identifier (e.g. accessibility, technical_seo)")
    source_agent: str = Field(..., description="Source agent name")
    source_finding_id: str = Field(..., description="Original finding ID from source agent")
    source_run_id: str = Field(..., description="Run ID where this finding originated")
    primary_site_id: str = Field(..., description="Canonical origin of target website")
    page_url: str = Field(default="", description="Affected page URL")
    category: str = Field(..., description="Normalized high-level category")
    subcategory: Optional[str] = Field(None, description="Detailed domain subcategory")
    title: str = Field(..., description="Finding title in English")
    title_ar: Optional[str] = Field(None, description="Finding title in Arabic")
    description: str = Field(..., description="Finding description in English")
    description_ar: Optional[str] = Field(None, description="Finding description in Arabic")
    observation_type: str = Field(default="deterministic", description="deterministic, heuristic, or ai_interpretation")
    verification_state: VerificationState = Field(
        default="confirmed_by_evidence",
        description="Rigorous classification of verification certainty",
    )
    original_severity: str = Field(..., description="Unaltered severity rating from original agent")
    normalized_impact_category: NormalizedImpact = Field(
        default="moderate_impairment",
        description="Phase 11 normalized cross-agent impact",
    )
    confidence_category: ConfidenceCategory = Field(default="high", description="Confidence level of the observation")
    evidence_ids: list[str] = Field(default_factory=list, description="Preserved underlying evidence references")
    source_timestamp: Optional[str] = Field(None, description="Timestamp when original finding was recorded")
    related_finding_ids: list[str] = Field(default_factory=list, description="IDs of related findings")
    limitations: Optional[str] = Field(None, description="Limitations of the measurement in English")
    limitations_ar: Optional[str] = Field(None, description="Limitations of the measurement in Arabic")


class DuplicateFindingGroup(BaseModel):
    """Group of findings from different agents representing the same underlying defect."""

    group_id: str = Field(
        default_factory=lambda: f"dupg-{uuid.uuid4().hex[:8]}",
        description="Canonical issue group ID",
    )
    canonical_title: str = Field(..., description="Unified canonical issue title")
    canonical_title_ar: Optional[str] = Field(None, description="Unified canonical issue title in Arabic")
    category: str = Field(..., description="Common category")
    findings: list[UnifiedFinding] = Field(default_factory=list, description="Underlying preserved original findings")
    source_agents: list[str] = Field(default_factory=list, description="List of source agents that detected this")
    affected_pages: list[str] = Field(default_factory=list, description="Unique pages affected")
    all_evidence_ids: list[str] = Field(default_factory=list, description="Combined evidence references")
    deduplication_reason: str = Field(..., description="Justification for grouping these findings")
    deduplication_reason_ar: Optional[str] = Field(None, description="Justification in Arabic")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0, description="Deduplication grouping confidence")


class FindingRelationship(BaseModel):
    """Directed or undirected semantic relationship between two findings or items."""

    relationship_id: str = Field(default_factory=lambda: f"rel-{uuid.uuid4().hex[:8]}")
    source_id: str = Field(..., description="Source finding or item ID")
    target_id: str = Field(..., description="Target finding or item ID")
    relationship_type: RelationshipType = Field(..., description="Type of semantic relationship")
    description: str = Field(..., description="Relationship explanation")
    description_ar: Optional[str] = Field(None, description="Explanation in Arabic")
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    is_candidate: bool = Field(default=False, description="True if hypothetical or candidate relationship")


class ConflictRecord(BaseModel):
    """Documented tradeoff or conflict between recommendations from different domains."""

    conflict_id: str = Field(default_factory=lambda: f"conf-{uuid.uuid4().hex[:8]}")
    conflict_type: ConflictType = Field(..., description="Type of conflicting tradeoff")
    finding_ids: list[str] = Field(default_factory=list, description="Conflicting finding IDs")
    recommendation_ids: list[str] = Field(default_factory=list, description="Conflicting recommendation IDs")
    description: str = Field(..., description="Description of tension in English")
    description_ar: Optional[str] = Field(None, description="Description of tension in Arabic")
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    proposed_resolution: str = Field(..., description="Constructive proposed resolution")
    proposed_resolution_ar: Optional[str] = Field(None, description="Proposed resolution in Arabic")
    resolution_confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    manual_review_required: bool = Field(default=True)
    status: Literal["pending_review", "approved", "rejected", "modified"] = Field(default="pending_review")


class RootCauseCandidate(BaseModel):
    """Pattern-based hypothesis of shared root cause without claiming access to private repo code."""

    cause_id: str = Field(default_factory=lambda: f"rc-{uuid.uuid4().hex[:8]}")
    title: str = Field(..., description="Title of root cause hypothesis")
    title_ar: Optional[str] = Field(None, description="Title in Arabic")
    description: str = Field(..., description="Hypothesized root cause explanation")
    description_ar: Optional[str] = Field(None, description="Explanation in Arabic")
    confidence: RootCauseConfidence = Field(default="possible_candidate")
    related_finding_ids: list[str] = Field(default_factory=list)
    affected_pages: list[str] = Field(default_factory=list)
    shared_pattern: str = Field(..., description="Observed structural or behavioral pattern across findings")
    evidence_ids: list[str] = Field(default_factory=list)


class StrategicOpportunity(BaseModel):
    """High-level improvement opportunity synthesized across multiple agents."""

    opportunity_id: str = Field(default_factory=lambda: f"opp-{uuid.uuid4().hex[:8]}")
    title: str = Field(..., description="Opportunity title")
    title_ar: Optional[str] = Field(None, description="Title in Arabic")
    category: OpportunityCategory = Field(...)
    related_finding_ids: list[str] = Field(default_factory=list)
    affected_pages: list[str] = Field(default_factory=list)
    observed_problem: str = Field(..., description="Summary of underlying observed problem")
    strategic_interpretation: str = Field(..., description="Strategic significance")
    evidence_ids: list[str] = Field(default_factory=list)
    expected_type_of_benefit: str = Field(..., description="Qualitative nature of benefit without invented numbers")
    estimated_effort: Literal["small", "medium", "large", "unknown"] = Field(default="medium")
    impact_confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    limitations: Optional[str] = Field(None)


class PriorityAssessment(BaseModel):
    """Explainable priority assessment calculation details."""

    item_id: str = Field(..., description="Action ID or finding ID being evaluated")
    priority_level: PriorityLevel = Field(..., description="P0, P1, P2, P3")
    composite_score: float = Field(..., ge=0.0, le=100.0, description="Calculated weighted score (0-100)")
    dimension_scores: dict[str, float] = Field(default_factory=dict, description="Component scores across 5 dimensions")
    justification: str = Field(..., description="Explanation of priority assignment")
    justification_ar: Optional[str] = Field(None)
    is_escalated: bool = Field(default=False, description="True if escalated due to safety, legal, or barrier urgency")
    escalation_reason: Optional[str] = Field(None)


class ActionDependency(BaseModel):
    """Dependency link between two roadmap actions."""

    dependency_id: str = Field(default_factory=lambda: f"dep-{uuid.uuid4().hex[:8]}")
    action_id: str = Field(..., description="Dependent action that requires prerequisite")
    depends_on_action_id: str = Field(..., description="Prerequisite action that must be completed first")
    dependency_type: Literal["hard_blocker", "recommended_order"] = Field(default="recommended_order")
    reason: str = Field(..., description="Technical or strategic rationale for sequence")


class RoadmapAction(BaseModel):
    """Concrete, prioritized implementation backlog item."""

    action_id: str = Field(default_factory=lambda: f"act-{uuid.uuid4().hex[:8]}")
    title: str = Field(..., description="Action title in English")
    title_ar: Optional[str] = Field(None, description="Action title in Arabic")
    description: str = Field(..., description="Actionable execution description in English")
    description_ar: Optional[str] = Field(None, description="Actionable execution description in Arabic")
    category: str = Field(..., description="Workstream or category")
    priority: PriorityLevel = Field(default="P2", description="Assigned priority tier")
    wave_number: int = Field(default=2, ge=1, le=4, description="Execution wave (1 to 4)")
    related_finding_ids: list[str] = Field(default_factory=list)
    related_recommendation_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    affected_pages: list[str] = Field(default_factory=list)
    suggested_owner_role: ActionOwnerRole = Field(default="Frontend Developer")
    estimated_effort: Literal["small", "medium", "large", "unknown"] = Field(default="medium")
    impact_category: Union[NormalizedImpact, Literal["very_high", "high", "medium", "low", "unknown"], str] = Field(
        default="moderate_impairment"
    )
    confidence: float = Field(default=0.85, ge=0.0, le=1.0)
    dependencies: list[str] = Field(default_factory=list, description="IDs of actions that block this action")
    acceptance_criteria: list[str] = Field(default_factory=list, description="Objective acceptance checklist")
    acceptance_criteria_ar: list[str] = Field(default_factory=list)
    verification_method: str = Field(..., description="Concrete method to verify post-implementation")
    verification_method_ar: Optional[str] = Field(None)
    status: ActionStatus = Field(default="proposed", description="Current execution tracking state")
    reviewer_notes: Optional[str] = Field(None, description="Human reviewer or operator audit notes")
    updated_at: Optional[str] = Field(None, description="ISO timestamp of last status update")


class RoadmapWave(BaseModel):
    """Conceptual execution wave grouping actions in logical order without fabricated calendar dates."""

    wave_number: int = Field(..., ge=1, le=4)
    name: str = Field(..., description="Wave title in English")
    name_ar: str = Field(..., description="Wave title in Arabic")
    description: str = Field(..., description="Focus description in English")
    description_ar: str = Field(..., description="Focus description in Arabic")
    actions: list[RoadmapAction] = Field(default_factory=list)
    action_count: int = Field(default=0)


class VerificationPlan(BaseModel):
    """Verification protocol for an implementation action."""

    plan_id: str = Field(default_factory=lambda: f"ver-{uuid.uuid4().hex[:8]}")
    action_id: str = Field(...)
    domain: str = Field(...)
    method: str = Field(..., description="e.g. automated_retest, browser_measurement, manual_assistive_check")
    steps: list[str] = Field(default_factory=list)
    state: Literal[
        "not_scheduled",
        "ready_for_verification",
        "verification_in_progress",
        "verified",
        "verification_failed",
        "unable_to_verify",
    ] = Field(default="not_scheduled")
    verification_evidence_ids: list[str] = Field(default_factory=list)


class MeasurementPlan(BaseModel):
    """Measurable metric recommendation preserving null baselines when real data is absent."""

    metric_id: str = Field(default_factory=lambda: f"met-{uuid.uuid4().hex[:8]}")
    name: str = Field(..., description="Metric name in English")
    name_ar: str = Field(..., description="Metric name in Arabic")
    purpose: str = Field(..., description="Objective of measurement")
    data_source: str = Field(..., description="Source of ground-truth measurement")
    baseline_value: Optional[float] = Field(None, description="Historical baseline if known; None if unmeasured")
    baseline_status: Literal["available", "null_baseline", "unsupported"] = Field(default="null_baseline")
    target_value: Optional[float] = Field(None, description="Desired target; None if user has not set target")
    target_status: Literal["user_configured", "provisional", "not_set"] = Field(default="not_set")
    measurement_method: str = Field(...)
    measurement_frequency: str = Field(default="after_each_release")
    limitations: str = Field(..., description="Limitations or caveats regarding causality")


class HumanReviewTask(BaseModel):
    """Structured task requiring human cognitive or business decision."""

    review_id: str = Field(default_factory=lambda: f"hr-{uuid.uuid4().hex[:8]}")
    related_item_ids: list[str] = Field(default_factory=list)
    review_reason: str = Field(...)
    review_reason_ar: str = Field(...)
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    question_for_reviewer: str = Field(...)
    question_for_reviewer_ar: str = Field(...)
    recommended_options: list[str] = Field(default_factory=list)
    status: Literal["pending", "approved", "rejected", "needs_more_evidence", "resolved"] = Field(default="pending")
    reviewer_record: Optional[dict[str, Any]] = Field(None)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reviewed_at: Optional[str] = Field(None)


class AgentCoverageRecord(BaseModel):
    """Audit coverage metadata for an individual source agent."""

    agent_id: str = Field(...)
    agent_name: str = Field(...)
    status: Literal["completed", "partial", "unavailable", "blocked", "awaiting_review"] = Field(default="unavailable")
    run_id: Optional[str] = Field(None)
    findings_count: int = Field(default=0)
    pages_inspected: int = Field(default=0)
    has_ai_interpretation: bool = Field(default=False)
    limitations: Optional[str] = Field(None)


class SourceCoverageAssessment(BaseModel):
    """Overall multi-agent evidence coverage audit."""

    total_potential_agents: int = Field(default=7, description="Phases 04 through 10")
    available_agents: list[str] = Field(default_factory=list)
    partial_agents: list[str] = Field(default_factory=list)
    missing_agents: list[str] = Field(default_factory=list)
    coverage_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    agent_records: list[AgentCoverageRecord] = Field(default_factory=list)
    total_pages_covered: int = Field(default=0)
    data_freshness_timestamp: Optional[str] = Field(None)


class StrategicStatistics(BaseModel):
    """Aggregated metrics and distributions for the roadmap."""

    source_coverage_percent: float = Field(default=0.0)
    total_raw_findings: int = Field(default=0)
    unified_findings_count: int = Field(default=0)
    duplicate_groups_count: int = Field(default=0)
    conflicts_count: int = Field(default=0)
    root_cause_candidates_count: int = Field(default=0)
    strategic_opportunities_count: int = Field(default=0)
    actions_count: int = Field(default=0)
    actions_by_priority: dict[str, int] = Field(default_factory=dict)
    actions_by_wave: dict[str, int] = Field(default_factory=dict)
    manual_reviews_count: int = Field(default=0)
    verified_actions_count: int = Field(default=0)
    strategic_index: Optional[float] = Field(default=None, description="Unified Strategic Health Index (0-100)")
    index_label_ar: Optional[str] = Field(default=None, description="Index quality label in Arabic")


class StrategicAnalysisRequest(BaseModel):
    """Request payload to trigger Phase 11 Strategic Intelligence analysis."""

    crawl_run_id: str = Field(..., description="Primary crawl run ID representing the target website")
    source_run_ids: Optional[Union[dict[str, str], list[str]]] = Field(
        None,
        description="Optional mapping of source phase to specific run ID (Mode B) or list of run IDs",
    )
    language: str = Field(default="ar", description="Language of generated report ('ar' or 'en')")
    max_actions: int = Field(default=50, ge=5, le=200, description="Maximum actions in backlog")
    include_partial_agents: bool = Field(default=True, description="Synthesize available agents even if some missing")
    deterministic_only: bool = Field(default=False, description="Run deterministic cross-agent synthesis only")
    save_results: bool = Field(default=True, description="Persist analysis artifacts to disk")

    @field_validator("source_run_ids", mode="before")
    @classmethod
    def normalize_source_run_ids(cls, v: Any) -> Optional[dict[str, str]]:
        if v is None:
            return None
        if isinstance(v, list):
            return {f"custom_run_{i}": str(item) for i, item in enumerate(v)}
        if isinstance(v, dict):
            return {str(k): str(val) for k, val in v.items()}
        return None


class StrategicIntelligenceReport(BaseModel):
    """Comprehensive Strategic Intelligence & Unified Action Roadmap Report."""

    strategic_run_id: str = Field(
        default_factory=lambda: f"strat-{uuid.uuid4().hex[:12]}",
        description="Unique strategic synthesis run ID",
    )
    crawl_run_id: str = Field(...)
    target_url: str = Field(...)
    canonical_origin: str = Field(...)
    analysis_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    model_name: str = Field(default="gemini-3.6-flash", description="Official model: strictly gemini-3.6-flash")
    ai_status: Literal["completed", "deterministic_fallback", "quota_blocked", "offline_mode"] = Field(
        default="deterministic_fallback"
    )
    coverage: SourceCoverageAssessment = Field(...)
    statistics: StrategicStatistics = Field(...)
    unified_findings: list[UnifiedFinding] = Field(default_factory=list)
    duplicate_groups: list[DuplicateFindingGroup] = Field(default_factory=list)
    relationships: list[FindingRelationship] = Field(default_factory=list)
    conflicts: list[ConflictRecord] = Field(default_factory=list)
    root_cause_candidates: list[RootCauseCandidate] = Field(default_factory=list)
    opportunities: list[StrategicOpportunity] = Field(default_factory=list)
    actions: list[RoadmapAction] = Field(default_factory=list)
    waves: list[RoadmapWave] = Field(default_factory=list)
    verification_plans: list[VerificationPlan] = Field(default_factory=list)
    measurement_plans: list[MeasurementPlan] = Field(default_factory=list)
    manual_reviews: list[HumanReviewTask] = Field(default_factory=list)
    report_markdown: str = Field(default="")
    executive_summary_markdown: str = Field(default="")

    @property
    def analysis_status(self) -> str:
        return "blocked_ai" if self.ai_status == "quota_blocked" else "completed"
