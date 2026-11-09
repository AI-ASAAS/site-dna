"""Link Purpose and Navigation Context Analyzer for Site DNA Phase 10 (WCAG 2.4.4 & 2.4.9)."""

from typing import Any

from bs4 import BeautifulSoup, Tag

from site_dna.schemas.accessibility import AccessibilityPageRecord

AMBIGUOUS_TEXTS = {
    "click here",
    "read more",
    "more",
    "learn more",
    "details",
    "here",
    "link",
    "view",
    "اضغط هنا",
    "اقرأ المزيد",
    "المزيد",
    "التفاصيل",
    "هنا",
    "عرض المزيد",
    "شاهد المزيد",
}


class LinksNavigationAnalyzer:
    """Evaluates link names, ambiguous link purpose, and empty navigation elements."""

    def analyze(
        self,
        pages: list[AccessibilityPageRecord],
        crawl_dataset: dict[str, Any],
    ) -> dict[str, Any]:
        """Audit links for empty names, vague text, and context clarity."""
        empty_links: list[dict[str, Any]] = []
        ambiguous_links: list[dict[str, Any]] = []
        evidence_ids: list[str] = []

        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            links = soup.find_all("a")

            for idx, a in enumerate(links):
                if not isinstance(a, Tag):
                    continue

                href = a.get("href", "")
                if not href or href.startswith("javascript:"):
                    continue

                text = a.get_text(strip=True).lower()
                aria_label = (a.get("aria-label") or "").strip()
                title = (a.get("title") or "").strip()
                has_img_alt = False

                for img in a.find_all("img"):
                    if img.get("alt", "").strip():
                        has_img_alt = True
                        break

                effective_name = aria_label or text or title or ("img" if has_img_alt else "")

                if not effective_name:
                    empty_links.append(
                        {
                            "page_url": page.page_url,
                            "href": href[:80],
                            "selector": f"a[href='{href[:40]}']",
                        }
                    )
                    evidence_ids.append(f"ev-link-empty-{page.page_url[:30]}-{idx}")
                elif effective_name.lower() in AMBIGUOUS_TEXTS:
                    ambiguous_links.append(
                        {
                            "page_url": page.page_url,
                            "href": href[:80],
                            "text": text,
                            "aria_label": aria_label,
                        }
                    )
                    evidence_ids.append(f"ev-link-ambiguous-{page.page_url[:30]}-{idx}")

        return {
            "empty_links_count": len(empty_links),
            "empty_links": empty_links,
            "ambiguous_links_count": len(ambiguous_links),
            "ambiguous_links": ambiguous_links,
            "evidence_ids": list(set(evidence_ids)),
        }
