"""Pydantic schemas for Site DNA Agent Registry, Run Orchestration & Dashboard."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class AgentRegistryItem(BaseModel):
    """Metadata describing a single analysis agent (Phases 01-12)."""

    id: str
    phase: int
    name: str
    name_ar: str
    description: str
    description_ar: str
    icon: str
    category: str
    implementation_status: Literal["implemented", "planned", "disabled"]
    runtime_availability: Literal[
        "ready", "running", "completed", "partial", "ai_blocked", "failed", "unavailable", "not_implemented"
    ]
    can_execute: bool = False
    requires_visual: bool = False
    dependencies: list[str] = Field(default_factory=list)
    output_types: list[str] = Field(default_factory=list)
    display_order: int = 0
    model_name: str = "gemini-3.6-flash"


class RunSubmissionRequest(BaseModel):
    """User request to initiate an analysis run with selective agent stages."""

    url: str = Field(..., description="Target website URL to analyze")
    stages: list[str] = Field(
        default_factory=lambda: [
            "discovery",
            "visual_capture",
            "visual_identity",
            "ux_ui",
            "content_marketing",
            "technical_seo",
        ],
        description="List of selected stage IDs to execute",
    )
    max_pages: int = Field(default=5, ge=1, le=20, description="Maximum crawl depth/pages")
    offline_mode: bool = Field(default=False, description="Run in offline mode without external AI requests")
    deterministic_only: bool = Field(
        default=False, description="Skip AI interpretation and produce deterministic output"
    )
    competitor_urls: list[str] = Field(
        default_factory=list, description="Optional competitor URLs for Phase 08 Competitor Intelligence"
    )


class StageExecutionRecord(BaseModel):
    """Execution status and metric summary for a single analysis stage."""

    stage_id: str
    name: str
    name_ar: str
    status: Literal["pending", "queued", "running", "completed", "partial", "ai_blocked", "failed", "skipped"] = (
        "pending"
    )
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_ms: float = 0.0
    score: Optional[float] = None
    findings_count: int = 0
    recommendations_count: int = 0
    error_message: Optional[str] = None
    output_path: Optional[str] = None
    analysis_run_id: Optional[str] = None


class RunRecord(BaseModel):
    """Comprehensive persistent record for a website analysis run."""

    run_id: str
    url: str
    canonical_origin: Optional[str] = None
    status: Literal["created", "queued", "running", "completed", "partial", "ai_blocked", "failed", "cancelled"] = (
        "created"
    )
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    total_duration_ms: float = 0.0
    stages: dict[str, StageExecutionRecord] = Field(default_factory=dict)
    visual_run_id: Optional[str] = None
    scores: dict[str, float] = Field(default_factory=dict)
    overall_score: Optional[float] = None
    total_findings: int = 0
    total_recommendations: int = 0
    error_message: Optional[str] = None


class RunEvent(BaseModel):
    """Structured operational event emitted during analysis execution."""

    event_id: str
    run_id: str
    stage_id: Optional[str] = None
    event_type: Literal[
        "run.created",
        "run.started",
        "stage.queued",
        "stage.started",
        "stage.progress",
        "stage.completed",
        "stage.partial",
        "stage.ai_blocked",
        "stage.failed",
        "run.completed",
        "run.partial",
        "run.failed",
    ]
    message: str
    message_ar: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data: dict[str, Any] = Field(default_factory=dict)


class DashboardSummary(BaseModel):
    """Aggregated dashboard telemetry and historical metrics."""

    total_runs: int = 0
    completed_runs: int = 0
    running_runs: int = 0
    failed_runs: int = 0
    total_findings: int = 0
    total_recommendations: int = 0
    recent_runs: list[dict[str, Any]] = Field(default_factory=list)
    agent_readiness: dict[str, Any] = Field(default_factory=dict)
