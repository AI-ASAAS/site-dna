"""Pydantic schemas for Site DNA Phase 03 Visual Evidence and Browser Rendering."""

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

CaptureStatus = Literal["completed", "partial", "failed", "blocked", "skipped"]
EvidenceCategory = Literal[
    "screenshot",
    "computed_css",
    "dom_element",
    "font_observation",
    "color_observation",
    "layout_measurement",
    "image_reference",
    "navigation_element",
    "responsive_measurement",
    "render_error",
]
ConfidenceLevel = Literal["observed", "derived", "heuristic", "unavailable"]


class ViewportProfile(BaseModel):
    """Browser viewport configuration profile for rendering."""

    name: Literal["desktop", "mobile"]
    width: int
    height: int
    device_scale_factor: float = 1.0
    is_mobile: bool = False
    has_touch: bool = False


class ScreenshotRecord(BaseModel):
    """Metadata describing a captured page screenshot."""

    viewport_profile: str
    screenshot_type: Literal["viewport", "full_page"]
    file_path: str
    relative_path: str
    file_size_bytes: int
    width_px: int
    height_px: int
    sha256: str
    captured_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = True
    error: Optional[str] = None


class DOMElementRecord(BaseModel):
    """Structured extraction of a relevant rendered DOM node."""

    element_id: str
    tag_name: str
    dom_path: str
    semantic_role: Optional[str] = None
    accessible_name: Optional[str] = None
    text_excerpt: Optional[str] = None
    visible: bool = True
    bounding_box: Optional[dict[str, float]] = None
    parent_reference: Optional[str] = None
    classes: list[str] = Field(default_factory=list)
    attributes: dict[str, str] = Field(default_factory=dict)


class ComputedStyleRecord(BaseModel):
    """Extracted computed CSS style declarations for a DOM element."""

    element_id: str
    tag_name: str
    color: Optional[str] = None
    background_color: Optional[str] = None
    border_color: Optional[str] = None
    font_family: Optional[str] = None
    font_size: Optional[str] = None
    font_weight: Optional[str] = None
    line_height: Optional[str] = None
    display: Optional[str] = None
    position: Optional[str] = None
    border_radius: Optional[str] = None
    box_shadow: Optional[str] = None
    viewport: str = "desktop"


class ColorRecord(BaseModel):
    """Observed color occurrence and usage role."""

    hex: str
    rgb: list[int]
    alpha: float = 1.0
    usage: str
    occurrence_count: int = 1
    sample_element_ids: list[str] = Field(default_factory=list)
    source: str = "computed_css"


class TypographyRecord(BaseModel):
    """Extracted typography properties for a text-bearing element."""

    element_type: str
    font_family: str
    font_size_px: float
    font_weight: str
    line_height_px: Optional[float] = None
    letter_spacing: Optional[str] = None
    text_align: Optional[str] = None
    text_transform: Optional[str] = None
    direction: Optional[str] = None
    language: Optional[str] = None
    viewport: str = "desktop"
    element_id: Optional[str] = None


class LayoutRecord(BaseModel):
    """Spatial and structural layout properties of candidate sections."""

    section_type: str
    element_id: str
    bounding_box: dict[str, float]
    display: str
    position: str
    is_visible: bool = True
    grid_flex_properties: dict[str, Any] = Field(default_factory=dict)


class ResponsiveObservation(BaseModel):
    """Measurable structural change between desktop and mobile viewports."""

    observation_type: str
    status: str
    description: str
    desktop_value: Any = None
    mobile_value: Any = None
    evidence_ids: list[str] = Field(default_factory=list)


class VisualEvidenceRecord(BaseModel):
    """Granular, auditable visual evidence unit."""

    evidence_id: str = Field(default_factory=lambda: str(uuid4()))
    crawl_run_id: str
    visual_run_id: str
    page_url: str
    viewport_profile: str
    evidence_category: EvidenceCategory
    confidence_category: ConfidenceLevel
    field_reference: str
    observed_value: Any
    collection_method: str
    screenshot_reference: Optional[str] = None
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VisualCaptureStatistics(BaseModel):
    """Quantitative execution statistics for the visual collection run."""

    total_pages_attempted: int = 0
    desktop_captures_completed: int = 0
    mobile_captures_completed: int = 0
    screenshots_saved: int = 0
    dom_elements_extracted: int = 0
    css_records_extracted: int = 0
    evidence_records_created: int = 0
    total_duration_ms: float = 0.0
    errors_count: int = 0


class VisualPageResult(BaseModel):
    """Complete visual data collection bundle for a single website page."""

    page_url: str
    safe_page_id: str
    status: CaptureStatus = "completed"
    desktop_screenshots: list[ScreenshotRecord] = Field(default_factory=list)
    mobile_screenshots: list[ScreenshotRecord] = Field(default_factory=list)
    dom_elements: list[DOMElementRecord] = Field(default_factory=list)
    computed_styles: list[ComputedStyleRecord] = Field(default_factory=list)
    colors: list[ColorRecord] = Field(default_factory=list)
    typography: list[TypographyRecord] = Field(default_factory=list)
    layout_records: list[LayoutRecord] = Field(default_factory=list)
    responsive_observations: list[ResponsiveObservation] = Field(default_factory=list)
    evidence_records: list[VisualEvidenceRecord] = Field(default_factory=list)
    render_errors: list[str] = Field(default_factory=list)


class VisualCaptureResult(BaseModel):
    """Comprehensive visual capture result for an entire website run."""

    schema_version: str = "1.0"
    crawl_run_id: str
    visual_run_id: str = Field(default_factory=lambda: str(uuid4()))
    status: Literal["completed", "partial", "failed", "blocked"] = "completed"
    target_origin: str
    pages: list[VisualPageResult] = Field(default_factory=list)
    statistics: VisualCaptureStatistics = Field(default_factory=VisualCaptureStatistics)
    manifest_path: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class VisualCaptureRequest(BaseModel):
    """Input payload to trigger visual evidence collection."""

    crawl_run_id: Optional[str] = None
    crawl_file: Optional[str] = None
    profiles: list[str] = Field(default_factory=lambda: ["desktop", "mobile"])
    max_pages: Optional[int] = None
