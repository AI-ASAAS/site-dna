"""WAI-ARIA Conformance and Attribute Integrity Analyzer for Site DNA Phase 10."""

from typing import Any

from bs4 import BeautifulSoup, Tag

from site_dna.schemas.accessibility import (
    AccessibilityPageRecord,
    ARIAAssessment,
)

VALID_ARIA_ROLES = {
    "alert",
    "alertdialog",
    "application",
    "article",
    "banner",
    "button",
    "cell",
    "checkbox",
    "columnheader",
    "combobox",
    "complementary",
    "contentinfo",
    "definition",
    "dialog",
    "directory",
    "document",
    "feed",
    "figure",
    "form",
    "grid",
    "gridcell",
    "group",
    "heading",
    "img",
    "link",
    "list",
    "listbox",
    "listitem",
    "log",
    "main",
    "marquee",
    "math",
    "menu",
    "menubar",
    "menuitem",
    "menuitemcheckbox",
    "menuitemradio",
    "navigation",
    "none",
    "note",
    "option",
    "presentation",
    "progressbar",
    "radio",
    "radiogroup",
    "region",
    "row",
    "rowgroup",
    "rowheader",
    "scrollbar",
    "search",
    "searchbox",
    "separator",
    "slider",
    "spinbutton",
    "status",
    "switch",
    "tab",
    "table",
    "tablist",
    "tabpanel",
    "term",
    "textbox",
    "timer",
    "toolbar",
    "tooltip",
    "tree",
    "treegrid",
    "treeitem",
}

COMMON_ARIA_TYPOS = {
    "aria-labeledby": "aria-labelledby",
    "aria-requred": "aria-required",
    "aria-describeby": "aria-describedby",
    "aria-disable": "aria-disabled",
    "aria-has-popup": "aria-haspopup",
}


class ARIAAnalyzer:
    """Evaluates WAI-ARIA role correctness, attribute syntax, and broken references."""

    def analyze(
        self,
        pages: list[AccessibilityPageRecord],
        crawl_dataset: dict[str, Any],
    ) -> ARIAAssessment:
        """Audit ARIA attributes across inspected pages."""
        roles_used: set[str] = set()
        invalid_roles: list[str] = []
        unsupported_attrs: list[str] = []
        broken_refs: list[str] = []
        misused_hidden_count = 0
        live_regions = 0
        evidence_ids: list[str] = []

        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            id_set: set[str] = {tag["id"] for tag in soup.find_all(id=True)}

            # 1. Check roles
            elements_with_role = soup.find_all(attrs={"role": True})
            for idx, el in enumerate(elements_with_role):
                if not isinstance(el, Tag):
                    continue
                r_val = (el["role"] or "").strip().lower()
                roles = r_val.split()
                for r in roles:
                    roles_used.add(r)
                    if r not in VALID_ARIA_ROLES:
                        invalid_roles.append(f"{el.name}[role='{r}'] on {page.page_url}")
                        evidence_ids.append(f"ev-aria-invalid-role-{r}-{page.page_url[:20]}-{idx}")

            # 2. Check for common typos and ARIA attributes
            all_tags = soup.find_all(True)
            for idx, tag in enumerate(all_tags):
                if not isinstance(tag, Tag):
                    continue

                for attr in list(tag.attrs.keys()):
                    if attr.lower() in COMMON_ARIA_TYPOS:
                        correct = COMMON_ARIA_TYPOS[attr.lower()]
                        unsupported_attrs.append(f"Typo '{attr}' (should be '{correct}') on {tag.name}")
                        evidence_ids.append(f"ev-aria-typo-{attr}-{page.page_url[:20]}-{idx}")

                # 3. Check broken ID references (aria-labelledby, aria-describedby, aria-controls, aria-owns)
                for ref_attr in ("aria-labelledby", "aria-describedby", "aria-controls", "aria-owns"):
                    if tag.has_attr(ref_attr):
                        target_ids = tag[ref_attr].split()
                        for tid in target_ids:
                            if tid not in id_set:
                                broken_refs.append(f"{ref_attr}='{tid}' missing ID target")
                                evidence_ids.append(f"ev-aria-broken-ref-{tid}-{page.page_url[:20]}-{idx}")

                # 4. Check misused aria-hidden on focusable elements
                if tag.get("aria-hidden") == "true":
                    if tag.name in ("button", "a", "input", "select", "textarea") or tag.has_attr("tabindex"):
                        # If it's a link with href, or button/input not disabled, aria-hidden is a serious barrier
                        if tag.name != "a" or tag.has_attr("href"):
                            misused_hidden_count += 1
                            evidence_ids.append(f"ev-aria-hidden-focusable-{tag.name}-{page.page_url[:20]}-{idx}")

                # 5. Live regions
                if tag.has_attr("aria-live") or tag.get("role") in ("status", "alert", "log"):
                    live_regions += 1
                    evidence_ids.append(f"ev-aria-live-{tag.name}-{page.page_url[:20]}-{idx}")

        return ARIAAssessment(
            aria_roles_used=sorted(list(roles_used)),
            invalid_roles=invalid_roles,
            unsupported_aria_attributes=unsupported_attrs,
            broken_aria_references=broken_refs,
            misused_aria_hidden=misused_hidden_count,
            live_regions_present=live_regions,
            evidence_ids=list(set(evidence_ids)),
        )
