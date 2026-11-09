"""Page-level schemas for extracted HTML structures and metadata."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

PageCategory = Literal[
    "home",
    "about",
    "services",
    "products",
    "pricing",
    "contact",
    "portfolio",
    "blog",
    "faq",
    "other",
    "unknown",
]


class HeadingData(BaseModel):
    """Extracted HTML heading tag with its hierarchical level."""

    level: int = Field(ge=1, le=6, description="Heading level (1 for H1, 2 for H2, etc.)")
    text: str = Field(description="Stripped text content of the heading")


class LinkData(BaseModel):
    """Extracted hyperlink information."""

    url: str = Field(description="Resolved absolute URL")
    text: str = Field(default="", description="Anchor text or description")
    is_internal: bool = Field(default=True, description="Whether link is within the target origin")
    rel: Optional[str] = Field(default=None, description="Link rel attribute (e.g. nofollow, sponsored)")


class ImageData(BaseModel):
    """Extracted image reference."""

    src: str = Field(description="Resolved absolute image URL")
    alt: Optional[str] = Field(default=None, description="Alt text attribute")
    width: Optional[int] = Field(default=None, description="Declared width if specified")
    height: Optional[int] = Field(default=None, description="Declared height if specified")


class FormData(BaseModel):
    """Extracted HTML form element metadata."""

    action: Optional[str] = Field(default=None, description="Resolved form action URL")
    method: str = Field(default="GET", description="Form HTTP method (GET or POST)")
    input_names: list[str] = Field(default_factory=list, description="Names of form input fields")
    has_submit_button: bool = Field(default=False, description="Whether form contains a submit button")


class PageMetadata(BaseModel):
    """Head and OpenGraph metadata extracted from HTML."""

    title: Optional[str] = None
    description: Optional[str] = None
    canonical_url: Optional[str] = None
    language: Optional[str] = None
    dir: Optional[str] = None
    charset: Optional[str] = None
    robots_meta: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image: Optional[str] = None
    viewport: Optional[str] = None


class PageData(BaseModel):
    """Complete structured representation of a crawled page."""

    url: str = Field(description="Original requested URL")
    final_url: str = Field(description="Final canonical URL after redirects")
    status_code: int = Field(description="HTTP response status code")
    depth: int = Field(ge=0, description="Crawl depth level (0 for seed/home)")
    category: PageCategory = Field(default="unknown", description="Heuristic page classification")
    category_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Classification confidence")
    metadata: PageMetadata = Field(default_factory=PageMetadata)
    headings: list[HeadingData] = Field(default_factory=list)
    main_content_text: str = Field(default="", description="Extracted visible text without chrome/boilerplate")
    word_count: int = Field(default=0, ge=0)
    navigation_links: list[LinkData] = Field(default_factory=list)
    buttons: list[str] = Field(default_factory=list, description="Extracted button text / CTAs")
    images: list[ImageData] = Field(default_factory=list)
    forms: list[FormData] = Field(default_factory=list)
    json_ld: list[dict[str, Any]] = Field(default_factory=list, description="Parsed JSON-LD scripts")
    crawled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
