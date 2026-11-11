"""Phase 1-9 report models (single source of truth for the JSON report)."""

from site_dna.models.common import (
    CheckStatus,
    FileRef,
    ModuleError,
    ModuleResult,
    ModuleStatus,
)
from site_dna.models.page import (
    HeadingLists,
    HeadingOutlineItem,
    ImageItem,
    LinkItem,
    PageData,
)
from site_dna.models.performance import (
    Diagnostic,
    FieldMetric,
    FieldMetrics,
    LabMetrics,
    Opportunity,
    Performance,
    StrategyPerformance,
)
from site_dna.models.report import (
    ExecutionSummary,
    ProjectInfo,
    Report,
    WebsiteContent,
)
from site_dna.models.seo import (
    CheckRecord,
    SeoAnalysis,
    SeoIssue,
    SeoSummary,
)
from site_dna.models.visual import (
    ColorRecord,
    ColorRoleRecord,
    ColorRoles,
    ColorsAnalysis,
    ColorUsage,
    FontFamilyRecord,
    HeadingStyle,
    ScreenshotResult,
    ScreenshotViewport,
    TypographyAnalysis,
    VisualIdentity,
)

__all__ = [
    "CheckRecord",
    "CheckStatus",
    "ColorRecord",
    "ColorRoleRecord",
    "ColorRoles",
    "ColorsAnalysis",
    "ColorUsage",
    "Diagnostic",
    "ExecutionSummary",
    "FieldMetric",
    "FieldMetrics",
    "FileRef",
    "FontFamilyRecord",
    "HeadingLists",
    "HeadingOutlineItem",
    "HeadingStyle",
    "ImageItem",
    "LabMetrics",
    "LinkItem",
    "ModuleError",
    "ModuleResult",
    "ModuleStatus",
    "Opportunity",
    "PageData",
    "Performance",
    "ProjectInfo",
    "Report",
    "ScreenshotResult",
    "ScreenshotViewport",
    "SeoAnalysis",
    "SeoIssue",
    "SeoSummary",
    "StrategyPerformance",
    "TypographyAnalysis",
    "VisualIdentity",
    "WebsiteContent",
]
