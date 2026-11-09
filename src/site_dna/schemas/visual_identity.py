"""Pydantic schemas for Site DNA Phase 04 AI Visual Identity Analysis."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

AnalysisStatus = Literal["completed", "partial", "ai_blocked", "failed", "cancelled", "blocked"]
FindingSeverity = Literal["critical", "high", "medium", "low", "informational"]
FindingConfidence = Literal["confirmed_by_measurement", "high_confidence_ai", "hypothesized", "uncertain"]
ObservationType = Literal["observed_measurement", "derived_calculation", "ai_interpretation"]
RecommendationEffort = Literal["small", "medium", "large"]
RecommendationImpact = Literal["high", "medium", "low"]
RecommendationPriority = Literal["P1", "P2", "P3"]
ScoreStatus = Literal["assessed", "not_assessed", "insufficient_evidence"]


class VisualIdentityAnalysisRequest(BaseModel):
    """Input payload to trigger AI visual identity analysis."""

    visual_run_id: Optional[str] = Field(
        default=None, description="Existing visual run identifier (e.g. vis-e6b6128de9b5)"
    )
    visual_manifest_file: Optional[str] = Field(default=None, description="Path to visual manifest.json")
    crawl_run_id: Optional[str] = Field(default=None, description="Optional associated crawl run identifier")
    language: str = Field(default="ar", description="Language for generated report ('ar' or 'en')")
    max_pages: int = Field(default=8, ge=1, le=50, description="Maximum pages to include in visual identity analysis")
    max_images: Optional[int] = Field(
        default=None, ge=1, le=30, description="Maximum screenshots to inspect with vision"
    )
    save_results: bool = Field(default=True, description="Whether to save analysis artifacts to disk")


class VisualEvidenceReference(BaseModel):
    """Traceable pointer to an underlying Phase 03 visual or Phase 02 crawl evidence record."""

    evidence_id: str
    evidence_category: str
    field_reference: str
    page_url: str
    viewport_profile: str
    screenshot_reference: Optional[str] = None
    checksum: Optional[str] = None


class VisualObservation(BaseModel):
    """Granular observation combining measured properties, derived metrics, and AI observations."""

    observation_id: str = Field(default_factory=lambda: f"OBS-{uuid4().hex[:8]}")
    category: str = Field(description="color, typography, hierarchy, consistency, responsive, branding, contrast")
    page_url: str
    viewport_profile: str = "desktop"
    observation_type: ObservationType = "observed_measurement"
    field_reference: str
    observed_value: Any
    description: str
    evidence_ids: list[str] = Field(default_factory=list)


class VisualFinding(BaseModel):
    """Structured, evidence-backed visual finding or issue identified during analysis."""

    finding_id: str = Field(description="Unique finding identifier (e.g. FIND-01)")
    title: str
    category: str = Field(
        description="color, typography, visual_hierarchy, spacing, alignment, component_consistency, branding, responsive_visual, contrast, other"
    )
    severity: FindingSeverity = "medium"
    confidence: FindingConfidence = "high_confidence_ai"
    finding_type: ObservationType = "ai_interpretation"
    page_url: str
    viewport_profile: str = "desktop"
    description: str
    potential_impact: str = ""
    suggested_action: str = ""
    element_references: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    is_validated: bool = True
    rejection_reason: Optional[str] = None


class VisualRecommendation(BaseModel):
    """Actionable, prioritized design improvement directly addressing validated findings."""

    recommendation_id: str = Field(description="Unique recommendation identifier (e.g. REC-01)")
    related_finding_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    title: str
    problem_statement: str
    proposed_correction: str
    affected_page_or_component: str
    expected_visual_improvement: str
    estimated_effort: RecommendationEffort = "medium"
    expected_impact: RecommendationImpact = "medium"
    priority: RecommendationPriority = "P2"


class VisualScoreExplanation(BaseModel):
    """Transparent explanation and score for a specific visual identity dimension."""

    dimension_name: str
    weight: float = Field(ge=0.0, le=1.0)
    score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    status: ScoreStatus = "assessed"
    explanation: str
    key_positive_factors: list[str] = Field(default_factory=list)
    key_negative_factors: list[str] = Field(default_factory=list)
    supporting_finding_ids: list[str] = Field(default_factory=list)


class VisualCategoryAssessment(BaseModel):
    """Detailed visual assessment across core brand design pillars."""

    color_palette_assessment: dict[str, Any] = Field(default_factory=dict)
    typography_scale_assessment: dict[str, Any] = Field(default_factory=dict)
    visual_hierarchy_assessment: dict[str, Any] = Field(default_factory=dict)
    cross_page_consistency_assessment: dict[str, Any] = Field(default_factory=dict)
    responsive_visual_assessment: dict[str, Any] = Field(default_factory=dict)
    business_context_alignment: dict[str, Any] = Field(default_factory=dict)


class VisualAnalysisStatistics(BaseModel):
    """Quantitative execution statistics for the visual analysis run."""

    pages_analyzed: int = 0
    viewports_analyzed: int = 0
    screenshots_processed: int = 0
    total_findings: int = 0
    validated_findings: int = 0
    rejected_findings: int = 0
    recommendations_count: int = 0
    duration_ms: float = 0.0
    model_name: str = "gemini-3.6-flash"
    tokens_used: Optional[dict[str, int]] = None
    ai_analysis_completed: bool = True
    from_cache: bool = False
    quota_exhausted: bool = False


class VisualIdentityReport(BaseModel):
    """Comprehensive visual identity analysis report output."""

    schema_version: str = "1.0"
    analysis_run_id: str = Field(default_factory=lambda: f"vi-{uuid4().hex[:12]}")
    crawl_run_id: str
    visual_run_id: str
    site_url: str
    model_name: str = "gemini-3.6-flash"
    analysis_status: AnalysisStatus = "completed"
    ai_analysis_completed: bool = True
    deterministic_analysis_completed: bool = True
    fallback_reason: Optional[str] = None
    from_cache: bool = False
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    summary_arabic: str
    summary_english: str
    overall_score: Optional[float] = None
    score_explanations: list[VisualScoreExplanation] = Field(default_factory=list)
    category_assessment: VisualCategoryAssessment = Field(default_factory=VisualCategoryAssessment)

    findings: list[VisualFinding] = Field(default_factory=list)
    rejected_findings: list[VisualFinding] = Field(default_factory=list)
    recommendations: list[VisualRecommendation] = Field(default_factory=list)
    evidence_index: list[VisualEvidenceReference] = Field(default_factory=list)
    limitations_arabic: list[str] = Field(default_factory=list)
    statistics: VisualAnalysisStatistics = Field(default_factory=VisualAnalysisStatistics)

    report_markdown_path: Optional[str] = None
    analysis_json_path: Optional[str] = None
