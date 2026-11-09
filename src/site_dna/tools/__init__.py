"""Custom CrewAI tools for Site DNA."""

from site_dna.tools.competitor_intelligence_tool import (
    CompetitorIntelligenceTool,
    CompetitorIntelligenceToolInput,
)
from site_dna.tools.content_marketing_tool import (
    ContentMarketingTool,
    ContentMarketingToolInput,
)
from site_dna.tools.technical_seo_tool import (
    TechnicalSEOTool,
    TechnicalSEOToolInput,
)
from site_dna.tools.ux_ui_tool import UXUITool, UXUIToolInput
from site_dna.tools.visual_evidence_tool import VisualEvidenceTool
from site_dna.tools.visual_identity_tool import VisualIdentityTool, VisualIdentityToolInput
from site_dna.tools.website_discovery_tool import WebsiteDiscoveryTool

__all__ = [
    "CompetitorIntelligenceTool",
    "CompetitorIntelligenceToolInput",
    "ContentMarketingTool",
    "ContentMarketingToolInput",
    "TechnicalSEOTool",
    "TechnicalSEOToolInput",
    "UXUITool",
    "UXUIToolInput",
    "VisualEvidenceTool",
    "VisualIdentityTool",
    "VisualIdentityToolInput",
    "WebsiteDiscoveryTool",
]
