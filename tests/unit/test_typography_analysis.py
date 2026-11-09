"""Unit tests for TypographyAnalyzer (font families, hierarchy, Arabic RTL)."""

from site_dna.analysis.visual_identity.context_builder import PageAnalysisContext
from site_dna.analysis.visual_identity.typography_analyzer import TypographyAnalyzer


def test_typography_excessive_fonts():
    """Verify that using more than 3 font families triggers a finding."""
    typography_records = [
        {"element_type": "h1", "font_family": "Comic Sans MS", "font_size_px": 32.0},
        {"element_type": "h2", "font_family": "Papyrus", "font_size_px": 24.0},
        {"element_type": "p", "font_family": "Times New Roman", "font_size_px": 16.0},
        {"element_type": "span", "font_family": "Arial", "font_size_px": 14.0},
    ]
    page = PageAnalysisContext(
        page_url="https://test.com/",
        safe_page_id="p0",
        status="completed",
        typography=typography_records,
    )

    result = TypographyAnalyzer.analyze_typography([page], evidence_index={})
    assert len(result["font_families"]) == 4
    assert any("تعدد عائلات الخطوط" in f.title for f in result["findings"])


def test_typography_scale_ratio_weak():
    """Verify that H1 size close to body size (< 1.3 ratio) triggers hierarchy finding."""
    typography_records = [
        {"element_type": "h1", "font_family": "Inter", "font_size_px": 18.0},
        {"element_type": "p", "font_family": "Inter", "font_size_px": 16.0},
    ]
    page = PageAnalysisContext(
        page_url="https://test.com/",
        safe_page_id="p0",
        status="completed",
        typography=typography_records,
    )

    result = TypographyAnalyzer.analyze_typography([page], evidence_index={})
    assert result["heading_to_body_ratio"] == 1.12 or result["heading_to_body_ratio"] < 1.3
    assert any("تقارب أحجام خطوط العناوين" in f.title for f in result["findings"])


def test_typography_arabic_rtl():
    """Verify that Arabic font and RTL directionality are accurately detected."""
    typography_records = [
        {
            "element_type": "h1",
            "font_family": "Cairo, sans-serif",
            "font_size_px": 32.0,
            "direction": "rtl",
            "language": "ar",
        },
        {
            "element_type": "p",
            "font_family": "Cairo, sans-serif",
            "font_size_px": 16.0,
            "direction": "rtl",
            "language": "ar",
        },
    ]
    page = PageAnalysisContext(
        page_url="https://test.sa/",
        safe_page_id="p0",
        status="completed",
        typography=typography_records,
    )

    result = TypographyAnalyzer.analyze_typography([page], evidence_index={})
    assert result["arabic_rtl_supported"] is True
    assert "Cairo" in result["font_families"]
    assert result["heading_to_body_ratio"] == 2.0
    assert len(result["findings"]) == 0
