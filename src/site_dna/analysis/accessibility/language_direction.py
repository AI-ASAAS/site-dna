"""Document Language, Direction & Arabic RTL Accessibility Analyzer for Site DNA Phase 10."""

from typing import Any, Optional

from bs4 import BeautifulSoup

from site_dna.schemas.accessibility import (
    AccessibilityPageRecord,
    LanguageDirectionAssessment,
)


class LanguageDirectionAnalyzer:
    """Evaluates HTML language tags, document direction, and Arabic/English bilingual isolation."""

    def analyze(
        self,
        pages: list[AccessibilityPageRecord],
        crawl_dataset: dict[str, Any],
    ) -> LanguageDirectionAssessment:
        """Audit language declarations and bidirectional text handling."""
        lang_declared = True
        primary_lang: Optional[str] = None
        primary_dir: Optional[str] = None
        bilingual_support = False
        mixed_spans_isolated = True
        evidence_ids: list[str] = []

        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            html_tag = soup.find("html")

            if not html_tag or not html_tag.get("lang"):
                lang_declared = False
                evidence_ids.append(f"ev-lang-missing-html-lang-{page.page_url[:30]}")
            else:
                declared_l = (html_tag["lang"] or "").strip().lower()
                if not primary_lang:
                    primary_lang = declared_l
                evidence_ids.append(f"ev-lang-declared-{declared_l}-{page.page_url[:20]}")

            if html_tag and html_tag.get("dir"):
                declared_d = (html_tag["dir"] or "").strip().lower()
                if declared_d in ("rtl", "ltr", "auto") and not primary_dir:
                    primary_dir = declared_d
                evidence_ids.append(f"ev-dir-declared-{declared_d}-{page.page_url[:20]}")

            # Check for bilingual language switcher or alternate language tags
            lang_switches = soup.find_all(
                lambda tag: (
                    tag.name in ("a", "button")
                    and any(w in tag.get_text(strip=True).lower() for w in ("english", "عربي", "en", "ar", "language"))
                )
            )
            if lang_switches:
                bilingual_support = True
                evidence_ids.append(f"ev-lang-switcher-detected-{page.page_url[:20]}")

            # Check inline language of parts (WCAG 3.1.2)
            # If page is Arabic (rtl), check if English blocks have lang="en" or dir="ltr"
            if primary_dir == "rtl" or (primary_lang and "ar" in primary_lang):
                unisolated_english_spans = soup.find_all(
                    lambda tag: (
                        tag.name in ("p", "div", "h2", "h3")
                        and not tag.get("lang")
                        and not tag.get("dir")
                        and tag.name not in ("code", "pre")
                        and len(tag.get_text(strip=True)) > 20
                        and tag.get_text(strip=True).isascii()
                    )
                )
                if unisolated_english_spans:
                    mixed_spans_isolated = False
                    for idx, span in enumerate(unisolated_english_spans[:3]):
                        evidence_ids.append(f"ev-lang-unisolated-english-{page.page_url[:20]}-{idx}")

        return LanguageDirectionAssessment(
            html_lang_declared=lang_declared,
            declared_language=primary_lang,
            declared_direction=primary_dir,  # type: ignore
            bilingual_arabic_english_support=bilingual_support,
            mixed_direction_spans_isolated=mixed_spans_isolated,
            evidence_ids=list(set(evidence_ids)),
        )
