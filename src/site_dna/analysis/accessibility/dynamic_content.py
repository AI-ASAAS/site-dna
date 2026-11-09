"""Dynamic Interfaces, Widgets & State Attributes Analyzer for Site DNA Phase 10."""

from typing import Any

from bs4 import BeautifulSoup, Tag

from site_dna.schemas.accessibility import AccessibilityPageRecord


class DynamicContentAnalyzer:
    """Evaluates tabs, accordions, dialogs, and ARIA state management on dynamic widgets."""

    def analyze(
        self,
        pages: list[AccessibilityPageRecord],
        crawl_dataset: dict[str, Any],
    ) -> dict[str, Any]:
        """Audit widget semantics, expanded states, and tab panel associations."""
        tabs_evaluated = 0
        tabs_properly_associated = 0
        accordions_evaluated = 0
        accordions_missing_expanded = 0
        alerts_present = 0
        evidence_ids: list[str] = []

        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            id_set: set[str] = {tag["id"] for tag in soup.find_all(id=True)}

            # 1. Tabs inspection
            tabs = soup.find_all(attrs={"role": "tab"})
            tabs_evaluated += len(tabs)
            for idx, tab in enumerate(tabs):
                if not isinstance(tab, Tag):
                    continue
                # Tab should have aria-controls pointing to tabpanel and aria-selected
                controls = tab.get("aria-controls")
                has_selected = tab.has_attr("aria-selected")
                if controls and controls in id_set and has_selected:
                    tabs_properly_associated += 1
                else:
                    evidence_ids.append(f"ev-dyn-tab-missing-association-{page.page_url[:20]}-{idx}")

            # 2. Accordions inspection (buttons controlling collapsible sections)
            accordions = soup.find_all(
                lambda tag: (
                    tag.name == "button"
                    and (
                        any(cls in (tag.get("class") or []) for cls in ("accordion", "collapse-toggle", "faq-toggle"))
                        or tag.has_attr("aria-expanded")
                    )
                )
            )
            accordions_evaluated += len(accordions)
            for idx, acc in enumerate(accordions):
                if not isinstance(acc, Tag):
                    continue
                if not acc.has_attr("aria-expanded"):
                    accordions_missing_expanded += 1
                    evidence_ids.append(f"ev-dyn-accordion-no-expanded-{page.page_url[:20]}-{idx}")

            # 3. Live alerts / notifications
            alerts = soup.find_all(attrs={"role": lambda r: r in ("alert", "status", "toast")})
            alerts_present += len(alerts)
            if alerts:
                evidence_ids.append(f"ev-dyn-alert-observed-{page.page_url[:20]}")

        return {
            "tabs_evaluated": tabs_evaluated,
            "tabs_properly_associated": tabs_properly_associated,
            "accordions_evaluated": accordions_evaluated,
            "accordions_missing_expanded": accordions_missing_expanded,
            "alerts_present": alerts_present,
            "evidence_ids": list(set(evidence_ids)),
        }
