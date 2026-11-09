"""Visual hierarchy analyzer evaluating element emphasis, CTA prominence, and spatial composition."""

from typing import Any

from site_dna.schemas.visual_identity import VisualFinding


class HierarchyAnalyzer:
    """Evaluates primary messaging emphasis, call-to-action distinction, and visual landmarks."""

    @staticmethod
    def analyze_hierarchy(
        pages_context: list[Any],
        evidence_index: dict[str, Any],
    ) -> dict[str, Any]:
        """Assess primary CTA distinction, section layout hierarchy, and headline prominence."""
        findings: list[VisualFinding] = []
        finding_counter = 20

        total_buttons = 0
        hero_found = False
        header_found = False
        footer_found = False

        for page in pages_context:
            for layout in page.layout_records:
                sec_type = layout.get("section_type")
                if sec_type in ("hero", "hero_candidate"):
                    hero_found = True
                elif sec_type == "header":
                    header_found = True
                elif sec_type == "footer":
                    footer_found = True

            buttons = [
                el
                for el in page.dom_elements
                if el.get("tag_name") == "button" or "btn" in " ".join(el.get("classes", []))
            ]
            total_buttons += len(buttons)

        # Finding: Missing or weak primary CTA
        if total_buttons == 0 and pages_context:
            findings.append(
                VisualFinding(
                    finding_id=f"FIND-{finding_counter:02d}",
                    title="غياب أو ضعف تمييز أزرار الإجراء الرئيسي (Call-to-Action)",
                    category="visual_hierarchy",
                    severity="high",
                    confidence="confirmed_by_measurement",
                    finding_type="derived_calculation",
                    page_url=pages_context[0].page_url if pages_context else "",
                    description="لم يتم رصد عناصر أزرار واضحة ذات معالجة بصرية بارزة لتوجيه المستخدم نحو الإجراء المنشود.",
                    potential_impact="تراجع قابلية التحويل وانخفاض توجيه الزوار للإجراءات الحيوية كالتواصل أو الشراء.",
                    suggested_action="تصميم زر بارز (Primary CTA Button) بلون تبايني واضح، وبحجم كافٍ في الثلث الأول من الصفحة.",
                    element_references=[],
                    evidence_ids=[],
                )
            )
            finding_counter += 1

        return {
            "hero_section_detected": hero_found,
            "header_detected": header_found,
            "footer_detected": footer_found,
            "total_buttons_detected": total_buttons,
            "findings": findings,
        }
