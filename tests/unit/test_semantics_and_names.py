"""Unit tests for Accessibility Semantics, Accessible Names, and Forms Analyzers."""

from pathlib import Path

from site_dna.analysis.accessibility.accessible_names import AccessibleNamesAnalyzer
from site_dna.analysis.accessibility.forms_labels import FormsLabelsAnalyzer
from site_dna.analysis.accessibility.headings_landmarks import HeadingsLandmarksAnalyzer
from site_dna.analysis.accessibility.images_and_media import ImagesMediaAnalyzer
from site_dna.analysis.accessibility.semantics import SemanticsAnalyzer

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "accessibility"


def test_accessible_site_semantics():
    html = (FIXTURES_DIR / "accessible_site.html").read_text(encoding="utf-8")
    analyzer = SemanticsAnalyzer()
    res = analyzer.analyze(html)

    assert res.has_main_landmark is True
    assert res.nav_landmarks_count >= 1
    assert res.headings_hierarchy_valid is True
    assert res.unheaded_tables_count == 0
    assert res.data_tables_with_headers >= 1


def test_inaccessible_site_semantics():
    html = (FIXTURES_DIR / "inaccessible_site.html").read_text(encoding="utf-8")
    analyzer = SemanticsAnalyzer()
    res = analyzer.analyze(html)

    assert res.has_main_landmark is False
    assert res.headings_hierarchy_valid is False
    assert res.unheaded_tables_count >= 1


def test_accessible_names_computation():
    html = (FIXTURES_DIR / "accessible_site.html").read_text(encoding="utf-8")
    analyzer = AccessibleNamesAnalyzer()
    names = analyzer.analyze(html)

    # Name computation for labeled inputs
    email_entry = next((n for n in names if "user-email" in n.element_html), None)
    assert email_entry is not None
    assert "البريد الإلكتروني" in email_entry.computed_name
    assert email_entry.naming_source == "label_for"


def test_forms_labels_analyzer():
    html = (FIXTURES_DIR / "accessible_site.html").read_text(encoding="utf-8")
    analyzer = FormsLabelsAnalyzer()
    form_res = analyzer.analyze(html)

    assert form_res.total_form_inputs >= 2
    assert form_res.unlabeled_inputs == 0
    assert form_res.inputs_with_explicit_labels >= 2
    assert form_res.error_messages_programmatically_associated >= 1


def test_images_media_analyzer():
    html = (FIXTURES_DIR / "inaccessible_site.html").read_text(encoding="utf-8")
    analyzer = ImagesMediaAnalyzer()
    media_res = analyzer.analyze(html)

    assert media_res.total_images >= 2
    assert media_res.missing_alt_count >= 1


def test_headings_landmarks_analyzer():
    html = (FIXTURES_DIR / "inaccessible_site.html").read_text(encoding="utf-8")
    analyzer = HeadingsLandmarksAnalyzer()
    headings_res = analyzer.analyze(html)

    assert headings_res.h1_count == 0
    assert headings_res.has_skipped_levels is True
