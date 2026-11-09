"""Unit tests for Phase 03 Visual Evidence Pydantic schemas."""

import json
from datetime import datetime, timezone

from site_dna.schemas.visual import (
    ColorRecord,
    ComputedStyleRecord,
    DOMElementRecord,
    LayoutRecord,
    ResponsiveObservation,
    ScreenshotRecord,
    TypographyRecord,
    ViewportProfile,
    VisualCaptureRequest,
    VisualCaptureResult,
    VisualCaptureStatistics,
    VisualEvidenceRecord,
    VisualPageResult,
)


def test_viewport_profile():
    desktop = ViewportProfile(name="desktop", width=1440, height=900)
    assert desktop.name == "desktop"
    assert desktop.width == 1440
    assert desktop.height == 900
    assert desktop.device_scale_factor == 1.0
    assert not desktop.is_mobile
    assert not desktop.has_touch

    mobile = ViewportProfile(
        name="mobile",
        width=390,
        height=844,
        device_scale_factor=2.0,
        is_mobile=True,
        has_touch=True,
    )
    assert mobile.name == "mobile"
    assert mobile.device_scale_factor == 2.0
    assert mobile.is_mobile
    assert mobile.has_touch


def test_screenshot_record():
    now = datetime.now(timezone.utc)
    rec = ScreenshotRecord(
        viewport_profile="desktop",
        screenshot_type="viewport",
        file_path="runs/test/desktop-viewport.png",
        relative_path="desktop-viewport.png",
        file_size_bytes=10240,
        width_px=1440,
        height_px=900,
        sha256="abcdef1234567890",
        captured_at=now,
        success=True,
    )
    assert rec.viewport_profile == "desktop"
    assert rec.screenshot_type == "viewport"
    assert rec.width_px == 1440
    assert rec.sha256 == "abcdef1234567890"
    assert rec.success is True


def test_dom_element_record():
    elem = DOMElementRecord(
        element_id="el-0",
        tag_name="header",
        dom_path="body > header",
        semantic_role="banner",
        classes=["site-header", "fixed"],
        attributes={"aria-label": "Main Navigation"},
    )
    assert elem.tag_name == "header"
    assert elem.semantic_role == "banner"
    assert "site-header" in elem.classes
    assert elem.attributes["aria-label"] == "Main Navigation"


def test_computed_style_record():
    style = ComputedStyleRecord(
        element_id="btn-1",
        tag_name="button",
        color="rgb(255, 255, 255)",
        background_color="rgb(10, 80, 160)",
        font_family="Inter, sans-serif",
        font_size="16px",
        font_weight="600",
        viewport="desktop",
    )
    assert style.tag_name == "button"
    assert style.background_color == "rgb(10, 80, 160)"
    assert style.viewport == "desktop"


def test_color_record():
    color = ColorRecord(
        hex="#0A50A0",
        rgb=[10, 80, 160],
        alpha=1.0,
        usage="button_background",
        occurrence_count=3,
        sample_element_ids=["btn-1", "btn-2"],
    )
    assert color.hex == "#0A50A0"
    assert color.rgb == [10, 80, 160]
    assert color.occurrence_count == 3


def test_typography_record():
    typo = TypographyRecord(
        element_type="h1",
        font_family="Tajawal, sans-serif",
        font_size_px=36.0,
        font_weight="700",
        line_height_px=44.0,
        direction="rtl",
        language="ar",
        viewport="desktop",
    )
    assert typo.element_type == "h1"
    assert typo.font_size_px == 36.0
    assert typo.direction == "rtl"


def test_layout_record():
    layout = LayoutRecord(
        section_type="nav",
        element_id="sec-nav",
        bounding_box={"x": 0.0, "y": 0.0, "width": 1440.0, "height": 80.0},
        display="flex",
        position="sticky",
        is_visible=True,
    )
    assert layout.section_type == "nav"
    assert layout.bounding_box["width"] == 1440.0
    assert layout.is_visible is True


def test_responsive_observation():
    obs = ResponsiveObservation(
        observation_type="horizontal_overflow",
        status="warning",
        description="Mobile viewport has horizontal overflow (scrollWidth 420px > viewport 390px)",
        desktop_value=1440,
        mobile_value=420,
    )
    assert obs.observation_type == "horizontal_overflow"
    assert obs.status == "warning"


def test_visual_evidence_record():
    ev = VisualEvidenceRecord(
        crawl_run_id="crawl-123",
        visual_run_id="vis-456",
        page_url="https://example.com",
        viewport_profile="desktop",
        evidence_category="screenshot",
        confidence_category="observed",
        field_reference="visual.screenshot.desktop_viewport",
        observed_value={"path": "desktop-viewport.png"},
        collection_method="playwright",
    )
    assert ev.crawl_run_id == "crawl-123"
    assert ev.evidence_category == "screenshot"
    assert ev.confidence_category == "observed"


def test_visual_capture_result_full_roundtrip():
    res = VisualCaptureResult(
        crawl_run_id="crawl-test-1",
        visual_run_id="vis-test-1",
        status="completed",
        target_origin="https://example.com",
        pages=[
            VisualPageResult(
                page_url="https://example.com",
                safe_page_id="page_00_example_com",
                status="completed",
                desktop_screenshots=[],
                mobile_screenshots=[],
            )
        ],
        statistics=VisualCaptureStatistics(
            total_pages_attempted=1,
            desktop_captures_completed=1,
            mobile_captures_completed=1,
            screenshots_saved=2,
        ),
    )

    json_str = res.model_dump_json()
    data = json.loads(json_str)
    assert data["crawl_run_id"] == "crawl-test-1"
    assert data["status"] == "completed"
    assert len(data["pages"]) == 1
    assert data["statistics"]["screenshots_saved"] == 2

    # Deserialization test
    loaded = VisualCaptureResult.model_validate(data)
    assert loaded.visual_run_id == "vis-test-1"
    assert loaded.pages[0].safe_page_id == "page_00_example_com"


def test_visual_capture_request_defaults():
    req = VisualCaptureRequest(crawl_run_id="run-123")
    assert req.crawl_run_id == "run-123"
    assert req.profiles == ["desktop", "mobile"]
    assert req.max_pages is None
