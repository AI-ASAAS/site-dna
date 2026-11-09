"""Discovery schemas representing crawl requests, results, errors, and statistics."""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from site_dna.schemas.evidence import EvidenceRecord
from site_dna.schemas.page import PageData


class CrawlRequest(BaseModel):
    """Input payload for a website discovery crawl request."""

    url: str = Field(description="Target website URL to discover and crawl")
    max_pages: Optional[int] = Field(default=None, ge=1, le=50, description="Override maximum pages to crawl")
    max_depth: Optional[int] = Field(default=None, ge=0, le=5, description="Override maximum crawl depth")


class CrawlSettings(BaseModel):
    """Runtime configuration applied during a discovery crawl."""

    max_pages: int
    max_depth: int
    request_delay_seconds: float
    respect_robots: bool
    user_agent: str
    connect_timeout_seconds: float
    read_timeout_seconds: float
    max_html_bytes: int


class WebsiteInfo(BaseModel):
    """High-level summary of the discovered website."""

    initial_url: str
    canonical_origin: str
    declared_language: Optional[str] = None
    sitemap_found: bool = False
    sitemap_urls: list[str] = Field(default_factory=list)
    robots_txt_found: bool = False
    robots_txt_allowed: bool = True


class CrawlError(BaseModel):
    """Recorded error encountered during crawl execution."""

    url: str
    error_type: str
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class CrawlStatistics(BaseModel):
    """Quantitative metrics of the crawl execution."""

    total_pages_crawled: int = 0
    total_pages_discovered: int = 0
    total_duration_ms: float = 0.0
    total_bytes_fetched: int = 0
    errors_count: int = 0


class CrawlResult(BaseModel):
    """Comprehensive discovery and crawl result for Site DNA agents and pipelines."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    website_info: WebsiteInfo
    pages: list[PageData] = Field(default_factory=list)
    discovered_internal_links: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRecord] = Field(default_factory=list)
    errors: list[CrawlError] = Field(default_factory=list)
    statistics: CrawlStatistics = Field(default_factory=CrawlStatistics)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
