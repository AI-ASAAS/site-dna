"""Health, readiness, and verification schemas for Site DNA."""

from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Basic health check response schema."""

    status: str = Field(default="ok", description="Overall service status")
    service: str = Field(default="site-dna", description="Service identifier")
    version: str = Field(default="0.1.0", description="Software version")
    phase: str = Field(default="01", description="Project development phase")


class ReadinessCheckDetails(BaseModel):
    """Subsystem readiness details."""

    backend_running: bool = Field(default=True, description="Backend application is online")
    api_key_configured: bool = Field(..., description="Gemini API key is configured")
    model_configured: str = Field(..., description="Target Gemini model name")
    live_connectivity_verified: bool = Field(
        default=False,
        description="Indicates whether live connectivity has been actively verified",
    )
    environment: str = Field(..., description="Current running environment")


class ReadinessResponse(BaseModel):
    """Readiness probe response schema."""

    status: str = Field(..., description="Overall readiness: 'ready' or 'unready'")
    service: str = Field(default="site-dna", description="Service identifier")
    version: str = Field(default="0.1.0", description="Software version")
    ready: bool = Field(..., description="True if service is ready to execute tasks")
    details: ReadinessCheckDetails = Field(..., description="Component readiness details")
    message: Optional[str] = Field(default=None, description="Diagnostic commentary or instructions")


class SmokeAgentOutput(BaseModel):
    """Structured output expected from the Foundation Smoke Agent."""

    project: str = Field(
        default="Site DNA",
        description="Project name confirmed by model",
    )
    status: str = Field(
        default="operational",
        description="Operational status",
    )
    message: str = Field(
        default="CrewAI Gemini integration successful",
        description="Confirmation message",
    )
