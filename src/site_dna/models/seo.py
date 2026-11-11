"""SEO analysis model defined for Phase 7."""

from typing import Any, Literal

from pydantic import BaseModel, Field

from site_dna.models.common import CheckStatus


class CheckRecord(BaseModel):
    """Single SEO rule result, scoped to a page or the whole site."""

    id: str
    scope: Literal["page", "site"]
    url: str | None = None
    status: CheckStatus
    value: Any = None
    message: str | None = None
    threshold: Any = None
    confidence: Literal["high", "medium"] | None = None


class SeoIssue(BaseModel):
    """Flat actionable issue extracted from failed or warning checks."""

    id: str
    url: str | None = None
    message: str | None = None
    confidence: Literal["high", "medium"] | None = None


class SeoSummary(BaseModel):
    """Counts of check statuses for the SEO module."""

    passed: int = 0
    warning: int = 0
    failed: int = 0
    not_available: int = 0


class SeoAnalysis(BaseModel):
    """Complete SEO analysis output."""

    checks: list[CheckRecord] = Field(default_factory=list)
    issues: list[SeoIssue] = Field(default_factory=list)
    summary: SeoSummary = Field(default_factory=SeoSummary)
