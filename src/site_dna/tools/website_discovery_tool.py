"""CrewAI BaseTool wrapper for Site DNA Website Discovery."""

from typing import Optional

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from site_dna.discovery.service import WebsiteDiscoveryService
from site_dna.schemas.discovery import CrawlRequest


class WebsiteDiscoveryInput(BaseModel):
    """Input parameters for website discovery tool."""

    url: str = Field(description="The website URL to discover and crawl")
    max_pages: Optional[int] = Field(default=None, description="Maximum number of pages to crawl")
    max_depth: Optional[int] = Field(default=None, description="Maximum crawl depth relative to root")


class WebsiteDiscoveryTool(BaseTool):
    """CrewAI tool providing deterministic, secure website discovery and structured data extraction."""

    name: str = "website_discovery_tool"
    description: str = (
        "Discovers, crawls, and extracts structured data (metadata, headings, text, links, buttons, "
        "images, forms) and auditable evidence from a public website URL."
    )
    args_schema: type[BaseModel] = WebsiteDiscoveryInput

    def _run(self, url: str, max_pages: Optional[int] = None, max_depth: Optional[int] = None) -> str:
        """Execute website discovery synchronously and return JSON-formatted crawl summary."""
        service = WebsiteDiscoveryService()
        req = CrawlRequest(url=url, max_pages=max_pages, max_depth=max_depth)
        result = service.discover_sync(req)
        return result.model_dump_json(indent=2)
