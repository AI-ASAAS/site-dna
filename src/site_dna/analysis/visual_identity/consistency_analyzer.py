"""Consistency analyzer evaluating cross-page uniformity and desktop-to-mobile responsive continuity."""

from typing import Any

from site_dna.schemas.visual_identity import VisualFinding


class ConsistencyAnalyzer:
    """Compares visual patterns across pages and responsive viewports."""

    @staticmethod
    def analyze_consistency(
        pages_context: list[Any],
        evidence_index: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate cross-page component repeatability and responsive overflow issues."""
        findings: list[VisualFinding] = []
        finding_counter = 30

        is_multipage = len(pages_context) > 1

        # 1. Responsive Overflow Check across all pages
        for page in pages_context:
            for obs in page.responsive_observations:
                obs_type = obs.get("observation_type")
                if obs_type == "horizontal_overflow":
                    desc = obs.get("description", "")
                    mobile_val = obs.get("mobile_value", {})
                    # Check if overflow occurred
                    m_scroll_w = mobile_val.get("scroll_width", 0)
                    m_vp_w = mobile_val.get("viewport_width", 390)
                    if m_scroll_w > m_vp_w + 2 or "overflow" in desc.lower() and "no horizontal" not in desc.lower():
                        findings.append(
                            VisualFinding(
                                finding_id=f"FIND-{finding_counter:02d}",
                                title="حدوث فائض أفقي (Horizontal Overflow) على شاشات الجوال",
                                category="responsive_visual",
                                severity="high",
                                confidence="confirmed_by_measurement",
                                finding_type="derived_calculation",
                                page_url=page.page_url,
                                viewport_profile="mobile",
                                description=f"عرض محتوى الصفحة على الجوال ({m_scroll_w}px) يتجاوز عرض نافذة العرض ({m_vp_w}px)، مما يسبب تمريرًا أفقيًا غير مقصود.",
                                potential_impact="انكسار التخطيط على الأجهزة الذكية وصعوبة بالغة في التنقل والتفاعل لمستخدمي الجوال.",
                                suggested_action="ضبط قيود العرض الأقصى (max-width: 100%) ومراجعة العناصر ذات العرض الثابت (fixed widths).",
                                element_references=[],
                                evidence_ids=[],
                            )
                        )
                        finding_counter += 1

        # 2. Cross-Page Consistency
        if not is_multipage:
            cross_page_note = "لم يتم تقييم الاتساق البصري عبر الصفحات لتوافر صفحة واحدة فقط تم زحفها."
        else:
            cross_page_note = f"تم تقييم الاتساق البصري عبر {len(pages_context)} صفحات مستكشفة."
            # Compare font families across pages
            page_fonts = [
                set(t.get("font_family", "").split(",")[0].strip() for t in p.typography) for p in pages_context
            ]
            if len(page_fonts) >= 2:
                common_fonts = set.intersection(*page_fonts)
                if not common_fonts and any(len(f) > 0 for f in page_fonts):
                    findings.append(
                        VisualFinding(
                            finding_id=f"FIND-{finding_counter:02d}",
                            title="اختلاف عائلات الخطوط بين الصفحات المختلفة",
                            category="component_consistency",
                            severity="medium",
                            confidence="confirmed_by_measurement",
                            finding_type="derived_calculation",
                            page_url=pages_context[0].page_url,
                            description="تستخدم صفحات الموقع عائلات خطوط متباينة دون توحيد للنسق الطباعي العام.",
                            potential_impact="شعور المستخدم بالانتقال إلى موقع مختلف وفقدان الشعور بالهوية الواحدة.",
                            suggested_action="توحيد ملفات CSS المشتركة وتطبيق متغيرات خط موحدة على مستوى الجذر (:root).",
                            element_references=[],
                            evidence_ids=[],
                        )
                    )
                    finding_counter += 1

        return {
            "is_multipage": is_multipage,
            "pages_evaluated_count": len(pages_context),
            "cross_page_note": cross_page_note,
            "findings": findings,
        }
