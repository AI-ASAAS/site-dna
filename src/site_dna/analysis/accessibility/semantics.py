"""Semantic HTML and Landmark Structure Analyzer for Site DNA Phase 10."""

import re
from typing import Any

from bs4 import BeautifulSoup

from site_dna.schemas.accessibility import (
    AccessibilityPageRecord,
    SemanticAssessment,
)


class SemanticHTMLAnalyzer:
    """Evaluates semantic HTML structure, landmarks, native controls, and table headers."""

    def analyze(
        self,
        pages: Any,
        crawl_dataset: Any = None,
    ) -> SemanticAssessment:
        """Evaluate landmark availability, headings hierarchy, and native vs non-semantic controls."""
        if isinstance(pages, str):
            p = AccessibilityPageRecord(page_url="https://example.com/test", page_title="Test Page")
            pages_list = [p]
            crawl_dataset = {"pages": [{"url": "https://example.com/test", "raw_html": pages}]}
        else:
            pages_list = pages or []
            crawl_dataset = crawl_dataset or {}

        has_main = False
        nav_count = 0
        heading_levels_seen: set[int] = set()
        hierarchy_valid = True
        prev_level = 0

        buttons_count = 0
        fake_buttons_count = 0
        tables_with_th = 0
        unheaded_tables = 0
        evidence_ids: list[str] = []

        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages_list:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # Check <main> landmark or role="main"
            if soup.find("main") or soup.find(attrs={"role": "main"}):
                has_main = True
                evidence_ids.append(f"ev-sem-main-{page.page_url[:30]}")

            # Check <nav> landmarks
            navs = soup.find_all(["nav"]) + soup.find_all(attrs={"role": "navigation"})
            nav_count += len(navs)
            if navs:
                evidence_ids.append(f"ev-sem-nav-{page.page_url[:30]}")

            # Check headings hierarchy
            headings = soup.find_all(re.compile(r"^h[1-6]$"))
            for h in headings:
                try:
                    lvl = int(h.name[1])
                    heading_levels_seen.add(lvl)
                    # Detect skips (e.g., h1 followed directly by h3 without h2)
                    if prev_level > 0 and lvl > prev_level + 1:
                        hierarchy_valid = False
                        evidence_ids.append(f"ev-sem-skip-h{prev_level}-to-h{lvl}")
                    prev_level = lvl
                except (ValueError, IndexError):
                    pass

            # Buttons vs clickable divs/spans
            native_buttons = soup.find_all("button") + soup.find_all(
                "input", attrs={"type": lambda t: t in ("button", "submit", "reset")}
            )
            buttons_count += len(native_buttons)

            # Look for non-semantic elements acting like buttons
            fake_buttons = soup.find_all(
                lambda tag: (
                    tag.name in ("div", "span", "a")
                    and (
                        tag.get("role") == "button"
                        or tag.has_attr("onclick")
                        or (tag.has_attr("tabindex") and tag.name not in ("button", "input", "select", "textarea"))
                    )
                )
            )
            fake_buttons_count += len(fake_buttons)
            if fake_buttons:
                evidence_ids.append(f"ev-sem-non-semantic-button-{page.page_url[:30]}")

            # Data Tables
            tables = soup.find_all("table")
            for tbl in tables:
                ths = tbl.find_all("th")
                if ths:
                    tables_with_th += 1
                else:
                    # Table with rows/td but no th
                    if tbl.find_all("td"):
                        unheaded_tables += 1
                        evidence_ids.append(f"ev-sem-unheaded-table-{page.page_url[:30]}")

        # Compute semantic score
        score = 100.0
        if not has_main:
            score -= 25.0
        if not hierarchy_valid:
            score -= 15.0
        if unheaded_tables > 0:
            score -= min(15.0, unheaded_tables * 5.0)
        if fake_buttons_count > 0:
            ratio = buttons_count / max(1, buttons_count + fake_buttons_count)
            if ratio < 0.7:
                score -= 15.0

        btn_ratio = round(buttons_count / max(1, buttons_count + fake_buttons_count), 2)

        return SemanticAssessment(
            has_main_landmark=has_main,
            nav_landmarks_count=nav_count,
            headings_hierarchy_valid=hierarchy_valid,
            heading_levels_present=sorted(list(heading_levels_seen)),
            buttons_vs_divs_ratio=btn_ratio,
            non_semantic_clickables_count=fake_buttons_count,
            data_tables_with_headers=tables_with_th,
            unheaded_tables_count=unheaded_tables,
            semantic_score=max(0.0, score),
            evidence_ids=list(set(evidence_ids)),
        )


SemanticsAnalyzer = SemanticHTMLAnalyzer
