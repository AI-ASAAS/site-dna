"""Unit tests for Color Contrast (W3C Formula) and Reflow / Zoom Analyzers."""

from pathlib import Path

from site_dna.analysis.accessibility.contrast_analysis import (
    ContrastAnalyzer,
    contrast_ratio,
    relative_luminance,
)
from site_dna.analysis.accessibility.reflow_zoom import ReflowZoomAnalyzer

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "accessibility"


def test_relative_luminance_and_contrast_ratio():
    # Pure white vs pure black = 21:1
    white_lum = relative_luminance(255, 255, 255)
    black_lum = relative_luminance(0, 0, 0)
    assert abs(white_lum - 1.0) < 0.001
    assert abs(black_lum - 0.0) < 0.001
    assert abs(contrast_ratio(white_lum, black_lum) - 21.0) < 0.01

    # Identical colors = 1:1
    assert abs(contrast_ratio(white_lum, white_lum) - 1.0) < 0.01


def test_contrast_analyzer_on_fixtures():
    html_inacc = (FIXTURES_DIR / "inaccessible_site.html").read_text(encoding="utf-8")
    analyzer = ContrastAnalyzer()
    res = analyzer.analyze(html_inacc)

    assert res.measured_text_elements_count >= 1
    # #888888 on #999999 has very low contrast (< 4.5:1)
    assert res.contrast_violations_aa_normal >= 1


def test_reflow_zoom_analyzer():
    html = (FIXTURES_DIR / "inaccessible_site.html").read_text(encoding="utf-8")
    analyzer = ReflowZoomAnalyzer()
    res = analyzer.analyze(html)

    # user-scalable=no detected
    assert res.user_scalable_disabled is True
