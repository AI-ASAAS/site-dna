"""Pointer Target Size (Minimum) Analyzer for Site DNA Phase 10 (WCAG 2.2 SC 2.5.8)."""

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from site_dna.schemas.accessibility import (
    AccessibilityPageRecord,
    TargetSizeAssessment,
)


class TargetSizeAnalyzer:
    """Evaluates interactive target dimensions against WCAG 2.2 SC 2.5.8 (24x24px baseline)."""

    def analyze(
        self,
        pages: Any,
        crawl_dataset: Any = None,
    ) -> TargetSizeAssessment:
        """Audit button, link, and input dimensions and spacing exceptions."""
        if isinstance(pages, str):
            p = AccessibilityPageRecord(page_url="https://example.com/test", page_title="Test Page")
            pages_list = [p]
            crawl_dataset = {"pages": [{"url": "https://example.com/test", "raw_html": pages}]}
        else:
            pages_list = pages or []
            crawl_dataset = crawl_dataset or {}

        total_targets = 0
        below_24px = 0
        exceptions_applied = 0
        confirmed_failures = 0
        sufficient_spacing = 0
        evidence_ids: list[str] = []

        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages_list:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # Also parse dimensions from <style> blocks
            style_class_dims: dict[str, tuple[int, int]] = {}
            for s_tag in soup.find_all("style"):
                css_text = s_tag.get_text()
                for rule_match in re.finditer(r"\.([a-zA-Z0-9_\-]+)\s*\{([^}]+)\}", css_text):
                    cls_name, body = rule_match.groups()
                    w_m = re.search(r"width\s*:\s*(\d+)px", body, re.I)
                    h_m = re.search(r"height\s*:\s*(\d+)px", body, re.I)
                    if w_m and h_m:
                        style_class_dims[cls_name] = (int(w_m.group(1)), int(h_m.group(1)))

            interactive_elements = (
                soup.find_all(["button", "a", "input", "select"])
                + soup.find_all(attrs={"onclick": True})
                + soup.find_all(attrs={"role": lambda r: r in ("button", "link")})
            )
            # Deduplicate tags
            seen_tags = set()
            unique_interactive = []
            for t in interactive_elements:
                if id(t) not in seen_tags:
                    seen_tags.add(id(t))
                    unique_interactive.append(t)

            total_targets += len(unique_interactive)

            for idx, el in enumerate(unique_interactive):
                if not isinstance(el, Tag):
                    continue

                # Check if it's an inline link within prose text (WCAG 2.5.8 Inline Exception)
                parent_tag = el.parent.name if el.parent else ""
                if el.name == "a" and parent_tag in ("p", "li", "span", "article"):
                    exceptions_applied += 1
                    continue

                style_str = el.get("style", "").lower()
                w_match = re.search(r"width\s*:\s*(\d+)px", style_str)
                h_match = re.search(r"height\s*:\s*(\d+)px", style_str)

                w, h = 24, 24
                has_dim = False
                if w_match or h_match:
                    w = int(w_match.group(1)) if w_match else 24
                    h = int(h_match.group(1)) if h_match else 24
                    has_dim = True
                else:
                    for cls in el.get("class") or []:
                        if cls in style_class_dims:
                            w, h = style_class_dims[cls]
                            has_dim = True
                            break

                if has_dim:
                    if w < 24 or h < 24:
                        below_24px += 1
                        # Check margin / padding spacing
                        padding_match = re.search(r"padding\s*:\s*(\d+)px", style_str)
                        if padding_match and int(padding_match.group(1)) >= 8:
                            sufficient_spacing += 1
                            exceptions_applied += 1
                        else:
                            confirmed_failures += 1
                            evidence_ids.append(f"ev-target-small-{el.name}-{page.page_url[:20]}-{idx}")

        return TargetSizeAssessment(
            total_interactive_targets=total_targets,
            targets_below_24px=below_24px,
            targets_with_sufficient_spacing=sufficient_spacing,
            target_size_exceptions_applied=exceptions_applied,
            confirmed_target_size_failures=confirmed_failures,
            evidence_ids=list(set(evidence_ids)),
        )
