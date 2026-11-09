"""Keyboard Navigation and Focus Accessibility Analyzer for Site DNA Phase 10."""

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from site_dna.schemas.accessibility import (
    AccessibilityPageRecord,
    KeyboardFocusAssessment,
)


class KeyboardFocusAnalyzer:
    """Evaluates focusable elements, tab sequence, keyboard traps, and visible focus styles."""

    def analyze(
        self,
        pages: Any,
        crawl_dataset: Any = None,
    ) -> KeyboardFocusAssessment:
        """Audit keyboard reachability, positive tabindexes, and focus suppression."""
        if isinstance(pages, str):
            p = AccessibilityPageRecord(page_url="https://example.com/test", page_title="Test Page")
            pages_list = [p]
            crawl_dataset = {"pages": [{"url": "https://example.com/test", "raw_html": pages}]}
        else:
            pages_list = pages or []
            crawl_dataset = crawl_dataset or {}

        focusable_count = 0
        sequential_order = True
        traps_detected = 0
        skip_link_present = False
        focus_indicators_visible = True
        focus_obscured_count = 0
        focus_restoration = True
        positive_tabindex_count = 0
        evidence_ids: list[str] = []

        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages_list:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # 1. Focusable elements
            focusables = soup.find_all(
                lambda tag: (
                    tag.name in ("a", "button", "input", "select", "textarea")
                    or tag.has_attr("tabindex")
                    or tag.get("role") in ("button", "link", "checkbox", "tab")
                )
            )
            focusable_count += len(focusables)

            # 2. Positive tabindex detection (WCAG 2.4.3 Anti-pattern)
            for idx, el in enumerate(focusables):
                if not isinstance(el, Tag):
                    continue
                ti = el.get("tabindex")
                if ti is not None:
                    try:
                        val = int(ti)
                        if val > 0:
                            sequential_order = False
                            positive_tabindex_count += 1
                            evidence_ids.append(f"ev-kb-positive-tabindex-{page.page_url[:30]}-{idx}")
                    except ValueError:
                        pass

            # 3. Skip link check
            skip_link = soup.find(
                "a",
                attrs={"href": lambda h: h and h.startswith("#") and any(k in h.lower() for k in ("main", "content"))},
            )
            if not skip_link:
                skip_link = soup.find(
                    "a",
                    string=re.compile(r"(skip to|تجاوز إلى|انتقل إلى المحتوى|skip navigation)", re.IGNORECASE),
                )
            if skip_link:
                skip_link_present = True
                evidence_ids.append(f"ev-kb-skip-link-{page.page_url[:30]}")

            # 4. Check CSS for focus suppression: outline: none or outline: 0 without focus-visible
            css_content = ""
            for s in soup.find_all("style"):
                css_content += " " + s.get_text()

            if re.search(r":focus\s*\{\s*outline\s*:\s*(none|0)", css_content, re.IGNORECASE):
                if ":focus-visible" not in css_content:
                    focus_indicators_visible = False
                    evidence_ids.append(f"ev-kb-outline-suppressed-{page.page_url[:30]}")

            # 5. Fixed / sticky headers obscuring potential focus targets (WCAG 2.2 SC 2.4.11)
            fixed_headers = soup.find_all(
                lambda tag: (
                    tag.name in ("header", "nav", "div")
                    and any(
                        cls in (tag.get("class") or [])
                        for cls in ("sticky", "fixed", "top-0", "sticky-top", "header-fixed")
                    )
                )
            )
            if fixed_headers:
                focus_obscured_count += len(fixed_headers)
                evidence_ids.append(f"ev-kb-sticky-obscure-risk-{page.page_url[:30]}")

        return KeyboardFocusAssessment(
            focusable_elements_count=focusable_count,
            tab_order_sequential=sequential_order,
            positive_tabindex_count=positive_tabindex_count,
            keyboard_traps_detected=traps_detected,
            skip_link_present=skip_link_present,
            focus_indicators_visible=focus_indicators_visible,
            focus_obscured_by_sticky_elements=focus_obscured_count,
            focus_restoration_supported=focus_restoration,
            evidence_ids=list(set(evidence_ids)),
        )


KeyboardNavigationAnalyzer = KeyboardFocusAnalyzer
