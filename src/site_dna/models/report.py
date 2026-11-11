"""Top-level report model defined for Phase 8 and produced by the pipeline."""

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field

from site_dna.models.common import ModuleError, ModuleResult
from site_dna.models.page import PageData
from site_dna.models.performance import Performance
from site_dna.models.seo import SeoAnalysis
from site_dna.models.visual import VisualIdentity


class ProjectInfo(BaseModel):
    """Scan metadata describing the requested and final target."""

    input_url: str
    final_url: str | None = None
    domain: str | None = None
    scan_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    scan_status: Literal["completed", "partial", "failed", "rejected"]
    processing_time_seconds: float = 0.0
    permission_attested: bool
    tool_version: str
    config: dict[str, Any] = Field(default_factory=dict)


class WebsiteContent(BaseModel):
    """Content and structure data for all crawled pages."""

    pages: list[PageData] = Field(default_factory=list)
    total_pages: int = 0
    total_words: int = 0
    pages_failed: int = 0


class ExecutionSummary(BaseModel):
    """Aggregated module outcomes, warnings, errors, and timings."""

    module_results: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    errors: list[ModuleError] = Field(default_factory=list)
    timings: dict[str, float] = Field(default_factory=dict)


class Report(BaseModel):
    """Single schema-valid report for one website scan."""

    schema_version: Literal["1.0"] = "1.0"
    scan_id: str
    project_info: ProjectInfo
    website_content: ModuleResult[WebsiteContent]
    visual_identity: ModuleResult[VisualIdentity]
    performance: ModuleResult[Performance]
    seo_analysis: ModuleResult[SeoAnalysis]
    execution_summary: ExecutionSummary = Field(default_factory=ExecutionSummary)
