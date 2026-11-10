"""PageSpeed Insights model defined for Phase 6."""

from typing import Literal

from pydantic import BaseModel, Field

from site_dna.models.common import ModuleStatus


class LabMetrics(BaseModel):
    """Lighthouse lab metrics."""

    lcp_ms: float | None = None
    fcp_ms: float | None = None
    speed_index_ms: float | None = None
    tbt_ms: float | None = None
    cls: float | None = None


class FieldMetric(BaseModel):
    """CrUX field metric percentile and rating category."""

    percentile: float | None = None
    category: str | None = None


class FieldMetrics(BaseModel):
    """CrUX field data for the URL or, as fallback, the origin."""

    lcp: FieldMetric | None = None
    inp: FieldMetric | None = None
    cls: FieldMetric | None = None
    source: Literal["crux_url", "crux_origin"] | None = None


class Opportunity(BaseModel):
    """Lighthouse opportunity with estimated savings."""

    id: str
    title: str | None = None
    description: str | None = None
    savings_ms: float | None = None
    savings_bytes: float | None = None


class Diagnostic(BaseModel):
    """Lighthouse diagnostic or informative audit."""

    id: str
    title: str | None = None
    score: float | None = None
    display_value: str | None = None
    description: str | None = None


class StrategyPerformance(BaseModel):
    """Performance result for one PSI strategy (mobile or desktop)."""

    status: ModuleStatus
    reason: str | None = None
    score: int | None = None
    lab: LabMetrics = Field(default_factory=LabMetrics)
    field: FieldMetrics = Field(default_factory=FieldMetrics)
    opportunities: list[Opportunity] = Field(default_factory=list)
    diagnostics: list[Diagnostic] = Field(default_factory=list)
    lighthouse_version: str | None = None


class Performance(BaseModel):
    """Combined mobile and desktop performance results."""

    mobile: StrategyPerformance
    desktop: StrategyPerformance
    notes: list[str] = Field(default_factory=list)
