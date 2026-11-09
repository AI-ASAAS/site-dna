"""Automated Accessibility Rule Engine Adapter for Site DNA Phase 10 (axe-core compatible)."""

from typing import Any

from bs4 import BeautifulSoup, Tag

from site_dna.schemas.accessibility import (
    AccessibilityPageRecord,
    AutomatedRuleResult,
)


class AutomatedRulesAdapter:
    """Executes deterministic accessibility rule checks aligned with standard axe-core rules."""

    def evaluate_rules(
        self,
        pages: list[AccessibilityPageRecord],
        crawl_dataset: dict[str, Any],
    ) -> list[AutomatedRuleResult]:
        """Run automated rule evaluation over HTML trees."""
        results: list[AutomatedRuleResult] = []
        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # Rule 1: html-has-lang
            html_tag = soup.find("html")
            if not html_tag or not html_tag.get("lang"):
                results.append(
                    AutomatedRuleResult(
                        rule_id="html-has-lang",
                        engine="axe-core-compatible",
                        ruleset_version="4.10.0",
                        impact="serious",
                        wcag_tags=["cat.language", "wcag2a", "wcag311"],
                        selector="html",
                        html_snippet="<html>",
                        failure_summary="<html> element does not have a lang attribute.",
                        failure_summary_ar="عنصر <html> لا يحتوي على سمة لغة المستند lang.",
                        evidence_id=f"ev-rule-html-lang-{page.page_url[:30]}",
                    )
                )

            # Rule 2: document-title
            if not soup.title or not soup.title.string or not soup.title.string.strip():
                results.append(
                    AutomatedRuleResult(
                        rule_id="document-title",
                        engine="axe-core-compatible",
                        ruleset_version="4.10.0",
                        impact="moderate",
                        wcag_tags=["cat.text-alternatives", "wcag2a", "wcag242"],
                        selector="head > title",
                        html_snippet="<title></title>",
                        failure_summary="Document does not have a non-empty <title> element.",
                        failure_summary_ar="المستند لا يحتوي على وسم <title> غير فارغ يوضح عنوان الصفحة.",
                        evidence_id=f"ev-rule-doc-title-{page.page_url[:30]}",
                    )
                )

            # Rule 3: image-alt
            for idx, img in enumerate(soup.find_all("img")):
                if not isinstance(img, Tag):
                    continue
                if not img.has_attr("alt"):
                    results.append(
                        AutomatedRuleResult(
                            rule_id="image-alt",
                            engine="axe-core-compatible",
                            ruleset_version="4.10.0",
                            impact="critical",
                            wcag_tags=["cat.text-alternatives", "wcag2a", "wcag111"],
                            selector=f"img:nth-of-type({idx + 1})",
                            html_snippet=str(img)[:100],
                            failure_summary="Image element does not have an alt attribute.",
                            failure_summary_ar="عنصر الصورة لا يحتوي على سمة النص البديل alt.",
                            evidence_id=f"ev-rule-img-alt-{page.page_url[:20]}-{idx}",
                        )
                    )

            # Rule 4: button-name
            for idx, btn in enumerate(soup.find_all("button")):
                if not isinstance(btn, Tag):
                    continue
                name = btn.get_text(strip=True) or btn.get("aria-label") or btn.get("title")
                if not name and not btn.find("img", attrs={"alt": True}):
                    results.append(
                        AutomatedRuleResult(
                            rule_id="button-name",
                            engine="axe-core-compatible",
                            ruleset_version="4.10.0",
                            impact="critical",
                            wcag_tags=["cat.name-role-value", "wcag2a", "wcag412"],
                            selector=f"button:nth-of-type({idx + 1})",
                            html_snippet=str(btn)[:100],
                            failure_summary="Button does not have an accessible name.",
                            failure_summary_ar="الزر التفاعلي لا يمتلك اسماً متاحاً يمكن لقارئات الشاشة قراءته.",
                            evidence_id=f"ev-rule-btn-name-{page.page_url[:20]}-{idx}",
                        )
                    )

            # Rule 5: duplicate-id
            id_counts: dict[str, int] = {}
            for tag in soup.find_all(id=True):
                tid = tag["id"].strip()
                if tid:
                    id_counts[tid] = id_counts.get(tid, 0) + 1

            for tid, count in id_counts.items():
                if count > 1:
                    results.append(
                        AutomatedRuleResult(
                            rule_id="duplicate-id",
                            engine="axe-core-compatible",
                            ruleset_version="4.10.0",
                            impact="minor",
                            wcag_tags=["cat.parsing", "wcag2a", "wcag411"],
                            selector=f"#{tid}",
                            html_snippet=f'id="{tid}" (repeated {count} times)',
                            failure_summary=f"ID attribute '{tid}' is duplicated across {count} elements.",
                            failure_summary_ar=f"معرف ID '{tid}' مكرر عبر {count} عناصر في الصفحة، مما يكسر ارتباطات ARIA.",
                            evidence_id=f"ev-rule-duplicate-id-{tid}-{page.page_url[:20]}",
                        )
                    )

        return results
