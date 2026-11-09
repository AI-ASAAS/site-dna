"""Unit tests for Keyboard Navigation, Focus Management, and Target Size Analyzers."""

from pathlib import Path

from site_dna.analysis.accessibility.focus_management import FocusManagementAnalyzer
from site_dna.analysis.accessibility.keyboard_navigation import KeyboardNavigationAnalyzer
from site_dna.analysis.accessibility.target_size import TargetSizeAnalyzer

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "accessibility"


def test_accessible_site_keyboard():
    html = (FIXTURES_DIR / "accessible_site.html").read_text(encoding="utf-8")
    analyzer = KeyboardNavigationAnalyzer()
    res = analyzer.analyze(html)

    assert res.tab_order_sequential is True
    assert res.skip_link_present is True
    assert res.focus_indicators_visible is True


def test_inaccessible_site_keyboard():
    html = (FIXTURES_DIR / "inaccessible_site.html").read_text(encoding="utf-8")
    analyzer = KeyboardNavigationAnalyzer()
    res = analyzer.analyze(html)

    # Positive tabindex anti-pattern present
    assert res.tab_order_sequential is False
    assert res.positive_tabindex_count >= 1
    # outline: none without focus-visible
    assert res.focus_indicators_visible is False
    assert res.skip_link_present is False


def test_focus_management_sticky_elements():
    html = (FIXTURES_DIR / "inaccessible_site.html").read_text(encoding="utf-8")
    analyzer = FocusManagementAnalyzer()
    res = analyzer.analyze(html)

    # Detects sticky/fixed overlay that may obscure focus
    assert res.focus_obscured_by_sticky_elements >= 1


def test_target_size_analyzer():
    html = (FIXTURES_DIR / "inaccessible_site.html").read_text(encoding="utf-8")
    analyzer = TargetSizeAnalyzer()
    res = analyzer.analyze(html)

    # Detects 14px small button failing 24x24px threshold
    assert res.evaluated_targets_count >= 1
    assert res.targets_meeting_24px_threshold < res.evaluated_targets_count
