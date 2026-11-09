"""Accessible Name and Description Computation Engine for Site DNA Phase 10 (W3C AccName 1.2)."""

from typing import Any, Optional

from bs4 import BeautifulSoup, Tag

from site_dna.schemas.accessibility import (
    AccessibilityPageRecord,
    AccessibleNameRecord,
)


class AccessibleNameAnalyzer:
    """Evaluates accessible names for interactive controls, buttons, links, and form fields."""

    def analyze(
        self,
        pages: Any,
        crawl_dataset: Any = None,
    ) -> list[AccessibleNameRecord]:
        """Compute verifiable accessible names and inspect for naming defects."""
        if isinstance(pages, str):
            p = AccessibilityPageRecord(page_url="https://example.com/test", page_title="Test Page")
            pages_list = [p]
            crawl_dataset = {"pages": [{"url": "https://example.com/test", "raw_html": pages}]}
        else:
            pages_list = pages or []
            crawl_dataset = crawl_dataset or {}

        records: list[AccessibleNameRecord] = []
        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages_list:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            id_map: set[str] = {tag["id"] for tag in soup.find_all(id=True)}

            # Find interactive elements: button, a, input, select, textarea, role=button
            elements = soup.find_all(["button", "a", "input", "select", "textarea"]) + soup.find_all(
                attrs={"role": lambda r: r in ("button", "link", "checkbox", "radio", "tab")}
            )

            for idx, el in enumerate(elements):
                if not isinstance(el, Tag):
                    continue

                # Skip hidden elements
                if el.get("type") == "hidden" or el.get("aria-hidden") == "true":
                    continue

                tag_name = el.name
                role = el.get("role")
                element_id = el.get("id") or f"{tag_name}-{idx}"
                element_ref = f"{tag_name}#{element_id}"

                acc_name: Optional[str] = None
                source: str = "missing"
                visible_text = el.get_text(strip=True) if tag_name not in ("input", "select") else None
                conflicting = False
                broken_ref = False

                # 1. aria-labelledby
                if el.has_attr("aria-labelledby"):
                    target_ids = el["aria-labelledby"].split()
                    parts = []
                    for tid in target_ids:
                        if tid in id_map:
                            target_tag = soup.find(id=tid)
                            if target_tag:
                                parts.append(target_tag.get_text(strip=True))
                        else:
                            broken_ref = True
                    if parts:
                        acc_name = " ".join(parts).strip()
                        source = "aria_labelledby"

                # 2. aria-label (overrides native text if present)
                if not acc_name and el.has_attr("aria-label"):
                    al_val = el["aria-label"].strip()
                    if al_val:
                        acc_name = al_val
                        source = "aria_label"

                # 3. Native <label> for inputs
                if not acc_name and tag_name in ("input", "select", "textarea"):
                    # Explicit label via for=
                    if el.get("id"):
                        lbl = soup.find("label", attrs={"for": el["id"]})
                        if lbl:
                            acc_name = lbl.get_text(strip=True)
                            source = "native_label"
                    # Wrapping label
                    if not acc_name:
                        parent_lbl = el.find_parent("label")
                        if parent_lbl:
                            acc_name = parent_lbl.get_text(strip=True)
                            source = "native_label"

                # 4. Text content for button / a
                if not acc_name and visible_text:
                    acc_name = visible_text
                    source = "text_content"

                # 5. Alt attribute for input[type=image] or inner img
                if not acc_name:
                    if tag_name == "input" and el.get("type") == "image":
                        acc_name = el.get("alt", "").strip()
                        source = "alt_attribute" if acc_name else "missing"
                    else:
                        inner_img = el.find("img")
                        if inner_img and inner_img.get("alt"):
                            acc_name = inner_img["alt"].strip()
                            source = "alt_attribute"

                # 6. Title fallback
                if not acc_name and el.has_attr("title"):
                    t_val = el["title"].strip()
                    if t_val:
                        acc_name = t_val
                        source = "title_attribute"

                # Check conflict (e.g. aria-label conflicting with visible text or broken ref)
                if broken_ref:
                    source = "conflicting"
                    conflicting = True

                name_matches = True
                if visible_text and acc_name and source == "aria_label":
                    # WCAG 2.5.3: Accessible name should contain the visible label text
                    if visible_text.lower() not in acc_name.lower():
                        name_matches = False

                rec = AccessibleNameRecord(
                    element_ref=element_ref,
                    tag_name=tag_name,
                    role=role,
                    accessible_name=acc_name if acc_name else None,
                    name_source=source,  # type: ignore
                    visible_text=visible_text,
                    name_matches_visible=name_matches,
                    has_conflicting_labels=conflicting,
                    evidence_id=f"ev-name-{element_ref[:30]}-{idx}",
                )
                records.append(rec)

        return records


AccessibleNamesAnalyzer = AccessibleNameAnalyzer
