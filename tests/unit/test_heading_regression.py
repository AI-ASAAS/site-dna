"""Regression test verifying H1, H2, and H3 extraction, hierarchy, and serialization."""

import json
from pathlib import Path

from site_dna.discovery.extractor import extract_page_content
from site_dna.schemas.page import PageData


def test_heading_extraction_hierarchy_and_serialization():
    fixture_path = Path("tests/fixtures/discovery/heading_test.html")
    html_content = fixture_path.read_text(encoding="utf-8")

    # Step 1: Verify direct heading extraction
    content = extract_page_content(html_content, "https://example.com/")
    headings = content.headings

    assert len(headings) == 3, f"Expected 3 headings, got {len(headings)}"

    # Check hierarchy and levels
    assert headings[0].level == 1
    assert headings[0].text == "Example Domain"

    assert headings[1].level == 2
    assert headings[1].text == "About This Website"

    assert headings[2].level == 3
    assert headings[2].text == "Additional Information"

    # Step 2: Verify PageData model assembling
    page = PageData(
        url="https://example.com/",
        final_url="https://example.com/",
        status_code=200,
        depth=0,
        metadata=content.metadata,
        headings=headings,
        main_content_text=content.main_content_text,
        word_count=content.word_count,
        navigation_links=content.navigation_links,
        buttons=content.buttons,
        images=content.images,
        forms=content.forms,
    )

    assert len(page.headings) == 3

    # Step 3: Verify JSON serialization and deserialization
    json_str = page.model_dump_json()
    data = json.loads(json_str)

    assert "headings" in data
    assert len(data["headings"]) == 3
    assert data["headings"][0]["level"] == 1
    assert data["headings"][0]["text"] == "Example Domain"
    assert data["headings"][1]["level"] == 2
    assert data["headings"][1]["text"] == "About This Website"
    assert data["headings"][2]["level"] == 3
    assert data["headings"][2]["text"] == "Additional Information"
