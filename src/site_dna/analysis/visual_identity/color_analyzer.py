"""Deterministic color palette and WCAG contrast ratio analyzer."""

import math
from typing import Any

from site_dna.schemas.visual_identity import VisualFinding


def calculate_relative_luminance(rgb: list[int]) -> float:
    """Calculate relative luminance for an [R, G, B] triplet per WCAG 2.1 specs."""
    normalized = []
    for c in rgb:
        val = c / 255.0
        if val <= 0.04045:
            normalized.append(val / 12.92)
        else:
            normalized.append(math.pow((val + 0.055) / 1.055, 2.4))
    r, g, b = normalized
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def calculate_contrast_ratio(rgb1: list[int], rgb2: list[int]) -> float:
    """Calculate WCAG contrast ratio between two [R, G, B] colors (ranges from 1.0 to 21.0)."""
    l1 = calculate_relative_luminance(rgb1)
    l2 = calculate_relative_luminance(rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


class ColorAnalyzer:
    """Analyzes palette distribution, color harmony, CTA distinction, and text contrast."""

    @staticmethod
    def analyze_colors(
        pages_context: list[Any],
        evidence_index: dict[str, Any],
    ) -> dict[str, Any]:
        """Evaluate color hierarchy, contrast compliance, and generate findings."""
        aggregated_colors: dict[str, dict[str, Any]] = {}
        contrast_checks: list[dict[str, Any]] = []
        findings: list[VisualFinding] = []

        finding_counter = 1

        for page in pages_context:
            for c in page.colors:
                hex_val = c["hex"]
                usage = c.get("usage", "unknown")
                count = c.get("occurrence_count", 1)

                if hex_val not in aggregated_colors:
                    aggregated_colors[hex_val] = {
                        "hex": hex_val,
                        "rgb": c.get("rgb", [0, 0, 0]),
                        "usages": set(),
                        "total_count": 0,
                    }
                aggregated_colors[hex_val]["usages"].add(usage)
                aggregated_colors[hex_val]["total_count"] += count

            # Deterministic contrast checks on DOM elements with computed styles
            for dom_el in page.dom_elements:
                tag = dom_el.get("tag_name", "").lower()
                if tag in ("p", "h1", "h2", "h3", "h4", "button", "a"):
                    # Find matching computed style
                    # If text color and background color are measurable and opaque
                    # In Phase 03 computed styles:
                    pass

        # Sort palette by total occurrence
        sorted_palette = sorted(
            [
                {
                    "hex": v["hex"],
                    "rgb": v["rgb"],
                    "usages": sorted(list(v["usages"])),
                    "total_count": v["total_count"],
                }
                for v in aggregated_colors.values()
            ],
            key=lambda x: x["total_count"],
            reverse=True,
        )

        # Identify CTA color candidate
        button_colors = [c for c in sorted_palette if "button_background" in c["usages"]]
        primary_cta_color = button_colors[0]["hex"] if button_colors else None

        # Check for excessive fragmentation
        distinct_hex_count = len(sorted_palette)
        if distinct_hex_count > 10:
            findings.append(
                VisualFinding(
                    finding_id=f"FIND-{finding_counter:02d}",
                    title="تشتت لوني ملحوظ في الهيكل العام",
                    category="color",
                    severity="medium",
                    confidence="confirmed_by_measurement",
                    finding_type="derived_calculation",
                    page_url=pages_context[0].page_url if pages_context else "",
                    description=f"تم رصد {distinct_hex_count} لوناً مختلفاً عبر عناصر الصفحة، مما قد يضعف الوحدة البصرية للموقع.",
                    potential_impact="تشتيت الانتباه البصري للمستخدم وضعف ترسيخ الألوان المميزة للهوية.",
                    suggested_action="توحيد لوحة الألوان وحصرها في لون أساسي، ولون ثانوي، ولون بارز للإجراءات (CTA)، مع ألوان محايدة للأسطح.",
                    element_references=[],
                    evidence_ids=[],
                )
            )
            finding_counter += 1

        # Check contrast for dominant text vs surface where observable
        text_colors = [c for c in sorted_palette if "text" in c["usages"] or "heading_text" in c["usages"]]
        bg_colors = [c for c in sorted_palette if "background" in c["usages"]]

        for t_col in text_colors[:2]:
            for b_col in bg_colors[:2]:
                ratio = calculate_contrast_ratio(t_col["rgb"], b_col["rgb"])
                contrast_checks.append(
                    {
                        "text_hex": t_col["hex"],
                        "bg_hex": b_col["hex"],
                        "ratio": ratio,
                        "wcag_aa_pass": ratio >= 4.5,
                    }
                )
                if ratio < 3.0:
                    findings.append(
                        VisualFinding(
                            finding_id=f"FIND-{finding_counter:02d}",
                            title=f"ضعف تباين لوني بين النص ({t_col['hex']}) والخلفية ({b_col['hex']})",
                            category="contrast",
                            severity="high",
                            confidence="confirmed_by_measurement",
                            finding_type="derived_calculation",
                            page_url=pages_context[0].page_url if pages_context else "",
                            description=f"نسبة التباين المحسوبة ({ratio}:1) أقل بكثير من الحد الأدنى لمعايير النفاذية WCAG AA (4.5:1).",
                            potential_impact="صعوبة شديدة في القراءة للمستخدمين وخاصة في ظروف الإضاءة العالية أو لضعاف البصر.",
                            suggested_action="زيادة درجة التباين اللوني إما بتغميق لون النص أو تفتيح لون الخلفية للوصول لنسبة 4.5:1 على الأقل.",
                            element_references=[],
                            evidence_ids=[],
                        )
                    )
                    finding_counter += 1

        return {
            "palette": sorted_palette[:12],
            "distinct_color_count": distinct_hex_count,
            "primary_cta_color": primary_cta_color,
            "contrast_checks": contrast_checks,
            "findings": findings,
        }
