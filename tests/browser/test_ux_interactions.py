"""Browser and geometry tests for UX interaction targets and touch bounding boxes."""

from site_dna.analysis.ux_ui.context_builder import UXPageContext
from site_dna.analysis.ux_ui.interaction_analyzer import InteractionAnalyzer


def test_interaction_touch_target_bounds():
    """Verify touch target minimum bounding box calculations."""
    page = UXPageContext(
        page_url="https://test.com/",
        safe_page_id="p1",
        status="completed",
        dom_elements=[
            {
                "tag_name": "button",
                "text": "Large Button",
                "accessible_name": "Large Button",
                "is_interactive": True,
                "bounding_box": {"x": 10, "y": 10, "width": 48, "height": 48},
            },
            {
                "tag_name": "button",
                "text": "Tiny Target",
                "accessible_name": "Tiny Target",
                "is_interactive": True,
                "bounding_box": {"x": 100, "y": 10, "width": 20, "height": 20},
            },
        ],
    )

    assessment = InteractionAnalyzer.analyze_interactions([page], evidence_index={})
    assert len(assessment.small_touch_targets) == 1
    assert assessment.small_touch_targets[0]["width"] == 20
    assert assessment.small_touch_targets[0]["height"] == 20
    assert any("أصغر من الحد الأدنى" in f.title or "المس" in f.title for f in assessment.findings)
