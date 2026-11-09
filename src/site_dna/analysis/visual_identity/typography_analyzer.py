"""Deterministic typography and typographic hierarchy analyzer with Arabic RTL support."""

from typing import Any

from site_dna.schemas.visual_identity import VisualFinding


class TypographyAnalyzer:
    """Analyzes font families, typographic scale, line heights, and Arabic RTL directionality."""

    @staticmethod
    def analyze_typography(
        pages_context: list[Any],
        evidence_index: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate typographic system, scale ratios, and font hierarchy."""
        font_families: set[str] = set()
        font_sizes_by_type: dict[str, list[float]] = {}
        arabic_rtl_observed = False
        findings: list[VisualFinding] = []
        finding_counter = 10  # Range for typography findings

        for page in pages_context:
            for t in page.typography:
                family = t.get("font_family", "").strip()
                if family:
                    # Clean family string
                    cleaned_family = family.split(",")[0].strip("\"' ")
                    font_families.add(cleaned_family)

                el_type = t.get("element_type", "").lower()
                size_px = t.get("font_size_px", 16.0)
                if el_type not in font_sizes_by_type:
                    font_sizes_by_type[el_type] = []
                font_sizes_by_type[el_type].append(size_px)

                # Check directionality
                direction = t.get("direction", "ltr")
                lang = t.get("language")
                if direction == "rtl" or lang == "ar":
                    arabic_rtl_observed = True

        # Calculate average sizes
        avg_h1 = sum(font_sizes_by_type.get("h1", [28.0])) / max(len(font_sizes_by_type.get("h1", [1])), 1)
        avg_body = sum(font_sizes_by_type.get("p", [16.0])) / max(len(font_sizes_by_type.get("p", [1])), 1)

        scale_ratio = round(avg_h1 / avg_body, 2) if avg_body > 0 else 1.0

        # Finding: Excessive font families
        if len(font_families) > 3:
            findings.append(
                VisualFinding(
                    finding_id=f"FIND-{finding_counter:02d}",
                    title="تعدد عائلات الخطوط المستخدمة في الواجهة",
                    category="typography",
                    severity="medium",
                    confidence="confirmed_by_measurement",
                    finding_type="derived_calculation",
                    page_url=pages_context[0].page_url if pages_context else "",
                    description=f"تم رصد {len(font_families)} عائلات خطوط مختلفة ({', '.join(sorted(list(font_families))[:4])}).",
                    potential_impact="تشتيت التماسك الطباعي للهوية البصرية وإضعاف انسجام تجربة القراءة.",
                    suggested_action="توحيد الخطوط بحصرها في عائلة واحدة للنصوص وعائلة متناسقة للعناوين كحد أقصى.",
                    element_references=[],
                    evidence_ids=[],
                )
            )
            finding_counter += 1

        # Finding: Weak typographic hierarchy
        if "h1" in font_sizes_by_type and scale_ratio < 1.3:
            findings.append(
                VisualFinding(
                    finding_id=f"FIND-{finding_counter:02d}",
                    title="تقارب أحجام خطوط العناوين مع النصوص الأساسية",
                    category="typography",
                    severity="medium",
                    confidence="confirmed_by_measurement",
                    finding_type="derived_calculation",
                    page_url=pages_context[0].page_url if pages_context else "",
                    description=f"نسبة التدرج بين العنوان الرئيسي والنص هي {scale_ratio}:1 (H1: {avg_h1}px مقابل نص: {avg_body}px)، وهي أقل من النسبة النموذجية (1.5:1).",
                    potential_impact="صعوبة المسح السريع للصفحة وضعف الإدراك الفوري لأقسام المحتوى وأولوياتها.",
                    suggested_action="تكبير حجم خط العنوان الرئيسي أو استخدام وزن أغمق لزيادة التمايز الهرمي.",
                    element_references=[],
                    evidence_ids=[],
                )
            )
            finding_counter += 1

        return {
            "font_families": sorted(list(font_families)),
            "font_sizes_by_type": {k: round(sum(v) / len(v), 1) for k, v in font_sizes_by_type.items()},
            "heading_to_body_ratio": scale_ratio,
            "arabic_rtl_supported": arabic_rtl_observed,
            "findings": findings,
        }
