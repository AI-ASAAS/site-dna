"""Generate synthetic test fixtures for Phase 04 Visual Identity tests."""

import hashlib
import json
from pathlib import Path

from PIL import Image

FIXTURES_DIR = Path("tests/fixtures/visual_identity")


def create_solid_png(path: Path, width: int, height: int, color: tuple[int, int, int]) -> tuple[str, int]:
    """Create a solid color PNG and return (sha256, file_size_bytes)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (width, height), color)
    img.save(path, format="PNG")
    raw = path.read_bytes()
    return hashlib.sha256(raw).hexdigest(), len(raw)


def build_fixture_a():
    """Fixture A: Consistent Visual Identity (2 pages, cohesive palette, consistent typography)."""
    target = FIXTURES_DIR / "fixture_a"
    vis_dir = target / "runs" / "crawl-a" / "visual" / "vis-a"
    pages_dir = vis_dir / "pages"

    p1_desk = pages_dir / "p1" / "desktop_viewport.png"
    p1_mob = pages_dir / "p1" / "mobile_viewport.png"
    p2_desk = pages_dir / "p2" / "desktop_viewport.png"
    p2_mob = pages_dir / "p2" / "mobile_viewport.png"

    h1_desk, s1_desk = create_solid_png(p1_desk, 1280, 800, (29, 78, 216))
    h1_mob, s1_mob = create_solid_png(p1_mob, 375, 667, (29, 78, 216))
    h2_desk, s2_desk = create_solid_png(p2_desk, 1280, 800, (29, 78, 216))
    h2_mob, s2_mob = create_solid_png(p2_mob, 375, 667, (29, 78, 216))

    crawl_json = {
        "schema_version": "1.0",
        "run_id": "crawl-a",
        "status": "completed",
        "website_info": {
            "initial_url": "https://site-a.com",
            "canonical_origin": "https://site-a.com",
            "declared_language": "en",
        },
        "pages": [
            {
                "url": "https://site-a.com/",
                "final_url": "https://site-a.com/",
                "depth": 0,
                "status_code": 200,
                "metadata": {"title": "Site A Home", "description": "Home"},
            },
            {
                "url": "https://site-a.com/about",
                "final_url": "https://site-a.com/about",
                "depth": 1,
                "status_code": 200,
                "metadata": {"title": "About Site A", "description": "About"},
            },
        ],
        "statistics": {"total_pages_visited": 2},
    }
    (target / "runs" / "crawl-a" / "crawl.json").write_text(json.dumps(crawl_json, indent=2), encoding="utf-8")

    visual_json = {
        "schema_version": "1.0",
        "crawl_run_id": "crawl-a",
        "visual_run_id": "vis-a",
        "status": "completed",
        "target_origin": "https://site-a.com",
        "pages": [
            {
                "page_url": "https://site-a.com/",
                "safe_page_id": "page_00_home",
                "status": "completed",
                "desktop_screenshots": [
                    {
                        "viewport_profile": "desktop",
                        "screenshot_type": "viewport",
                        "file_path": str(p1_desk.resolve()),
                        "relative_path": "pages/p1/desktop_viewport.png",
                        "file_size_bytes": s1_desk,
                        "width_px": 1280,
                        "height_px": 800,
                        "sha256": h1_desk,
                        "success": True,
                    }
                ],
                "mobile_screenshots": [
                    {
                        "viewport_profile": "mobile",
                        "screenshot_type": "viewport",
                        "file_path": str(p1_mob.resolve()),
                        "relative_path": "pages/p1/mobile_viewport.png",
                        "file_size_bytes": s1_mob,
                        "width_px": 375,
                        "height_px": 667,
                        "sha256": h1_mob,
                        "success": True,
                    }
                ],
                "colors": [
                    {"hex": "#1d4ed8", "rgb": [29, 78, 216], "usage": "primary", "occurrence_count": 25},
                    {"hex": "#ffffff", "rgb": [255, 255, 255], "usage": "background", "occurrence_count": 40},
                    {"hex": "#1f2937", "rgb": [31, 41, 55], "usage": "text", "occurrence_count": 50},
                    {"hex": "#9333ea", "rgb": [147, 51, 234], "usage": "secondary", "occurrence_count": 10},
                ],
                "typography": [
                    {
                        "element_type": "h1",
                        "font_family": "Inter, sans-serif",
                        "font_size_px": 36.0,
                        "font_weight": "700",
                        "line_height_px": 44.0,
                    },
                    {
                        "element_type": "h2",
                        "font_family": "Inter, sans-serif",
                        "font_size_px": 28.0,
                        "font_weight": "600",
                        "line_height_px": 36.0,
                    },
                    {
                        "element_type": "p",
                        "font_family": "Inter, sans-serif",
                        "font_size_px": 16.0,
                        "font_weight": "400",
                        "line_height_px": 24.0,
                    },
                ],
                "layout_records": [
                    {
                        "section_type": "hero",
                        "element_id": "hero-sec",
                        "bounding_box": {"x": 0, "y": 0, "width": 1280, "height": 500},
                        "display": "flex",
                        "position": "static",
                    }
                ],
                "responsive_observations": [
                    {
                        "observation_type": "mobile_overflow",
                        "status": "passed",
                        "description": "No horizontal overflow detected",
                    }
                ],
                "evidence_records": [
                    {
                        "evidence_id": "ev-a-1",
                        "crawl_run_id": "crawl-a",
                        "visual_run_id": "vis-a",
                        "page_url": "https://site-a.com/",
                        "viewport_profile": "desktop",
                        "evidence_category": "screenshot",
                        "confidence_category": "observed",
                        "field_reference": "desktop_viewport",
                        "observed_value": str(p1_desk.resolve()),
                        "collection_method": "playwright_screenshot",
                    }
                ],
            },
            {
                "page_url": "https://site-a.com/about",
                "safe_page_id": "page_01_about",
                "status": "completed",
                "desktop_screenshots": [
                    {
                        "viewport_profile": "desktop",
                        "screenshot_type": "viewport",
                        "file_path": str(p2_desk.resolve()),
                        "relative_path": "pages/p2/desktop_viewport.png",
                        "file_size_bytes": s2_desk,
                        "width_px": 1280,
                        "height_px": 800,
                        "sha256": h2_desk,
                        "success": True,
                    }
                ],
                "mobile_screenshots": [
                    {
                        "viewport_profile": "mobile",
                        "screenshot_type": "viewport",
                        "file_path": str(p2_mob.resolve()),
                        "relative_path": "pages/p2/mobile_viewport.png",
                        "file_size_bytes": s2_mob,
                        "width_px": 375,
                        "height_px": 667,
                        "sha256": h2_mob,
                        "success": True,
                    }
                ],
                "colors": [
                    {"hex": "#1d4ed8", "rgb": [29, 78, 216], "usage": "primary", "occurrence_count": 20},
                    {"hex": "#ffffff", "rgb": [255, 255, 255], "usage": "background", "occurrence_count": 35},
                    {"hex": "#1f2937", "rgb": [31, 41, 55], "usage": "text", "occurrence_count": 45},
                ],
                "typography": [
                    {
                        "element_type": "h1",
                        "font_family": "Inter, sans-serif",
                        "font_size_px": 36.0,
                        "font_weight": "700",
                        "line_height_px": 44.0,
                    },
                    {
                        "element_type": "p",
                        "font_family": "Inter, sans-serif",
                        "font_size_px": 16.0,
                        "font_weight": "400",
                        "line_height_px": 24.0,
                    },
                ],
                "evidence_records": [
                    {
                        "evidence_id": "ev-a-2",
                        "crawl_run_id": "crawl-a",
                        "visual_run_id": "vis-a",
                        "page_url": "https://site-a.com/about",
                        "viewport_profile": "desktop",
                        "evidence_category": "screenshot",
                        "confidence_category": "observed",
                        "field_reference": "desktop_viewport",
                        "observed_value": str(p2_desk.resolve()),
                        "collection_method": "playwright_screenshot",
                    }
                ],
            },
        ],
    }
    (vis_dir / "visual.json").write_text(json.dumps(visual_json, indent=2), encoding="utf-8")
    (vis_dir / "manifest.json").write_text(json.dumps(visual_json, indent=2), encoding="utf-8")


def build_fixture_b():
    """Fixture B: Inconsistent Visual Identity (chaotic colors, 5 fonts, mobile overflow)."""
    target = FIXTURES_DIR / "fixture_b"
    vis_dir = target / "runs" / "crawl-b" / "visual" / "vis-b"
    pages_dir = vis_dir / "pages"

    p1_desk = pages_dir / "p1" / "desktop_viewport.png"
    p1_mob = pages_dir / "p1" / "mobile_viewport.png"
    p2_desk = pages_dir / "p2" / "desktop_viewport.png"
    p2_mob = pages_dir / "p2" / "mobile_viewport.png"

    h1_desk, s1_desk = create_solid_png(p1_desk, 1280, 800, (255, 0, 0))
    h1_mob, s1_mob = create_solid_png(p1_mob, 375, 667, (0, 255, 0))
    h2_desk, s2_desk = create_solid_png(p2_desk, 1280, 800, (0, 0, 255))
    h2_mob, s2_mob = create_solid_png(p2_mob, 375, 667, (255, 255, 0))

    crawl_json = {
        "schema_version": "1.0",
        "run_id": "crawl-b",
        "status": "completed",
        "website_info": {"initial_url": "https://site-b.com", "canonical_origin": "https://site-b.com"},
        "pages": [
            {
                "url": "https://site-b.com/",
                "final_url": "https://site-b.com/",
                "depth": 0,
                "status_code": 200,
                "metadata": {},
            },
            {
                "url": "https://site-b.com/services",
                "final_url": "https://site-b.com/services",
                "depth": 1,
                "status_code": 200,
                "metadata": {},
            },
        ],
    }
    (target / "runs" / "crawl-b" / "crawl.json").write_text(json.dumps(crawl_json, indent=2), encoding="utf-8")

    visual_json = {
        "schema_version": "1.0",
        "crawl_run_id": "crawl-b",
        "visual_run_id": "vis-b",
        "status": "completed",
        "target_origin": "https://site-b.com",
        "pages": [
            {
                "page_url": "https://site-b.com/",
                "safe_page_id": "page_00_home",
                "status": "completed",
                "desktop_screenshots": [
                    {
                        "viewport_profile": "desktop",
                        "screenshot_type": "viewport",
                        "file_path": str(p1_desk.resolve()),
                        "relative_path": "pages/p1/desktop_viewport.png",
                        "file_size_bytes": s1_desk,
                        "width_px": 1280,
                        "height_px": 800,
                        "sha256": h1_desk,
                        "success": True,
                    }
                ],
                "mobile_screenshots": [
                    {
                        "viewport_profile": "mobile",
                        "screenshot_type": "viewport",
                        "file_path": str(p1_mob.resolve()),
                        "relative_path": "pages/p1/mobile_viewport.png",
                        "file_size_bytes": s1_mob,
                        "width_px": 375,
                        "height_px": 667,
                        "sha256": h1_mob,
                        "success": True,
                    }
                ],
                "colors": [
                    {"hex": "#ff0000", "rgb": [255, 0, 0], "usage": "brand", "occurrence_count": 5},
                    {"hex": "#00ff00", "rgb": [0, 255, 0], "usage": "brand", "occurrence_count": 5},
                    {"hex": "#0000ff", "rgb": [0, 0, 255], "usage": "brand", "occurrence_count": 5},
                    {"hex": "#ffff00", "rgb": [255, 255, 0], "usage": "brand", "occurrence_count": 5},
                    {"hex": "#ff00ff", "rgb": [255, 0, 255], "usage": "brand", "occurrence_count": 5},
                    {"hex": "#00ffff", "rgb": [0, 255, 255], "usage": "brand", "occurrence_count": 5},
                    {"hex": "#888888", "rgb": [136, 136, 136], "usage": "text", "occurrence_count": 10},
                    {"hex": "#777777", "rgb": [119, 119, 119], "usage": "background", "occurrence_count": 10},
                    {"hex": "#ffa500", "rgb": [255, 165, 0], "usage": "brand", "occurrence_count": 5},
                    {"hex": "#800080", "rgb": [128, 0, 128], "usage": "brand", "occurrence_count": 5},
                    {"hex": "#008000", "rgb": [0, 128, 0], "usage": "brand", "occurrence_count": 5},
                    {"hex": "#000080", "rgb": [0, 0, 128], "usage": "brand", "occurrence_count": 5},
                ],
                "typography": [
                    {
                        "element_type": "h1",
                        "font_family": "Comic Sans MS",
                        "font_size_px": 24.0,
                        "font_weight": "400",
                        "line_height_px": 24.0,
                    },
                    {
                        "element_type": "h2",
                        "font_family": "Papyrus",
                        "font_size_px": 28.0,
                        "font_weight": "700",
                        "line_height_px": 26.0,
                    },
                    {
                        "element_type": "p",
                        "font_family": "Times New Roman",
                        "font_size_px": 16.0,
                        "font_weight": "400",
                        "line_height_px": 16.0,
                    },
                ],
                "responsive_observations": [
                    {
                        "observation_type": "horizontal_overflow",
                        "status": "failed",
                        "description": "Horizontal overflow of 120px detected",
                        "mobile_value": {"scroll_width": 495, "viewport_width": 375},
                    }
                ],
                "evidence_records": [
                    {
                        "evidence_id": "ev-b-1",
                        "crawl_run_id": "crawl-b",
                        "visual_run_id": "vis-b",
                        "page_url": "https://site-b.com/",
                        "viewport_profile": "desktop",
                        "evidence_category": "screenshot",
                        "confidence_category": "observed",
                        "field_reference": "shot",
                        "observed_value": str(p1_desk.resolve()),
                        "collection_method": "playwright",
                    }
                ],
            },
            {
                "page_url": "https://site-b.com/services",
                "safe_page_id": "page_01_serv",
                "status": "completed",
                "desktop_screenshots": [
                    {
                        "viewport_profile": "desktop",
                        "screenshot_type": "viewport",
                        "file_path": str(p2_desk.resolve()),
                        "relative_path": "pages/p2/desktop_viewport.png",
                        "file_size_bytes": s2_desk,
                        "width_px": 1280,
                        "height_px": 800,
                        "sha256": h2_desk,
                        "success": True,
                    }
                ],
                "mobile_screenshots": [
                    {
                        "viewport_profile": "mobile",
                        "screenshot_type": "viewport",
                        "file_path": str(p2_mob.resolve()),
                        "relative_path": "pages/p2/mobile_viewport.png",
                        "file_size_bytes": s2_mob,
                        "width_px": 375,
                        "height_px": 667,
                        "sha256": h2_mob,
                        "success": True,
                    }
                ],
                "colors": [
                    {"hex": "#123456", "rgb": [18, 52, 86], "usage": "brand", "occurrence_count": 5},
                    {"hex": "#654321", "rgb": [101, 67, 33], "usage": "brand", "occurrence_count": 5},
                ],
                "typography": [
                    {"element_type": "h1", "font_family": "Arial", "font_size_px": 32.0, "font_weight": "400"},
                    {"element_type": "p", "font_family": "Roboto", "font_size_px": 14.0, "font_weight": "300"},
                ],
                "evidence_records": [
                    {
                        "evidence_id": "ev-b-2",
                        "crawl_run_id": "crawl-b",
                        "visual_run_id": "vis-b",
                        "page_url": "https://site-b.com/services",
                        "viewport_profile": "desktop",
                        "evidence_category": "screenshot",
                        "confidence_category": "observed",
                        "field_reference": "shot",
                        "observed_value": str(p2_desk.resolve()),
                        "collection_method": "playwright",
                    }
                ],
            },
        ],
    }
    (vis_dir / "visual.json").write_text(json.dumps(visual_json, indent=2), encoding="utf-8")
    (vis_dir / "manifest.json").write_text(json.dumps(visual_json, indent=2), encoding="utf-8")


def build_fixture_c():
    """Fixture C: Minimal Website (1 single page, minimal styling)."""
    target = FIXTURES_DIR / "fixture_c"
    vis_dir = target / "runs" / "crawl-c" / "visual" / "vis-c"
    pages_dir = vis_dir / "pages"

    p1_desk = pages_dir / "p1" / "desktop_viewport.png"
    h1_desk, s1_desk = create_solid_png(p1_desk, 1280, 800, (240, 240, 240))

    crawl_json = {
        "schema_version": "1.0",
        "run_id": "crawl-c",
        "status": "completed",
        "website_info": {"initial_url": "https://site-c.com", "canonical_origin": "https://site-c.com"},
        "pages": [
            {
                "url": "https://site-c.com/",
                "final_url": "https://site-c.com/",
                "depth": 0,
                "status_code": 200,
                "metadata": {},
            }
        ],
    }
    (target / "runs" / "crawl-c" / "crawl.json").write_text(json.dumps(crawl_json, indent=2), encoding="utf-8")

    visual_json = {
        "schema_version": "1.0",
        "crawl_run_id": "crawl-c",
        "visual_run_id": "vis-c",
        "status": "completed",
        "target_origin": "https://site-c.com",
        "pages": [
            {
                "page_url": "https://site-c.com/",
                "safe_page_id": "page_00_home",
                "status": "completed",
                "desktop_screenshots": [
                    {
                        "viewport_profile": "desktop",
                        "screenshot_type": "viewport",
                        "file_path": str(p1_desk.resolve()),
                        "relative_path": "pages/p1/desktop_viewport.png",
                        "file_size_bytes": s1_desk,
                        "width_px": 1280,
                        "height_px": 800,
                        "sha256": h1_desk,
                        "success": True,
                    }
                ],
                "mobile_screenshots": [],
                "colors": [
                    {"hex": "#000000", "rgb": [0, 0, 0], "usage": "text", "occurrence_count": 10},
                    {"hex": "#ffffff", "rgb": [255, 255, 255], "usage": "background", "occurrence_count": 10},
                ],
                "typography": [
                    {"element_type": "p", "font_family": "system-ui", "font_size_px": 16.0, "font_weight": "400"}
                ],
                "evidence_records": [
                    {
                        "evidence_id": "ev-c-1",
                        "crawl_run_id": "crawl-c",
                        "visual_run_id": "vis-c",
                        "page_url": "https://site-c.com/",
                        "viewport_profile": "desktop",
                        "evidence_category": "screenshot",
                        "confidence_category": "observed",
                        "field_reference": "shot",
                        "observed_value": str(p1_desk.resolve()),
                        "collection_method": "playwright",
                    }
                ],
            }
        ],
    }
    (vis_dir / "visual.json").write_text(json.dumps(visual_json, indent=2), encoding="utf-8")
    (vis_dir / "manifest.json").write_text(json.dumps(visual_json, indent=2), encoding="utf-8")


def build_fixture_d():
    """Fixture D: Arabic RTL Website (Arabic font, RTL directionality)."""
    target = FIXTURES_DIR / "fixture_d"
    vis_dir = target / "runs" / "crawl-d" / "visual" / "vis-d"
    pages_dir = vis_dir / "pages"

    p1_desk = pages_dir / "p1" / "desktop_viewport.png"
    p1_mob = pages_dir / "p1" / "mobile_viewport.png"
    h1_desk, s1_desk = create_solid_png(p1_desk, 1280, 800, (15, 23, 42))
    h1_mob, s1_mob = create_solid_png(p1_mob, 375, 667, (15, 23, 42))

    crawl_json = {
        "schema_version": "1.0",
        "run_id": "crawl-d",
        "status": "completed",
        "website_info": {
            "initial_url": "https://site-d.sa",
            "canonical_origin": "https://site-d.sa",
            "declared_language": "ar",
        },
        "pages": [
            {
                "url": "https://site-d.sa/",
                "final_url": "https://site-d.sa/",
                "depth": 0,
                "status_code": 200,
                "metadata": {"title": "موقع أساس"},
            }
        ],
    }
    (target / "runs" / "crawl-d" / "crawl.json").write_text(json.dumps(crawl_json, indent=2), encoding="utf-8")

    visual_json = {
        "schema_version": "1.0",
        "crawl_run_id": "crawl-d",
        "visual_run_id": "vis-d",
        "status": "completed",
        "target_origin": "https://site-d.sa",
        "pages": [
            {
                "page_url": "https://site-d.sa/",
                "safe_page_id": "page_00_home",
                "status": "completed",
                "desktop_screenshots": [
                    {
                        "viewport_profile": "desktop",
                        "screenshot_type": "viewport",
                        "file_path": str(p1_desk.resolve()),
                        "relative_path": "pages/p1/desktop_viewport.png",
                        "file_size_bytes": s1_desk,
                        "width_px": 1280,
                        "height_px": 800,
                        "sha256": h1_desk,
                        "success": True,
                    }
                ],
                "mobile_screenshots": [
                    {
                        "viewport_profile": "mobile",
                        "screenshot_type": "viewport",
                        "file_path": str(p1_mob.resolve()),
                        "relative_path": "pages/p1/mobile_viewport.png",
                        "file_size_bytes": s1_mob,
                        "width_px": 375,
                        "height_px": 667,
                        "sha256": h1_mob,
                        "success": True,
                    }
                ],
                "colors": [
                    {"hex": "#0f172a", "rgb": [15, 23, 42], "usage": "background", "occurrence_count": 30},
                    {"hex": "#f8fafc", "rgb": [248, 250, 252], "usage": "text", "occurrence_count": 40},
                    {"hex": "#38bdf8", "rgb": [56, 189, 248], "usage": "primary", "occurrence_count": 15},
                ],
                "typography": [
                    {
                        "element_type": "h1",
                        "font_family": "Cairo, sans-serif",
                        "font_size_px": 32.0,
                        "font_weight": "700",
                        "direction": "rtl",
                        "language": "ar",
                    },
                    {
                        "element_type": "p",
                        "font_family": "Cairo, sans-serif",
                        "font_size_px": 16.0,
                        "font_weight": "400",
                        "direction": "rtl",
                        "language": "ar",
                    },
                ],
                "evidence_records": [
                    {
                        "evidence_id": "ev-d-1",
                        "crawl_run_id": "crawl-d",
                        "visual_run_id": "vis-d",
                        "page_url": "https://site-d.sa/",
                        "viewport_profile": "desktop",
                        "evidence_category": "screenshot",
                        "confidence_category": "observed",
                        "field_reference": "shot",
                        "observed_value": str(p1_desk.resolve()),
                        "collection_method": "playwright",
                    }
                ],
            }
        ],
    }
    (vis_dir / "visual.json").write_text(json.dumps(visual_json, indent=2), encoding="utf-8")
    (vis_dir / "manifest.json").write_text(json.dumps(visual_json, indent=2), encoding="utf-8")


def build_fixture_e():
    """Fixture E: Missing / Corrupt Evidence (missing screenshot file, bad checksum)."""
    target = FIXTURES_DIR / "fixture_e"
    vis_dir = target / "runs" / "crawl-e" / "visual" / "vis-e"
    pages_dir = vis_dir / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    crawl_json = {
        "schema_version": "1.0",
        "run_id": "crawl-e",
        "status": "completed",
        "website_info": {"initial_url": "https://site-e.com", "canonical_origin": "https://site-e.com"},
        "pages": [
            {
                "url": "https://site-e.com/",
                "final_url": "https://site-e.com/",
                "depth": 0,
                "status_code": 200,
                "metadata": {},
            }
        ],
    }
    (target / "runs" / "crawl-e" / "crawl.json").write_text(json.dumps(crawl_json, indent=2), encoding="utf-8")

    visual_json = {
        "schema_version": "1.0",
        "crawl_run_id": "crawl-e",
        "visual_run_id": "vis-e",
        "status": "completed",
        "target_origin": "https://site-e.com",
        "pages": [
            {
                "page_url": "https://site-e.com/",
                "safe_page_id": "page_00_home",
                "status": "completed",
                "desktop_screenshots": [
                    {
                        "viewport_profile": "desktop",
                        "screenshot_type": "viewport",
                        "file_path": str((pages_dir / "non_existent.png").resolve()),
                        "relative_path": "pages/non_existent.png",
                        "file_size_bytes": 100,
                        "width_px": 1280,
                        "height_px": 800,
                        "sha256": "0000000000000000000000000000000000000000000000000000000000000000",
                        "success": True,
                    }
                ],
                "mobile_screenshots": [],
                "colors": [],
                "typography": [],
                "evidence_records": [],
            }
        ],
    }
    (vis_dir / "visual.json").write_text(json.dumps(visual_json, indent=2), encoding="utf-8")
    (vis_dir / "manifest.json").write_text(json.dumps(visual_json, indent=2), encoding="utf-8")


if __name__ == "__main__":
    print("Generating Phase 04 test fixtures...")
    build_fixture_a()
    build_fixture_b()
    build_fixture_c()
    build_fixture_d()
    build_fixture_e()
    print("All fixtures generated successfully.")
