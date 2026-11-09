"""Deterministic interaction and CTA clarity analyzer."""

from typing import Any

from site_dna.analysis.ux_ui.context_builder import UXPageContext
from site_dna.schemas.ux_ui import UXFinding, UXInteractionAssessment
from site_dna.schemas.visual import VisualEvidenceRecord

CTA_KEYWORDS = {
    "sign up",
    "register",
    "get started",
    "buy now",
    "subscribe",
    "contact us",
    "book now",
    "join",
    "download",
    "تسجيل",
    "اشترك",
    "ابدأ الآن",
    "تواصل معنا",
    "احجز الآن",
    "انضم إلينا",
    "تحميل",
    "شراء",
    "طلب الخدمة",
}


class InteractionAnalyzer:
    """Analyzes interactive controls, button sizes, accessible names, and primary CTA affordances."""

    @staticmethod
    def analyze_interactions(
        pages: list[UXPageContext],
        evidence_index: dict[str, VisualEvidenceRecord],
    ) -> UXInteractionAssessment:
        """Inspect buttons, interactive targets, touch sizes, and CTA prominence."""
        findings: list[UXFinding] = []
        total_buttons = 0
        total_links = 0
        cta_candidates: list[dict[str, Any]] = []
        interactive_elements: list[dict[str, Any]] = []
        small_touch_targets: list[dict[str, Any]] = []
        unlabeled_controls: list[dict[str, Any]] = []

        for page in pages:
            for el in page.dom_elements:
                tag = el.get("tag_name", "").lower()
                role = (el.get("semantic_role") or el.get("role") or el.get("computed_role") or "").lower()
                classes = el.get("classes", [])
                c_name = (" ".join(classes) if isinstance(classes, list) else str(el.get("class_name") or "")).lower()
                bbox = el.get("bounding_box") or {}
                width = bbox.get("width", 0)
                height = bbox.get("height", 0)
                text = (el.get("text_excerpt") or el.get("text_content") or el.get("text") or "").strip()
                aria_label = (
                    el.get("accessible_name")
                    or el.get("aria_label")
                    or (el.get("attributes") or {}).get("aria-label")
                    or ""
                ).strip()

                is_button = tag == "button" or role == "button" or "btn" in c_name or "button" in c_name
                is_link = tag == "a" or role == "link"

                if not (is_button or is_link):
                    continue

                if is_button:
                    total_buttons += 1
                if is_link:
                    total_links += 1

                element_summary = {
                    "page_url": page.page_url,
                    "tag": tag,
                    "role": role,
                    "text": text,
                    "width": width,
                    "height": height,
                    "has_label": bool(text or aria_label),
                }
                interactive_elements.append(element_summary)

                # 1. Unlabeled interactive control check
                if not (text or aria_label):
                    unlabeled_controls.append(element_summary)

                # 2. Touch target size check (WCAG 2.2 min 24x24 px threshold for standalone controls)
                if 0 < width < 24 or 0 < height < 24:
                    # Exclude inline links inside paragraph bodies from strict standalone button penalty
                    if is_button or (is_link and ("btn" in c_name or "button" in c_name)):
                        small_touch_targets.append(element_summary)

                # 3. Primary CTA identification
                lower_text = text.lower()
                if any(k in lower_text for k in CTA_KEYWORDS):
                    cta_candidates.append(
                        {
                            "page_url": page.page_url,
                            "text": text,
                            "tag": tag,
                            "width": width,
                            "height": height,
                        }
                    )

        # Generate Findings
        # Finding: Missing Primary CTA on landing/seed page
        if pages and not cta_candidates:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-INT-01",
                    title="غياب عنصر توجيه رئيسي بارز (Primary Call to Action)",
                    category="cta_clarity",
                    description=(
                        "لم يتم رصد زر أو رابط إجراء رئيسي واضح (CTA) مثل 'ابدأ الآن' أو 'تواصل معنا' "
                        "في الصفحة الرئيسية لتوجيه الزائر نحو الهدف التحويلي."
                    ),
                    source_page=pages[0].page_url,
                    viewport="desktop",
                    element_reference="header, .hero, main",
                    evidence_ids=[],
                    observation_type="observed",
                    severity="high",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="انخفاض معدل تفاعل الزوار وضياع فرص التحويل لعدم وضوح الخطوة التالية.",
                    recommended_action="إضافة زر إجراء رئيسي بلون تبايني بارز ونص محدد في الثلث العلوي من الصفحة.",
                )
            )

        # Finding: Small Touch Targets on mobile/desktop
        if small_touch_targets:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-INT-02",
                    title="أزرار تفاعلية بأبعاد أصغر من الحد الأدنى الموصى به للمس (24×24px)",
                    category="interaction",
                    description=(
                        f"تم رصد {len(small_touch_targets)} عنصراً تفاعلياً بأبعاد تقل عن 24×24 بكسل "
                        f"(أصغر هدف مرصود: {min((t['width'] for t in small_touch_targets), default=0):.0f}×{min((t['height'] for t in small_touch_targets), default=0):.0f}px)."
                    ),
                    source_page=small_touch_targets[0]["page_url"],
                    viewport="mobile",
                    element_reference=f"{small_touch_targets[0]['tag']}",
                    evidence_ids=[],
                    observation_type="derived",
                    severity="medium",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="صعوبة النقر على الأجهزة المحمولة وارتفاع احتمالية النقر الخاطئ.",
                    recommended_action="توسيع الحشوة (Padding) للعناصر التفاعلية لتصل مساحة النقر إلى 44×44px على الأقل (أو 24×24px كحد أدنى مطلق).",
                )
            )

        # Finding: Unlabeled interactive controls
        if unlabeled_controls:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-INT-03",
                    title="عناصر تحكم وأزرار تفاعلية تفتقر للتسمية النصية أو aria-label",
                    category="interaction",
                    description=(
                        f"تم رصد {len(unlabeled_controls)} عنصراً تفاعلياً دون محتوى نصي مقروء أو وسم aria-label، "
                        "مثل أزرار الأيقونات المجردة."
                    ),
                    source_page=unlabeled_controls[0]["page_url"],
                    viewport="desktop",
                    element_reference=f"{unlabeled_controls[0]['tag']}",
                    evidence_ids=[],
                    observation_type="observed",
                    severity="high",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="استحالة معرفة وظيفة الزر لمستخدمي قارئات الشاشة والزوار الجدد.",
                    recommended_action="إضافة نصوص توضيحية أو سمة aria-label واضحة تشرح وظيفة الزر للمستخدم.",
                )
            )

        return UXInteractionAssessment(
            total_buttons=total_buttons,
            total_links=total_links,
            cta_candidates=cta_candidates,
            interactive_elements=interactive_elements[:30],
            small_touch_targets=small_touch_targets[:10],
            unlabeled_controls=unlabeled_controls[:10],
            findings=findings,
        )
