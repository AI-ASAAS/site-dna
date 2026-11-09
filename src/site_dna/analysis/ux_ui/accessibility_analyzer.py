"""Deterministic accessibility checks covering WCAG-actionable criteria."""

from typing import Any

from site_dna.analysis.ux_ui.context_builder import UXPageContext
from site_dna.schemas.ux_ui import UXAccessibilityAssessment, UXFinding
from site_dna.schemas.visual import VisualEvidenceRecord


class AccessibilityAnalyzer:
    """Conducts automated audits of accessible names, heading hierarchy, contrast, and ARIA roles."""

    @staticmethod
    def analyze_accessibility(
        pages: list[UXPageContext],
        evidence_index: dict[str, VisualEvidenceRecord],
    ) -> UXAccessibilityAssessment:
        """Audit actionable accessibility criteria across pages."""
        findings: list[UXFinding] = []
        accessible_name_issues: list[dict[str, Any]] = []
        heading_issues: list[str] = []
        contrast_issues: list[dict[str, Any]] = []
        keyboard_focusable_count = 0
        missing_aria_labels: list[dict[str, Any]] = []
        heading_hierarchy_valid = True

        for page in pages:
            # 1. Heading Hierarchy Audit
            h_levels = [h.get("level", 1) for h in page.headings]
            has_h1 = any(lvl == 1 for lvl in h_levels)
            if not has_h1 and page.headings:
                heading_hierarchy_valid = False
                issue_msg = f"الصفحة {page.page_url} تفتقر لعنوان رئيسي H1 صريح."
                heading_issues.append(issue_msg)

            # Check skipped levels (e.g. H1 followed immediately by H3 or H4)
            for i in range(len(h_levels) - 1):
                if h_levels[i + 1] - h_levels[i] > 1:
                    heading_hierarchy_valid = False
                    issue_msg = (
                        f"تخطي في مستويات العناوين في {page.page_url} من H{h_levels[i]} إلى H{h_levels[i + 1]} مباشرة."
                    )
                    heading_issues.append(issue_msg)
                    break

            # 2. DOM Elements Accessibility (Images, Buttons, Links, Inputs)
            for el in page.dom_elements:
                tag = el.get("tag_name", "").lower()
                role = (el.get("role") or "").lower()
                attrs = el.get("attributes") or {}
                text = (el.get("text_content") or "").strip()
                aria_label = (el.get("aria_label") or attrs.get("aria-label") or "").strip()

                # Focusable count
                if (
                    tag in ("a", "button", "input", "select", "textarea")
                    or role in ("button", "link")
                    or attrs.get("tabindex") == "0"
                ):
                    keyboard_focusable_count += 1

                # Missing image alt
                if tag == "img" and not attrs.get("alt"):
                    accessible_name_issues.append(
                        {
                            "page_url": page.page_url,
                            "element": "img",
                            "issue": "Missing alt attribute on image",
                        }
                    )

                # Icon buttons missing label
                if tag == "button" and not text and not aria_label:
                    missing_aria_labels.append(
                        {
                            "page_url": page.page_url,
                            "element": "button",
                            "issue": "Button has no readable text or aria-label",
                        }
                    )

            # 3. Check contrast issues recorded in evidence
            for ev in page.evidence_records:
                if ev.evidence_category == "color_contrast" and ev.field_reference == "contrast_ratio":
                    ratio = float(ev.measured_value or 0)
                    if 0 < ratio < 4.5:
                        contrast_issues.append(
                            {
                                "page_url": page.page_url,
                                "ratio": ratio,
                                "evidence_id": ev.evidence_id,
                            }
                        )

        # Generate Findings
        # Finding: Missing H1 or Skipped Heading Levels
        if not heading_hierarchy_valid and heading_issues:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-A11Y-01",
                    title="خلل في التسلسل الهرمي للعناوين (WCAG 1.3.1 Info and Relationships)",
                    category="accessibility",
                    description=heading_issues[0],
                    source_page=pages[0].page_url if pages else "",
                    viewport="desktop",
                    element_reference="h1, h2, h3",
                    evidence_ids=[],
                    observation_type="observed",
                    severity="medium",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="إعاقة قدرة مستخدمي قارئات الشاشة على التنقل السريع بين أقسام الصفحة والتعرف على بنيتها الهيكلية.",
                    recommended_action="ضمان وجود وسم H1 فريد في رأس كل صفحة وتدرج مستويات العناوين منطقياً (H1 ثم H2 ثم H3 دون قفز).",
                )
            )

        # Finding: Missing Alt on Images
        if accessible_name_issues:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-A11Y-02",
                    title="صور تفتقر للنص البديل (WCAG 1.1.1 Non-text Content)",
                    category="accessibility",
                    description=(
                        f"تم رصد {len(accessible_name_issues)} صورة دون سمة alt البديلة في عينة الصفحات المفحوصة."
                    ),
                    source_page=accessible_name_issues[0]["page_url"],
                    viewport="desktop",
                    element_reference="img",
                    evidence_ids=[],
                    observation_type="observed",
                    severity="high",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="عجز ضعاف البصر عن فهم دلالة الصورة أو سياقها في واجهة الموقع.",
                    recommended_action="إضافة سمة `alt='وصف مختصر ومعبر'` لكل صورة ذات دلالة، واستخدام `alt=''` للصور التزيينية فقط.",
                )
            )

        # Finding: Low Contrast
        if contrast_issues:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-A11Y-03",
                    title="نصوص بنسب تباين لوني غير كافية (WCAG 1.4.3 Contrast Minimum)",
                    category="accessibility",
                    description=(
                        f"تم رصد نصوص بنسبة تباين لوني ({contrast_issues[0]['ratio']:.1f}:1) "
                        "أقل من الحد الأدنى القياسي لمطابقة WCAG AA (4.5:1)."
                    ),
                    source_page=contrast_issues[0]["page_url"],
                    viewport="desktop",
                    element_reference="p, span",
                    evidence_ids=[contrast_issues[0]["evidence_id"]],
                    observation_type="observed",
                    severity="high",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="صعوبة بالغة في قراءة المحتوى لضعاف البصر وفي ظروف الإضاءة الشديدة.",
                    recommended_action="تغميق لون النص أو تفتيح لون الخلفية لضمان نسبة تباين لا تقل عن 4.5:1 للنصوص العادية.",
                )
            )

        return UXAccessibilityAssessment(
            accessible_name_issues=accessible_name_issues[:10],
            heading_hierarchy_valid=heading_hierarchy_valid,
            heading_issues=heading_issues[:5],
            contrast_issues=contrast_issues[:10],
            keyboard_focusable_count=keyboard_focusable_count,
            missing_aria_labels=missing_aria_labels[:10],
            findings=findings,
        )
