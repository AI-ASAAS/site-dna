"""Color Contrast Calculation and WCAG 2.2 Relative Luminance Engine for Site DNA Phase 10."""

import math
import re
from typing import Any, Optional

from bs4 import BeautifulSoup, Tag

from site_dna.schemas.accessibility import (
    AccessibilityPageRecord,
    ContrastAssessment,
    ContrastMeasurement,
)

NAMED_COLORS: dict[str, tuple[int, int, int]] = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
    "red": (255, 0, 0),
    "blue": (0, 0, 255),
    "green": (0, 128, 0),
    "yellow": (255, 255, 0),
    "navy": (0, 0, 128),
    "silver": (192, 192, 192),
    "darkgray": (169, 169, 169),
    "lightgray": (211, 211, 211),
}


def parse_color(color_str: str) -> Optional[tuple[int, int, int]]:
    """Parse hex, rgb(), or named color to RGB tuple."""
    if not color_str:
        return None
    s = color_str.strip().lower()

    if s in NAMED_COLORS:
        return NAMED_COLORS[s]

    # Hex: #fff or #ffffff
    hex_match = re.match(r"^#([0-9a-f]{3}|[0-9a-f]{6})$", s)
    if hex_match:
        val = hex_match.group(1)
        if len(val) == 3:
            return (int(val[0] * 2, 16), int(val[1] * 2, 16), int(val[2] * 2, 16))
        return (int(val[0:2], 16), int(val[2:4], 16), int(val[4:6], 16))

    # rgb(r, g, b)
    rgb_match = re.match(r"^rgba?\((\d+)\s*,\s*(\d+)\s*,\s*(\d+)", s)
    if rgb_match:
        return (int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3)))

    return None


def calculate_relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Calculate relative luminance per WCAG 2.2 definition."""

    def channel_l(c: int) -> float:
        s = c / 255.0
        return s / 12.92 if s <= 0.04045 else math.pow((s + 0.055) / 1.055, 2.4)

    r = channel_l(rgb[0])
    g = channel_l(rgb[1])
    b = channel_l(rgb[2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def relative_luminance(r: int, g: int, b: int) -> float:
    """Convenience function calculating relative luminance for R, G, B channels."""
    return calculate_relative_luminance((r, g, b))


def contrast_ratio(l1: float, l2: float) -> float:
    """Convenience function calculating contrast ratio from two luminance values."""
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


def compute_contrast_ratio(fg_rgb: tuple[int, int, int], bg_rgb: tuple[int, int, int]) -> float:
    """Compute contrast ratio between two RGB colors (result between 1.0 and 21.0)."""
    l1 = calculate_relative_luminance(fg_rgb)
    l2 = calculate_relative_luminance(bg_rgb)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return round((lighter + 0.05) / (darker + 0.05), 2)


class ContrastAnalyzer:
    """Calculates verifiable contrast ratios and identifies text failing WCAG 2.2 SC 1.4.3."""

    def analyze(
        self,
        pages: Any,
        crawl_dataset: Optional[dict[str, Any]] = None,
    ) -> ContrastAssessment:
        """Analyze text and background contrast on inspected pages."""
        if isinstance(pages, str):
            # Raw HTML string passed
            p = AccessibilityPageRecord(page_url="https://example.com/test", page_title="Test Page")
            pages_list = [p]
            crawl_dataset = {"pages": [{"url": "https://example.com/test", "raw_html": pages}]}
        else:
            pages_list = pages or []
            crawl_dataset = crawl_dataset or {}

        measurements: list[ContrastMeasurement] = []
        violations_normal = 0
        violations_large = 0
        passes = 0
        complex_bg_count = 0
        worst_ratio: Optional[float] = None
        evidence_ids: list[str] = []

        raw_pages_map = {p.get("url"): p for p in crawl_dataset.get("pages", [])}

        for page in pages_list:
            raw_p = raw_pages_map.get(page.page_url, {})
            html = raw_p.get("raw_html") or raw_p.get("html") or ""
            if not html:
                continue

            soup = BeautifulSoup(html, "html.parser")

            # Also parse rules from <style> blocks
            style_class_colors: dict[str, tuple[str, str]] = {}
            for s_tag in soup.find_all("style"):
                css_text = s_tag.get_text()
                for rule_match in re.finditer(r"\.([a-zA-Z0-9_\-]+)\s*\{([^}]+)\}", css_text):
                    cls_name, body = rule_match.groups()
                    fg_m = re.search(r"(?:^|;|\s)color\s*:\s*([^;]+)", body, re.I)
                    bg_m = re.search(r"(?:^|;|\s)background(?:-color)?\s*:\s*([^;]+)", body, re.I)
                    if fg_m and bg_m:
                        style_class_colors[cls_name] = (fg_m.group(1).strip(), bg_m.group(1).strip())

            # Extract inline style or style attributes with color and background-color
            styled_elements = soup.find_all(attrs={"style": True})
            for idx, el in enumerate(styled_elements):
                if not isinstance(el, Tag):
                    continue

                text = el.get_text(strip=True)
                if not text or len(text) < 2:
                    continue

                style_str = el.get("style", "").lower()
                fg_match = re.search(r"(?:^|;)\s*color\s*:\s*([^;]+)", style_str)
                bg_match = re.search(r"(?:^|;)\s*background(?:-color)?\s*:\s*([^;]+)", style_str)

                if fg_match and bg_match:
                    fg_val = fg_match.group(1).strip()
                    bg_val = bg_match.group(1).strip()

                    # Check for complex background
                    if any(k in bg_val for k in ("url", "gradient", "image")):
                        complex_bg_count += 1
                        continue

                    fg_rgb = parse_color(fg_val)
                    bg_rgb = parse_color(bg_val)

                    if fg_rgb and bg_rgb:
                        ratio = compute_contrast_ratio(fg_rgb, bg_rgb)
                        is_large = bool(
                            re.search(r"font-size\s*:\s*([2-9]\d|1[89])px", style_str)
                            or (
                                re.search(r"font-weight\s*:\s*(bold|[7-9]00)", style_str)
                                and re.search(r"font-size\s*:\s*(1[4-9])px", style_str)
                            )
                        )
                        required = 3.0 if is_large else 4.5
                        meets = ratio >= required

                        if worst_ratio is None or ratio < worst_ratio:
                            worst_ratio = ratio

                        if meets:
                            passes += 1
                        else:
                            if is_large:
                                violations_large += 1
                            else:
                                violations_normal += 1

                        ev_id = f"ev-contrast-{page.page_url[:20]}-{idx}"
                        evidence_ids.append(ev_id)
                        measurements.append(
                            ContrastMeasurement(
                                element_ref=f"{el.name}#{el.get('id') or idx}",
                                selector=f"{el.name}[style*='{fg_val}']",
                                text_sample=text[:40],
                                foreground_color=fg_val,
                                background_color=bg_val,
                                contrast_ratio=ratio,
                                passes_wcag_aa_normal=meets if not is_large else ratio >= 4.5,
                                passes_wcag_aa_large=meets if is_large else ratio >= 3.0,
                                font_size_px=18.0 if is_large else 14.0,
                                is_large_text=is_large,
                                is_complex_background=False,
                                evidence_id=ev_id,
                            )
                        )

            # Process elements matching classes defined in <style>
            for cls_name, (fg_val, bg_val) in style_class_colors.items():
                for c_idx, el in enumerate(soup.find_all(class_=cls_name)):
                    if not isinstance(el, Tag):
                        continue
                    text = el.get_text(strip=True)
                    if not text or len(text) < 2:
                        continue
                    fg_rgb = parse_color(fg_val)
                    bg_rgb = parse_color(bg_val)
                    if fg_rgb and bg_rgb:
                        ratio = compute_contrast_ratio(fg_rgb, bg_rgb)
                        if worst_ratio is None or ratio < worst_ratio:
                            worst_ratio = ratio
                        meets = ratio >= 4.5
                        if meets:
                            passes += 1
                        else:
                            violations_normal += 1
                        ev_id = f"ev-contrast-{cls_name}-{c_idx}"
                        evidence_ids.append(ev_id)
                        measurements.append(
                            ContrastMeasurement(
                                element_ref=f"{el.name}.{cls_name}",
                                selector=f"{el.name}.{cls_name}",
                                text_sample=text[:40],
                                foreground_color=fg_val,
                                background_color=bg_val,
                                contrast_ratio=ratio,
                                passes_wcag_aa_normal=meets,
                                passes_wcag_aa_large=ratio >= 3.0,
                                font_size_px=14.0,
                                is_large_text=False,
                                is_complex_background=False,
                                evidence_id=ev_id,
                            )
                        )

        return ContrastAssessment(
            measured_text_elements_count=len(measurements),
            contrast_violations_aa_normal=violations_normal,
            contrast_violations_aa_large=violations_large,
            contrast_passes_count=passes,
            complex_backgrounds_needing_review=complex_bg_count,
            worst_contrast_ratio=worst_ratio,
            sample_measurements=measurements[:20],
            evidence_ids=list(set(evidence_ids)),
        )
