"""Form Labels, Controls & Error Association Analyzer for Site DNA Phase 10."""

from typing import Any

from bs4 import BeautifulSoup, Tag

from site_dna.schemas.accessibility import (
    AccessibilityPageRecord,
    FormAccessibilityAssessment,
)


class FormAccessibilityAnalyzer:
    """Evaluates form control labels, required indicators, error descriptions, and grouping."""

    def analyze(
        self,
        pages: Any,
        crawl_dataset: Any = None,
    ) -> FormAccessibilityAssessment:
        """Audit forms for explicit labeling, error association, and accessible authentication."""
        if isinstance(pages, str):
            p = AccessibilityPageRecord(page_url="https://example.com/test", page_title="Test Page")
            pages_list = [p]
            crawl_dataset = {"pages": [{"url": "https://example.com/test", "raw_html": pages}]}
        else:
            pages_list = pages or []
            crawl_dataset = crawl_dataset or {}

        total_inputs = 0
        labeled_inputs = 0
        unlabeled_inputs = 0
        required_indicated = 0
        errors_associated = 0
        has_auth_considerations = False
        evidence_ids: list[str] = []

        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages_list:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")
            id_set: set[str] = {tag["id"] for tag in soup.find_all(id=True)}

            # Look for inputs (excluding hidden, submit, reset, button)
            controls = soup.find_all(
                lambda tag: (
                    (tag.name == "input" and tag.get("type") not in ("hidden", "submit", "reset", "button", "image"))
                    or tag.name in ("select", "textarea")
                )
            )
            total_inputs += len(controls)

            for idx, ctrl in enumerate(controls):
                if not isinstance(ctrl, Tag):
                    continue

                is_labeled = False
                c_id = ctrl.get("id")

                # Check aria-labelledby
                if ctrl.has_attr("aria-labelledby"):
                    target_ids = ctrl["aria-labelledby"].split()
                    if any(tid in id_set for tid in target_ids):
                        is_labeled = True

                # Check aria-label
                if not is_labeled and ctrl.get("aria-label", "").strip():
                    is_labeled = True

                # Check explicit <label for=id>
                if not is_labeled and c_id:
                    lbl = soup.find("label", attrs={"for": c_id})
                    if lbl and lbl.get_text(strip=True):
                        is_labeled = True

                # Check wrapping parent <label>
                if not is_labeled:
                    parent_lbl = ctrl.find_parent("label")
                    if parent_lbl and parent_lbl.get_text(strip=True):
                        is_labeled = True

                if is_labeled:
                    labeled_inputs += 1
                else:
                    unlabeled_inputs += 1
                    evidence_ids.append(f"ev-form-unlabeled-{page.page_url[:30]}-{idx}")

                # Check required-field indication
                if ctrl.has_attr("required") or ctrl.get("aria-required") == "true":
                    required_indicated += 1

                # Check error message association (aria-describedby or aria-errormessage)
                desc_by = ctrl.get("aria-describedby") or ctrl.get("aria-errormessage")
                if desc_by:
                    desc_ids = desc_by.split()
                    if any(did in id_set for did in desc_ids):
                        errors_associated += 1
                        evidence_ids.append(f"ev-form-error-assoc-{page.page_url[:30]}-{idx}")

                # Check accessible authentication considerations (password, captcha, autocomplete)
                if ctrl.get("type") == "password" or "login" in page.page_url or "signin" in page.page_url:
                    has_auth_considerations = True
                    # Check autocomplete attribute support (WCAG 2.2 SC 3.3.8 / 1.3.5)
                    if not ctrl.get("autocomplete"):
                        evidence_ids.append(f"ev-form-no-autocomplete-{page.page_url[:30]}-{idx}")

        return FormAccessibilityAssessment(
            total_form_inputs=total_inputs,
            inputs_with_explicit_labels=labeled_inputs,
            unlabeled_inputs=unlabeled_inputs,
            required_fields_indicated_programmatically=required_indicated,
            error_messages_programmatically_associated=errors_associated,
            has_accessible_authentication_considerations=has_auth_considerations,
            evidence_ids=list(set(evidence_ids)),
        )


FormsLabelsAnalyzer = FormAccessibilityAnalyzer
