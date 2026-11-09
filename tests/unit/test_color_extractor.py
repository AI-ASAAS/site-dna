"""Unit tests for ColorExtractor and parse_css_color utility."""

from site_dna.schemas.visual import ComputedStyleRecord
from site_dna.visual.color_extractor import ColorExtractor, parse_css_color


def test_parse_css_color_rgb():
    res = parse_css_color("rgb(255, 0, 128)")
    assert res is not None
    hex_val, rgb, alpha = res
    assert hex_val == "#FF0080"
    assert rgb == [255, 0, 128]
    assert alpha == 1.0


def test_parse_css_color_rgba():
    res = parse_css_color("rgba(10, 20, 30, 0.5)")
    assert res is not None
    hex_val, rgb, alpha = res
    assert hex_val == "#0A141E"
    assert rgb == [10, 20, 30]
    assert alpha == 0.5


def test_parse_css_color_rgba_zero_alpha():
    # Fully transparent rgba returns None
    res = parse_css_color("rgba(0, 0, 0, 0)")
    assert res is None


def test_parse_css_color_hex():
    res6 = parse_css_color("#1a2b3c")
    assert res6 is not None
    hex_val, rgb, alpha = res6
    assert hex_val == "#1A2B3C"
    assert rgb == [26, 43, 60]
    assert alpha == 1.0

    res3 = parse_css_color("#f0a")
    assert res3 is not None
    hex_val3, rgb3, alpha3 = res3
    assert hex_val3 == "#FF00AA"
    assert rgb3 == [255, 0, 170]
    assert alpha3 == 1.0


def test_parse_css_color_transparent_and_invalid():
    assert parse_css_color("transparent") is None
    assert parse_css_color("inherit") is None
    assert parse_css_color("initial") is None
    assert parse_css_color("none") is None
    assert parse_css_color("") is None
    assert parse_css_color(None) is None
    assert parse_css_color("not-a-color") is None


def test_color_extractor_palette_aggregation():
    styles = [
        ComputedStyleRecord(
            element_id="el-1",
            tag_name="body",
            background_color="rgb(255, 255, 255)",
            color="rgb(30, 30, 30)",
        ),
        ComputedStyleRecord(
            element_id="el-2",
            tag_name="h1",
            background_color="rgba(0, 0, 0, 0)",  # transparent
            color="rgb(10, 80, 160)",
        ),
        ComputedStyleRecord(
            element_id="el-3",
            tag_name="button",
            background_color="rgb(10, 80, 160)",
            color="rgb(255, 255, 255)",
            border_color="rgb(8, 64, 128)",
        ),
        ComputedStyleRecord(
            element_id="el-4",
            tag_name="p",
            background_color="transparent",
            color="rgb(30, 30, 30)",
        ),
    ]

    palette = ColorExtractor.extract_palette(styles)
    assert len(palette) > 0

    # Verify occurrence counts
    text_colors = [c for c in palette if c.usage == "text"]
    assert any(c.hex == "#1E1E1E" and c.occurrence_count == 2 for c in text_colors)

    button_bg = [c for c in palette if c.usage == "button_background"]
    assert any(c.hex == "#0A50A0" for c in button_bg)

    heading_text = [c for c in palette if c.usage == "heading_text"]
    assert any(c.hex == "#0A50A0" for c in heading_text)

    # Sorted by frequency descending
    counts = [c.occurrence_count for c in palette]
    assert counts == sorted(counts, reverse=True)
