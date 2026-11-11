"""Phase 4 unit tests for CSS color parsing and palette helpers."""

import pytest

from site_dna.analyzers.color_utils import (
    RGBA,
    composite,
    hue_distance,
    is_neutral,
    parse_color,
    rgb_to_hsl,
    to_hex,
)


def assert_rgba(actual, red, green, blue, alpha):
    assert actual is not None
    assert actual.r == pytest.approx(red, abs=1)
    assert actual.g == pytest.approx(green, abs=1)
    assert actual.b == pytest.approx(blue, abs=1)
    assert actual.a == pytest.approx(alpha, abs=0.01)


def test_parse_rgb_and_rgba():
    assert_rgba(parse_color("rgb(230, 57, 70)"), 230, 57, 70, 1.0)
    assert_rgba(parse_color("rgba(0, 0, 0, 0)"), 0, 0, 0, 0.0)
    assert_rgba(parse_color("rgb(100% 0% 0% / 50%)"), 255, 0, 0, 0.5)


def test_parse_hex_short_and_long():
    assert_rgba(parse_color("#fff"), 255, 255, 255, 1.0)
    assert_rgba(parse_color("#E63946"), 230, 57, 70, 1.0)
    assert_rgba(parse_color("#E6394680"), 230, 57, 70, 128 / 255)


def test_parse_hsl_and_color_function():
    assert_rgba(parse_color("hsl(0, 100%, 50%)"), 255, 0, 0, 1.0)
    assert_rgba(parse_color("hsla(0, 100%, 50%, 0.25)"), 255, 0, 0, 0.25)
    assert_rgba(parse_color("color(srgb 0.9 0.2 0.3 / 0.5)"), 230, 51, 77, 0.5)


def test_parse_transparent_and_invalid():
    assert_rgba(parse_color("transparent"), 0, 0, 0, 0.0)
    assert parse_color("not-a-color") is None
    assert parse_color("") is None


def test_to_hex_is_uppercase_six_digit():
    assert to_hex(RGBA(230, 57, 70, 1.0)) == "#E63946"
    assert to_hex(RGBA(0, 0, 0, 0.0)) == "#000000"


def test_composite_alpha_over_background():
    result = composite(RGBA(230, 57, 70, 0.5), RGBA(255, 255, 255, 1.0))
    assert_rgba(result, 242.5, 156, 162.5, 1.0)


def test_rgb_to_hsl_and_hue_distance():
    hue, saturation, lightness = rgb_to_hsl(230, 57, 70)
    assert hue == pytest.approx(355.5, abs=0.5)
    assert saturation == pytest.approx(0.776, abs=0.01)
    assert lightness == pytest.approx(0.563, abs=0.01)
    assert hue_distance(355, 10) == pytest.approx(15)
    assert hue_distance(10, 350) == pytest.approx(20)


def test_is_neutral_detects_neutrals_and_brand_colors():
    assert is_neutral("#FFFFFF") is True
    assert is_neutral("#222222") is True
    assert is_neutral("#F1FAEE") is True
    assert is_neutral("#E63946") is False
    assert is_neutral("#1D3557") is False
