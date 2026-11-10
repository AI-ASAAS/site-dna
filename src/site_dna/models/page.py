"""Per-page content model defined for Phase 3 and reused by later phases."""

from datetime import datetime

from pydantic import BaseModel, Field

from site_dna.models.common import FileRef


class HeadingLists(BaseModel):
    """Headings grouped by level, in document order."""

    h1: list[str] = Field(default_factory=list)
    h2: list[str] = Field(default_factory=list)
    h3: list[str] = Field(default_factory=list)


class HeadingOutlineItem(BaseModel):
    """Single heading entry in the document outline."""

    level: int
    text: str


class LinkItem(BaseModel):
    """Link discovered on a page."""

    url: str
    text: str
    internal: bool
    rel: str | None = None


class ImageItem(BaseModel):
    """Image discovered on a page."""

    src: str
    alt: str | None = None
    width: int | None = None
    height: int | None = None
    loading: str | None = None


class PageData(BaseModel):
    """Content and structure extracted from a single crawled page."""

    url: str
    final_url: str | None = None
    http_status: int | None = None
    category: str | None = None
    depth: int | None = None
    fetched_at: datetime | None = None
    fetch_ms: int | None = None
    title: str | None = None
    language: str | None = None
    markdown: str | None = None
    markdown_file: FileRef | None = None
    markdown_chars: int | None = None
    word_count: int | None = None
    headings: HeadingLists = Field(default_factory=HeadingLists)
    heading_outline: list[HeadingOutlineItem] = Field(default_factory=list)
    paragraphs_count: int | None = None
    lists_count: int | None = None
    links: list[LinkItem] = Field(default_factory=list)
    images: list[ImageItem] = Field(default_factory=list)
    html_sha256: str | None = None
    raw_html: str | None = Field(default=None, exclude=True)
    non_http_link_counts: dict[str, int] = Field(default_factory=dict, exclude=True)
    error: str | None = None
