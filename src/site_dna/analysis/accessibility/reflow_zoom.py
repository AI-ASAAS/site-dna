"""Responsive Reflow, Viewport Scaling & Text Spacing Analyzer for Site DNA Phase 10 (WCAG 1.4.4 & 1.4.10)."""

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from site_dna.schemas.accessibility import (
    AccessibilityPageRecord,
    ReflowZoomAssessment,
)


class ReflowZoomAnalyzer:
    """Evaluates narrow viewport reflow, fixed container clipping, and horizontal overflow."""

    def analyze(
        self,
        pages: Any,
        crawl_dataset: Any = None,
    ) -> ReflowZoomAssessment:
        """Audit viewport meta tags, fixed width containers, and clipping properties."""
        if isinstance(pages, str):
            p = AccessibilityPageRecord(page_url="https://example.com/test", page_title="Test Page")
            pages_list = [p]
            crawl_dataset = {"pages": [{"url": "https://example.com/test", "raw_html": pages}]}
        else:
            pages_list = pages or []
            crawl_dataset = crawl_dataset or {}

        overflow_at_320 = False
        text_clipping = False
        user_scalable_disabled = False
        content_overlap = False
        two_d_scrolling = False
        evidence_ids: list[str] = []

        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages_list:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # 1. Viewport meta tag check
            meta_viewport = soup.find("meta", attrs={"name": "viewport"})
            if meta_viewport:
                vp_content = meta_viewport.get("content", "").lower()
                # If maximum-scale=1.0 or user-scalable=no, zoom is disabled (WCAG 1.4.4 failure)
                if "user-scalable=no" in vp_content or "maximum-scale=1" in vp_content:
                    text_clipping = True
                    user_scalable_disabled = True
                    evidence_ids.append(f"ev-reflow-zoom-disabled-{page.page_url[:30]}")
                    evidence_ids.append(f"ev-reflow-zoom-disabled-{page.page_url[:30]}")

            # 2. Check for rigid fixed widths exceeding 320px in inline styles
            fixed_wide_elements = soup.find_all(
                lambda tag: (
                    tag.has_attr("style")
                    and bool(re.search(r"width\s*:\s*([4-9]\d{2}|\d{4,})px", tag["style"], re.IGNORECASE))
                )
            )
            for idx, el in enumerate(fixed_wide_elements):
                if not isinstance(el, Tag):
                    continue
                # If it's not a table or video, rigid wide width causes horizontal overflow
                if el.name not in ("table", "video", "iframe"):
                    overflow_at_320 = True
                    evidence_ids.append(f"ev-reflow-fixed-width-{page.page_url[:20]}-{idx}")

            # 3. Check for fixed height with overflow:hidden on text containers
            clipping_elements = soup.find_all(
                lambda tag: (
                    tag.has_attr("style")
                    and "overflow:hidden" in tag["style"].replace(" ", "").lower()
                    and bool(re.search(r"height\s*:\s*\d+px", tag["style"], re.IGNORECASE))
                )
            )
            if clipping_elements:
                text_clipping = True
                for idx, c in enumerate(clipping_elements[:5]):
                    evidence_ids.append(f"ev-reflow-clipping-{page.page_url[:20]}-{idx}")

        return ReflowZoomAssessment(
            horizontal_overflow_at_320px=overflow_at_320,
            text_clipping_observed=text_clipping,
            user_scalable_disabled=user_scalable_disabled,
            content_overlap_observed=content_overlap,
            two_dimensional_scrolling_required=two_d_scrolling,
            evidence_ids=list(set(evidence_ids)),
        )
