"""Deterministic form usability, labeling, and submission affordance analyzer."""

from typing import Any

from site_dna.analysis.ux_ui.context_builder import UXPageContext
from site_dna.schemas.ux_ui import UXFinding, UXFormAssessment
from site_dna.schemas.visual import VisualEvidenceRecord


class FormsAnalyzer:
    """Evaluates form usability, input labels, placeholders, and submission controls."""

    @staticmethod
    def analyze_forms(
        pages: list[UXPageContext],
        evidence_index: dict[str, VisualEvidenceRecord],
    ) -> UXFormAssessment:
        """Audit forms across pages for labeling, layout, and submission clarity."""
        findings: list[UXFinding] = []
        forms_detected = 0
        total_fields = 0
        unlabeled_fields: list[dict[str, Any]] = []
        placeholder_only_fields: list[dict[str, Any]] = []
        missing_submit_buttons: list[str] = []
        form_summaries: list[dict[str, Any]] = []

        for page in pages:
            # Check Phase 02 forms
            for crawl_form in page.forms:
                forms_detected += 1
                method = crawl_form.get("method", "GET").upper()
                action = crawl_form.get("action", "")
                fields = crawl_form.get("fields") or crawl_form.get("input_names", [])
                total_fields += len(fields)

                has_submit = crawl_form.get("has_submit_button", False)
                if not has_submit:
                    for f in fields:
                        if isinstance(f, dict):
                            f_type = f.get("field_type", "").lower()
                            if f_type in ("submit", "image") or f.get("name") in ("submit", "send"):
                                has_submit = True

                form_summaries.append(
                    {
                        "page_url": page.page_url,
                        "action": action,
                        "method": method,
                        "fields_count": len(fields),
                        "has_submit": has_submit,
                    }
                )

                if not has_submit:
                    missing_submit_buttons.append(page.page_url)

            # Check DOM inputs directly for label and placeholder compliance
            for el in page.dom_elements:
                tag = el.get("tag_name", "").lower()
                if tag not in ("input", "textarea", "select"):
                    continue

                attrs = el.get("attributes") or {}
                input_type = (attrs.get("type") or "text").lower()
                if input_type in ("hidden", "submit", "button", "reset"):
                    continue

                total_fields += 1
                has_label_text = bool((el.get("aria_label") or "").strip() or attrs.get("aria-label"))
                has_placeholder = bool(attrs.get("placeholder"))
                name_or_id = attrs.get("name") or attrs.get("id") or f"{tag}[type='{input_type}']"

                field_info = {
                    "page_url": page.page_url,
                    "element": name_or_id,
                    "input_type": input_type,
                    "placeholder": attrs.get("placeholder", ""),
                }

                # 1. Check for placeholder-only labeling
                if has_placeholder and not has_label_text:
                    placeholder_only_fields.append(field_info)
                # 2. Check for completely unlabeled fields
                elif not has_label_text and not has_placeholder:
                    unlabeled_fields.append(field_info)

        # Generate Findings
        # Finding: Placeholder-only labeling
        if placeholder_only_fields:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-FORM-01",
                    title="الاعتماد الحصري على النص التوضيحي المؤقت (Placeholder) كبديل للتسمية",
                    category="forms",
                    description=(
                        f"تم رصد {len(placeholder_only_fields)} حقلاً تعتمد حصراً على Placeholder دون وسم `<label>` دائم. "
                        f"مثال: الحقل '{placeholder_only_fields[0]['element']}'."
                    ),
                    source_page=placeholder_only_fields[0]["page_url"],
                    viewport="desktop",
                    element_reference=placeholder_only_fields[0]["element"],
                    evidence_ids=[],
                    observation_type="observed",
                    severity="high",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="اختفاء النص التوضيحي عند بدء الكتابة، مما يؤدي لفقدان سياق الحقل وصعوبة المراجعة وإرباك الذاكرة قصيرة المدى.",
                    recommended_action="توفير وسوم `<label>` ثابتة ومرئية أعلى أو بجانب الحقول، وقصر Placeholder على أمثلة الإدخال التوضيحية فقط.",
                )
            )

        # Finding: Missing labels entirely
        if unlabeled_fields:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-FORM-02",
                    title="حقول إدخال تفتقر كلياً لأي تسمية وصفية أو وسم وصول",
                    category="accessibility",
                    description=(
                        f"تم رصد {len(unlabeled_fields)} حقلاً مجهولة التسمية بدون `<label>` أو `aria-label`. "
                        f"مثال: '{unlabeled_fields[0]['element']}'."
                    ),
                    source_page=unlabeled_fields[0]["page_url"],
                    viewport="desktop",
                    element_reference=unlabeled_fields[0]["element"],
                    evidence_ids=[],
                    observation_type="observed",
                    severity="critical",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="عجز مستخدمي قارئات الشاشة وضعاف البصر عن معرفة البيانات المطلوبة في الحقل.",
                    recommended_action="ربط كل حقل إدخال بوسم `<label for='id'>` صريح أو إضافة سمة aria-label مناسبة.",
                )
            )

        # Finding: Form missing visible submit button
        if missing_submit_buttons:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-FORM-03",
                    title="نموذج مدخلات يفتقر لزر إرسال صريح وواضح",
                    category="forms",
                    description="تم رصد نموذج في الصفحة يفتقر لزر إرسال (Submit Button) محدد برمجياً وبصرياً.",
                    source_page=missing_submit_buttons[0],
                    viewport="desktop",
                    element_reference="form",
                    evidence_ids=[],
                    observation_type="observed",
                    severity="medium",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="ارتباك المستخدم حول كيفية حفظ أو إرسال البيانات المكتوبة.",
                    recommended_action="إضافة زر إرسال صريح مثل `<button type='submit'>إرسال</button>` بلون وحجم واضحين.",
                )
            )

        return UXFormAssessment(
            forms_detected=forms_detected,
            total_fields=total_fields,
            unlabeled_fields=unlabeled_fields[:10],
            placeholder_only_fields=placeholder_only_fields[:10],
            missing_submit_buttons=missing_submit_buttons[:5],
            form_summaries=form_summaries,
            findings=findings,
        )
