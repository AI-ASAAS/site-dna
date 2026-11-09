"""Focus Management and Obscured Focus Analyzer for Site DNA Phase 10 (WCAG 2.4.7, 2.4.11, 2.4.12)."""

from typing import Any

from bs4 import BeautifulSoup, Tag

from site_dna.schemas.accessibility import AccessibilityPageRecord


class FocusManagementResult:
    """Structured result for focus management analysis."""

    def __init__(self, data: dict[str, Any], focus_obscured: int):
        self._data = data
        self.focus_obscured_by_sticky_elements = focus_obscured
        for k, v in data.items():
            setattr(self, k, v)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)


class FocusManagementAnalyzer:
    """Evaluates modal focus trapping, focus restoration, and obscured focus risks."""

    def analyze(
        self,
        pages: Any,
        crawl_dataset: Any = None,
    ) -> FocusManagementResult:
        """Audit modals, dialogs, and sticky overlay obstructions."""
        if isinstance(pages, str):
            p = AccessibilityPageRecord(page_url="https://example.com/test", page_title="Test Page")
            pages_list = [p]
            crawl_dataset = {"pages": [{"url": "https://example.com/test", "raw_html": pages}]}
        else:
            pages_list = pages or []
            crawl_dataset = crawl_dataset or {}

        modals_without_aria_modal: list[dict[str, Any]] = []
        dialogs_missing_title: list[dict[str, Any]] = []
        sticky_elements: list[dict[str, Any]] = []
        evidence_ids: list[str] = []

        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages_list:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # Look for dialogs / modals
            dialogs = soup.find_all(lambda tag: tag.name == "dialog" or tag.get("role") in ("dialog", "alertdialog"))
            for idx, d in enumerate(dialogs):
                if not isinstance(d, Tag):
                    continue

                if not d.get("aria-modal") and d.name != "dialog":
                    modals_without_aria_modal.append(
                        {
                            "page_url": page.page_url,
                            "tag": d.name,
                            "id": d.get("id"),
                        }
                    )
                    evidence_ids.append(f"ev-focus-no-aria-modal-{page.page_url[:30]}-{idx}")

                has_title = (
                    bool(d.get("aria-labelledby")) or bool(d.get("aria-label")) or bool(d.find(["h1", "h2", "h3"]))
                )
                if not has_title:
                    dialogs_missing_title.append(
                        {
                            "page_url": page.page_url,
                            "tag": d.name,
                            "id": d.get("id"),
                        }
                    )
                    evidence_ids.append(f"ev-focus-dialog-no-title-{page.page_url[:30]}-{idx}")

            # Check sticky / fixed elements for potential WCAG 2.4.11 / 2.4.12 overlap
            stickies = soup.find_all(
                lambda tag: (
                    any(
                        "sticky" in cls or "fixed" in cls or "top-0" in cls or "bottom-0" in cls
                        for cls in (tag.get("class") or [])
                    )
                    or (
                        tag.has_attr("style")
                        and (
                            "position:fixed" in tag["style"].replace(" ", "").lower()
                            or "position:sticky" in tag["style"].replace(" ", "").lower()
                        )
                    )
                )
            )
            for idx, s in enumerate(stickies):
                sticky_elements.append(
                    {
                        "page_url": page.page_url,
                        "tag": s.name,
                        "class": s.get("class"),
                    }
                )
                evidence_ids.append(f"ev-focus-sticky-{page.page_url[:30]}-{idx}")

        res_data = {
            "modals_without_aria_modal": modals_without_aria_modal,
            "dialogs_missing_title": dialogs_missing_title,
            "sticky_overlays_count": len(sticky_elements),
            "evidence_ids": list(set(evidence_ids)),
        }
        return FocusManagementResult(
            data=res_data,
            focus_obscured=len(sticky_elements),
        )
