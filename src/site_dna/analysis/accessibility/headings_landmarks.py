"""Headings Hierarchy and Landmark Navigation Analyzer for Site DNA Phase 10."""

import re
from typing import Any

from bs4 import BeautifulSoup

from site_dna.schemas.accessibility import AccessibilityPageRecord


class HeadingsLandmarksResult:
    """Structured result for headings and landmarks analysis."""

    def __init__(self, data: dict[str, Any], h1_count: int, has_skipped_levels: bool):
        self._data = data
        self.h1_count = h1_count
        self.has_skipped_levels = has_skipped_levels
        for k, v in data.items():
            setattr(self, k, v)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


class HeadingsLandmarksAnalyzer:
    """Evaluates heading levels, landmark structures, and skip-link availability."""

    def analyze(
        self,
        pages: Any,
        crawl_dataset: Any = None,
    ) -> HeadingsLandmarksResult:
        """Analyze headings structure and skip links."""
        if isinstance(pages, str):
            p = AccessibilityPageRecord(page_url="https://example.com/test", page_title="Test Page")
            pages_list = [p]
            crawl_dataset = {"pages": [{"url": "https://example.com/test", "raw_html": pages}]}
        else:
            pages_list = pages or []
            crawl_dataset = crawl_dataset or {}

        h1_missing_pages: list[str] = []
        multiple_h1_pages: list[str] = []
        hierarchy_skips: list[dict[str, Any]] = []
        skip_links_found: list[str] = []
        total_h1_count = 0
        evidence_ids: list[str] = []

        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages_list:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # H1 check
            h1s = soup.find_all("h1")
            total_h1_count += len(h1s)
            if not h1s:
                h1_missing_pages.append(page.page_url)
                evidence_ids.append(f"ev-hl-missing-h1-{page.page_url[:30]}")
            elif len(h1s) > 1:
                multiple_h1_pages.append(page.page_url)

            # Skip-navigation link check
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
                skip_links_found.append(page.page_url)
                evidence_ids.append(f"ev-hl-skip-link-{page.page_url[:30]}")

            # Hierarchy skips
            headings = soup.find_all(re.compile(r"^h[1-6]$"))
            last_level = 0
            for h in headings:
                lvl = int(h.name[1])
                if last_level > 0 and lvl > last_level + 1:
                    hierarchy_skips.append(
                        {
                            "page_url": page.page_url,
                            "from_level": last_level,
                            "to_level": lvl,
                            "text": h.get_text(strip=True)[:50],
                        }
                    )
                    evidence_ids.append(f"ev-hl-skip-h{last_level}-to-h{lvl}")
                last_level = lvl

        res_data = {
            "h1_missing_pages": h1_missing_pages,
            "multiple_h1_pages": multiple_h1_pages,
            "hierarchy_skips": hierarchy_skips,
            "has_skip_navigation": len(skip_links_found) > 0,
            "evidence_ids": list(set(evidence_ids)),
        }
        return HeadingsLandmarksResult(
            data=res_data,
            h1_count=total_h1_count,
            has_skipped_levels=len(hierarchy_skips) > 0,
        )
