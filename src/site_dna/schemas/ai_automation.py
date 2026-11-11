"""Pydantic schemas for AI & Automation Readiness Analysis (Site DNA)."""

from typing import Literal

from pydantic import BaseModel, Field


class AIDetectedEvidence(BaseModel):
    """Specific observable evidence of AI / chatbot / automation."""
    category: Literal["widget", "script", "meta", "content", "framework", "ui", "api", "asset"] = Field(
        ..., description="Category of observable indicator"
    )
    indicator: str = Field(..., description="Name of indicator or library detected")
    source: str = Field(..., description="File, URL or snippet where evidence was observed")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence in observation")


class AIProposal(BaseModel):
    """Actionable recommendation for adopting or optimizing AI / Agents / Automation."""
    id: str = Field(..., description="Unique proposal identifier, e.g. AIP-01")
    title: str = Field(..., description="Proposal title in English")
    title_ar: str = Field(..., description="Proposal title in Arabic")
    type: Literal[
        "chatbot",
        "agent",
        "semantic_search",
        "workflow_automation",
        "multimodal_upgrade",
        "context_memory",
        "guardrails",
        "observability",
    ] = Field(..., description="Functional nature of the AI proposal")
    priority: Literal["P1", "P2", "P3"] = Field(default="P1", description="Execution priority")
    expected_impact: Literal["critical", "high", "medium"] = Field(default="high")
    description: str = Field(..., description="Detailed description in English")
    description_ar: str = Field(..., description="Detailed description in Arabic")
    problem_addressed_ar: str = Field(default="", description="The exact bottleneck or gap being resolved")
    recommended_technologies: list[str] = Field(
        default_factory=list, description="Recommended models, APIs, and frameworks"
    )
    implementation_steps: list[str] = Field(
        default_factory=list, description="Step-by-step practical implementation guidance"
    )


class AIAutomationReport(BaseModel):
    """Comprehensive AI & Automation audit report for a target website."""
    run_id: str = Field(..., description="Analysis run ID")
    target_url: str = Field(..., description="Primary website URL")
    status: Literal["present", "partial", "absent"] = Field(
        ..., description="Current status of AI employment in the website"
    )
    maturity_score: float = Field(
        ..., ge=0.0, le=100.0, description="AI Readiness & Maturity Score (0-100)"
    )
    headline_ar: str = Field(..., description="High-level diagnostic headline in Arabic")
    headline_en: str = Field(..., description="High-level diagnostic headline in English")
    summary_ar: str = Field(..., description="Executive narrative summary in Arabic")
    summary_en: str = Field(..., description="Executive narrative summary in English")
    has_chatbot: bool = Field(default=False, description="Whether an active conversational chatbot is detected")
    has_agent: bool = Field(default=False, description="Whether autonomous AI agents/tools are detected")
    has_semantic_search: bool = Field(default=False, description="Whether semantic/AI search is detected")
    detected_evidences: list[AIDetectedEvidence] = Field(default_factory=list)
    proposals: list[AIProposal] = Field(default_factory=list)
    created_at: str = Field(...)
