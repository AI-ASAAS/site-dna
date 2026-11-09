"""Unit tests for ColorAnalyzer and WCAG contrast calculations."""

from site_dna.analysis.visual_identity.color_analyzer import (
    ColorAnalyzer,
    calculate_contrast_ratio,
    calculate_relative_luminance,
)
from site_dna.analysis.visual_identity.context_builder import PageAnalysisContext


def test_relative_luminance():
    """Verify luminance calculations for standard reference colors."""
    # Pure white [255, 255, 255] luminance is 1.0
    lum_white = calculate_relative_luminance([255, 255, 255])
    assert abs(lum_white - 1.0) < 0.001

    # Pure black [0, 0, 0] luminance is 0.0
    lum_black = calculate_relative_luminance([0, 0, 0])
    assert abs(lum_black - 0.0) < 0.001


def test_contrast_ratio_wcag():
    """Verify WCAG 2.1 contrast ratios."""
    # Black on White: 21:1
    ratio_max = calculate_contrast_ratio([0, 0, 0], [255, 255, 255])
    assert ratio_max == 21.0

    # Same color on same color: 1:1
    ratio_min = calculate_contrast_ratio([100, 100, 100], [100, 100, 100])
    assert ratio_min == 1.0

    # Low contrast gray on gray (#888888 on #777777): < 3:1
    ratio_low = calculate_contrast_ratio([136, 136, 136], [119, 119, 119])
    assert ratio_low < 3.0


def test_color_analyzer_palette_fragmentation():
    """Verify that excessive colors (>10) triggers a fragmentation finding."""
    # Create mock page context with 12 distinct colors
    colors = [
        {"hex": f"#{i:02x}{i:02x}{i:02x}", "rgb": [i, i, i], "usage": "brand", "occurrence_count": 5} for i in range(12)
    ]
    page = PageAnalysisContext(
        page_url="https://test.com/",
        safe_page_id="p0",
        status="completed",
        colors=colors,
    )

    result = ColorAnalyzer.analyze_colors([page], evidence_index={})
    assert result["distinct_color_count"] == 12
    assert any("تشتت لوني" in f.title for f in result["findings"])


def test_color_analyzer_low_contrast_finding():
    """Verify that low text/bg contrast generates a high-severity finding."""
    colors = [
        {"hex": "#888888", "rgb": [136, 136, 136], "usage": "text", "occurrence_count": 10},
        {"hex": "#777777", "rgb": [119, 119, 119], "usage": "background", "occurrence_count": 10},
    ]
    page = PageAnalysisContext(
        page_url="https://test.com/",
        safe_page_id="p0",
        status="completed",
        colors=colors,
    )

    result = ColorAnalyzer.analyze_colors([page], evidence_index={})
    assert any(f.category == "contrast" and f.severity == "high" for f in result["findings"])
