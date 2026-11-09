"""Pydantic schemas for Site DNA Phase 12 — Final Reporting & Enterprise PDF Export."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional
import uuid

from pydantic import BaseModel, Field, model_validator

ReportMode = Literal["executive", "comprehensive", "agent"]
ReportLanguage = Literal["ar", "en"]
ReportPaperSize = Literal["A4", "Letter"]
ReportStatus = Literal[
    "completed",
    "partial",
    "ai_blocked",
    "source_missing",
    "validation_failed",
    "generation_failed",
]


class ReportProvenance(BaseModel):
    """Provenance tracking for a source analysis stage."""

    stage_id: str = Field(..., description="Stage identifier (e.g. technical_seo)")
    agent_id: str = Field(..., description="Agent or engine that produced the artifact")
    source_run_id: str = Field(..., description="ID of source execution")
    artifact_path: str = Field(..., description="Path to analysis artifact")
    artifact_sha256: str = Field(..., description="SHA-256 content checksum")
    captured_at: Optional[str] = Field(None, description="ISO timestamp of collection")
    status: str = Field(default="completed", description="Execution status of source")

    @property
    def sha256_hash(self) -> str:
        return self.artifact_sha256



class ReportFindingItem(BaseModel):
    """Normalized finding item for unified reporting."""

    finding_id: str = Field(..., description="Unique finding ID")
    canonical_id: Optional[str] = Field(None, description="Unified finding ID if deduplicated")
    title: str = Field(...)
    title_ar: Optional[str] = Field(None)
    description: str = Field(...)
    description_ar: Optional[str] = Field(None)
    domain: str = Field(default="general")
    severity: Literal["critical", "high", "medium", "low", "info"] = Field(default="medium")
    source_agent: str = Field(default="unknown")
    evidence_ids: list[str] = Field(default_factory=list)
    affected_urls: list[str] = Field(default_factory=list)
    remediation_strategy: Optional[str] = Field(default=None)


class ReportRecommendationItem(BaseModel):
    """Prioritized recommendation item for reporting."""

    action_id: str = Field(...)
    title: str = Field(...)
    title_ar: Optional[str] = Field(None)
    description: str = Field(...)
    description_ar: Optional[str] = Field(None)
    priority: Literal["P0", "P1", "P2", "P3"] = Field(default="P1")
    wave_number: int = Field(default=1)
    owner_role: str = Field(default="Engineer")
    effort: str = Field(default="medium")
    impact: str = Field(default="high")
    status: str = Field(default="proposed")
    verification_method: Optional[str] = Field(None)
    verification_method_ar: Optional[str] = Field(None)


class ReportRoadmapWaveItem(BaseModel):
    """Wave sequencing structure in final report."""

    wave_number: int
    name: str
    name_ar: str
    timeframe: str
    description: str
    description_ar: Optional[str] = None
    actions: list[ReportRecommendationItem] = Field(default_factory=list)


class ReportEvidenceItem(BaseModel):
    """Indexed evidence entry linking findings to verifiable technical data."""

    evidence_id: str
    source_agent: str
    observation_type: str
    target_url: str
    capture_date: Optional[str] = None
    details: dict[str, Any] = Field(default_factory=dict)


class FinalReportRequest(BaseModel):
    """Request payload for POST /api/v1/reports/final and CLI."""

    crawl_run_id: Optional[str] = Field(None, description="Completed crawl run ID")
    analysis_run_id: Optional[str] = Field(None, description="Alias for crawl_run_id")
    mode: ReportMode = Field(default="comprehensive", description="Report mode")
    language: ReportLanguage = Field(default="ar", description="Document language")
    paper_size: ReportPaperSize = Field(default="A4", description="Print paper size")
    target_agent: Optional[str] = Field(None, description="Target agent if mode is 'agent'")
    include_screenshots: bool = Field(default=True, description="Embed screenshots in PDF")
    include_evidence_catalog: bool = Field(default=True, description="Include detailed evidence catalog")
    validate_pdf: bool = Field(default=True, description="Run automated 20-point quality verification")
    deterministic_only: bool = Field(default=False, description="Run only deterministic analyzers without AI")
    regenerate: bool = Field(default=False, description="Force regeneration if exists")

    @model_validator(mode="before")
    @classmethod
    def reconcile_run_id(cls, values: Any) -> Any:
        if isinstance(values, dict):
            c_id = values.get("crawl_run_id") or values.get("analysis_run_id")
            if not c_id:
                raise ValueError("Either 'crawl_run_id' or 'analysis_run_id' must be provided.")
            values["crawl_run_id"] = c_id
            values["analysis_run_id"] = c_id
        return values


class FinalReportMetadata(BaseModel):
    """Summary metadata record for a generated final report."""

    report_id: str = Field(default_factory=lambda: f"rep-{uuid.uuid4().hex[:12]}")
    report_version: str = Field(default="v1.0.0")
    target_url: str = Field(...)
    crawl_run_id: str = Field(...)
    mode: ReportMode = Field(...)
    language: ReportLanguage = Field(default="ar")
    paper_size: ReportPaperSize = Field(default="A4")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: ReportStatus = Field(...)
    overall_score: Optional[float] = Field(None, description="Overall health / strategic score out of 100")
    page_count: int = Field(default=0)
    pdf_size_bytes: int = Field(default=0)
    sha256_checksum: str = Field(default="")
    available_agents_count: int = Field(default=0)
    total_findings_count: int = Field(default=0)
    critical_findings_count: int = Field(default=0)
    total_actions_count: int = Field(default=0)
    pdf_path: Optional[str] = Field(None)
    html_path: Optional[str] = Field(None)
    markdown_path: Optional[str] = Field(None)
    json_path: Optional[str] = Field(None)

    @property
    def analysis_run_id(self) -> str:
        return self.crawl_run_id

    @property
    def total_findings(self) -> int:
        return self.total_findings_count

    @property
    def total_recommendations(self) -> int:
        return self.total_actions_count

    @property
    def validation_passed(self) -> bool:
        return bool(self.sha256_checksum and self.pdf_size_bytes > 0)

    @property
    def artifacts(self) -> Any:
        class _Artifacts:
            def __init__(self, pdf: Optional[str], html: Optional[str], md: Optional[str], js: Optional[str]):
                self.pdf = pdf
                self.html = html
                self.markdown = md
                self.json_data = js
        return _Artifacts(self.pdf_path, self.html_path, self.markdown_path, self.json_path)


class FinalReportContext(BaseModel):
    """Complete canonical data context for report templates, JSON, and PDF generation."""

    report_id: str = Field(default_factory=lambda: f"rep-{uuid.uuid4().hex[:12]}")
    report_version: str = Field(default="v1.0.0")
    target_url: str
    crawl_run_id: str
    mode: ReportMode
    language: ReportLanguage = "ar"
    paper_size: ReportPaperSize = "A4"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    status: ReportStatus = "completed"

    # Executive narrative
    executive_summary_md: str = ""
    executive_summary_ar: str = ""
    key_conclusions: list[str] = Field(default_factory=list)

    # Multi-agent coverage and health
    coverage: dict[str, Any] = Field(default_factory=dict)
    scores: dict[str, float] = Field(default_factory=dict)
    strategic_index: Optional[float] = None
    strategic_label_ar: Optional[str] = None

    # Granular data
    findings: list[ReportFindingItem] = Field(default_factory=list)
    critical_issues: list[ReportFindingItem] = Field(default_factory=list)
    recommendations: list[ReportRecommendationItem] = Field(default_factory=list)
    roadmap_waves: list[ReportRoadmapWaveItem] = Field(default_factory=list)
    evidence_catalog: list[ReportEvidenceItem] = Field(default_factory=list)
    source_manifest: list[ReportProvenance] = Field(default_factory=list)

    # Transparent disclosures & limitations
    limitations: list[str] = Field(default_factory=list)
    missing_stages: list[str] = Field(default_factory=list)
    ai_status_notice: Optional[str] = None

    # Visual screenshots
    desktop_screenshot_b64: Optional[str] = None
    mobile_screenshot_b64: Optional[str] = None

    # Deep structured domain audit deliverables
    domain_audits: dict[str, Any] = Field(default_factory=dict)
