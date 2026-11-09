"""Deterministic mobile UX, responsive adaptation, and viewport geometry analyzer."""

from typing import Any

from site_dna.analysis.ux_ui.context_builder import UXPageContext
from site_dna.schemas.ux_ui import UXFinding, UXResponsiveAssessment
from site_dna.schemas.visual import VisualEvidenceRecord


class ResponsiveAnalyzer:
    """Evaluates mobile presentation, horizontal overflow, touch targets, and viewport adaptability."""

    @staticmethod
    def analyze_responsive(
        pages: list[UXPageContext],
        evidence_index: dict[str, VisualEvidenceRecord],
    ) -> UXResponsiveAssessment:
        """Inspect mobile screenshots and DOM measurements for responsive friction points."""
        findings: list[UXFinding] = []
        horizontal_overflow_detected = False
        overflow_pages: list[str] = []
        clipped_elements_count = 0
        mobile_nav_collapsed = True
        undersized_targets: list[dict[str, Any]] = []

        for page in pages:
            # 1. Check responsive observations from Phase 03
            for obs in page.responsive_observations:
                obs_type = (obs.get("observation_type") or obs.get("observation_name") or "").lower()
                obs_status = (obs.get("status") or "").lower()
                details = obs.get("details") or {}

                if "overflow" in obs_type:
                    if (
                        obs_status in ("failed", "detected", "true")
                        or details.get("has_overflow")
                        or obs.get("mobile_value")
                    ):
                        horizontal_overflow_detected = True
                        if page.page_url not in overflow_pages:
                            overflow_pages.append(page.page_url)

                if "clipped" in obs_type:
                    if (
                        obs_status in ("failed", "detected", "true")
                        or details.get("clipped_count", 0) > 0
                        or obs.get("mobile_value")
                    ):
                        clipped_elements_count += details.get("clipped_count", 1)

            # 2. Check layout records for element overflow beyond mobile viewport (width 390px)
            for layout in page.layout_records:
                if layout.get("viewport_profile") == "mobile":
                    w = layout.get("bounding_box", {}).get("width", 0)
                    x = layout.get("bounding_box", {}).get("x", 0)
                    if (x + w) > 395:  # Tolerance threshold
                        horizontal_overflow_detected = True
                        if page.page_url not in overflow_pages:
                            overflow_pages.append(page.page_url)

            # 3. Check mobile touch targets in DOM
            for el in page.dom_elements:
                tag = el.get("tag_name", "").lower()
                role = (el.get("role") or "").lower()
                c_name = (el.get("class_name") or "").lower()
                bbox = el.get("bounding_box") or {}
                w = bbox.get("width", 0)
                h = bbox.get("height", 0)

                is_interactive = tag in ("button", "a", "input", "select") or role in ("button", "link")
                if is_interactive and (0 < w < 24 or 0 < h < 24):
                    undersized_targets.append(
                        {
                            "page_url": page.page_url,
                            "tag": tag,
                            "class": c_name,
                            "width": w,
                            "height": h,
                        }
                    )

            # 4. Check whether mobile navigation collapses into menu button/hamburger
            mobile_has_menu_button = any(
                "menu" in (d.get("class_name") or "").lower()
                or "hamburger" in (d.get("class_name") or "").lower()
                or d.get("aria_label") in ("Menu", "قائمة", "القائمة", "Navigation")
                for d in page.dom_elements
            )
            # If multiple links exist on mobile without a collapse button, nav is not collapsed
            if len(page.links) > 6 and not mobile_has_menu_button:
                mobile_nav_collapsed = False

        # Generate Findings
        # Finding: Horizontal Overflow on mobile
        if horizontal_overflow_detected:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-RESP-01",
                    title="وجود فائض أفقي غير مرغوب فيه على شاشات الهواتف المحمولة",
                    category="responsive",
                    description=(
                        f"تم رصد عناصر تتجاوز عرض نافذة الجوال (390px) مما يتسبب في شريط تمرير أفقي غير مقصود "
                        f"في {len(overflow_pages)} صفحة (مثل: {overflow_pages[0]})."
                    ),
                    source_page=overflow_pages[0],
                    viewport="mobile",
                    element_reference="body, main, .container",
                    evidence_ids=[],
                    observation_type="derived",
                    severity="critical",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="تراجع تجربة التصفح على الجوال، وانحراف المحاذاة وصعوبة القراءة والتمرير باللمس.",
                    recommended_action="تطبيق `max-width: 100%` و `overflow-x: hidden` وضمان ضبط مقاسات الجداول والصور داخل حاويات مرنة.",
                )
            )

        # Finding: Undersized mobile touch targets
        if undersized_targets:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-RESP-02",
                    title="أهداف لمس على الجوال دون الحد الأدنى المريح للمستخدم",
                    category="responsive",
                    description=(
                        f"تم رصد {len(undersized_targets)} عنصراً تفاعلياً على الجوال بأبعاد أقل من 24×24px، "
                        "مما يقل عن معايير WCAG 2.2 ومبادئ تصميم الهواتف أولاً."
                    ),
                    source_page=undersized_targets[0]["page_url"],
                    viewport="mobile",
                    element_reference=f"{undersized_targets[0]['tag']}.{undersized_targets[0]['class']}",
                    evidence_ids=[],
                    observation_type="observed",
                    severity="medium",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="صعوبة النقر الدقيق بالإبهام والضغط المتكرر غير المقصود على العناصر المجاورة.",
                    recommended_action="زيادة الهوامش الداخلية (padding) لكل هدف تفاعلي على الجوال لضمان مساحة نقر لا تقل عن 44×44px.",
                )
            )

        # Finding: Uncollapsed Mobile Navigation
        if not mobile_nav_collapsed and len(pages) > 0:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-RESP-03",
                    title="قائمة التنقل لا تتقلص إلى قائمة همبرغر مدمجة على الجوال",
                    category="responsive",
                    description="قائمة الروابط العريضة تظهر بالكامل على الجوال دون طيها في زر قائمة منسدلة، مما يستهلك معظم مساحة الشاشة الأولى.",
                    source_page=pages[0].page_url,
                    viewport="mobile",
                    element_reference="nav",
                    evidence_ids=[],
                    observation_type="observed",
                    severity="medium",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="دفع المحتوى الرئيسي إلى أسفل الشاشة وإجبار المستخدم على التمرير المطول قبل رؤية عنوان الصفحة.",
                    recommended_action="استخدام مكون رأس الصفحة المتجاوب (SiteHeader) الذي يطوي الروابط في زر قائمة أسفل دقة 900px.",
                )
            )

        return UXResponsiveAssessment(
            horizontal_overflow_detected=horizontal_overflow_detected,
            overflow_pages=overflow_pages,
            clipped_elements_count=clipped_elements_count,
            mobile_navigation_collapsed=mobile_nav_collapsed,
            undersized_touch_targets=undersized_targets[:10],
            findings=findings,
        )
