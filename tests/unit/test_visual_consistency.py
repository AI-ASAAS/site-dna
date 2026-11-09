"""Unit tests for ConsistencyAnalyzer (cross-page consistency and mobile overflow)."""

from site_dna.analysis.visual_identity.consistency_analyzer import ConsistencyAnalyzer
from site_dna.analysis.visual_identity.context_builder import PageAnalysisContext


def test_consistency_mobile_overflow():
    """Verify that horizontal overflow observation on mobile triggers high-severity finding."""
    page = PageAnalysisContext(
        page_url="https://test.com/",
        safe_page_id="p0",
        status="completed",
        responsive_observations=[
            {
                "observation_type": "horizontal_overflow",
                "status": "failed",
                "description": "Page has horizontal scrollbar on mobile viewport",
                "mobile_value": {"scroll_width": 450, "viewport_width": 375},
            }
        ],
    )

    result = ConsistencyAnalyzer.analyze_consistency([page], evidence_index={})
    assert any("فائض أفقي" in f.title and f.severity == "high" for f in result["findings"])


def test_consistency_single_page_note():
    """Verify that a single-page site reports single-page context note without failing."""
    page = PageAnalysisContext(
        page_url="https://test.com/",
        safe_page_id="p0",
        status="completed",
    )

    result = ConsistencyAnalyzer.analyze_consistency([page], evidence_index={})
    assert result["is_multipage"] is False
    assert "صفحة واحدة فقط" in result["cross_page_note"]


def test_consistency_cross_page_font_discrepancy():
    """Verify that disparate fonts between pages generate an inconsistency finding."""
    page1 = PageAnalysisContext(
        page_url="https://test.com/page1",
        safe_page_id="p1",
        status="completed",
        typography=[{"font_family": "Times New Roman"}],
    )
    page2 = PageAnalysisContext(
        page_url="https://test.com/page2",
        safe_page_id="p2",
        status="completed",
        typography=[{"font_family": "Comic Sans MS"}],
    )

    result = ConsistencyAnalyzer.analyze_consistency([page1, page2], evidence_index={})
    assert result["is_multipage"] is True
    assert any("اختلاف عائلات الخطوط بين الصفحات" in f.title for f in result["findings"])
