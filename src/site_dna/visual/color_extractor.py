"""Deterministic color palette extractor normalizing computed CSS colors."""

import re
from typing import Optional

from site_dna.schemas.visual import ColorRecord, ComputedStyleRecord


def parse_css_color(color_str: Optional[str]) -> Optional[tuple[str, list[int], float]]:
    """Parse a CSS color string (rgb, rgba, hex) into (hex, [r, g, b], alpha).

    Returns None if color is transparent or invalid.
    """
    if not color_str or color_str.strip().lower() in ("transparent", "inherit", "initial", "none"):
        return None

    cleaned = color_str.strip().lower()

    # rgba(r, g, b, a) or rgb(r, g, b)
    rgb_match = re.match(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)(?:\s*,\s*([\d.]+))?\s*\)", cleaned)
    if rgb_match:
        r = int(rgb_match.group(1))
        g = int(rgb_match.group(2))
        b = int(rgb_match.group(3))
        alpha = float(rgb_match.group(4)) if rgb_match.group(4) is not None else 1.0

        if alpha == 0.0:
            return None  # fully transparent

        hex_str = f"#{r:02x}{g:02x}{b:02x}".upper()
        return hex_str, [r, g, b], alpha

    # #RRGGBB or #RGB
    hex_match = re.match(r"^#([0-9a-f]{3}|[0-9a-f]{6})$", cleaned)
    if hex_match:
        val = hex_match.group(1)
        if len(val) == 3:
            val = "".join(c * 2 for c in val)
        r = int(val[0:2], 16)
        g = int(val[2:4], 16)
        b = int(val[4:6], 16)
        return f"#{val}".upper(), [r, g, b], 1.0

    return None


class ColorExtractor:
    """Extracts and aggregates observed colors from computed styles into a palette."""

    @staticmethod
    def extract_palette(computed_styles: list[ComputedStyleRecord]) -> list[ColorRecord]:
        """Aggregate unique observed colors, categorize usage roles, and compute occurrence counts."""
        # Key: (hex, usage_role) -> {"rgb": [r,g,b], "alpha": a, "count": int, "elements": list}
        aggregated: dict[tuple[str, str], dict] = {}

        for style in computed_styles:
            # 1. Background color
            bg_parsed = parse_css_color(style.background_color)
            if bg_parsed:
                hex_c, rgb, alpha = bg_parsed
                role = "button_background" if style.tag_name == "button" else "background"
                key = (hex_c, role)
                if key not in aggregated:
                    aggregated[key] = {"rgb": rgb, "alpha": alpha, "count": 0, "elements": []}
                aggregated[key]["count"] += 1
                if style.element_id not in aggregated[key]["elements"]:
                    aggregated[key]["elements"].append(style.element_id)

            # 2. Text color
            text_parsed = parse_css_color(style.color)
            if text_parsed:
                hex_c, rgb, alpha = text_parsed
                role = "heading_text" if style.tag_name in ("h1", "h2", "h3", "h4") else "text"
                key = (hex_c, role)
                if key not in aggregated:
                    aggregated[key] = {"rgb": rgb, "alpha": alpha, "count": 0, "elements": []}
                aggregated[key]["count"] += 1
                if style.element_id not in aggregated[key]["elements"]:
                    aggregated[key]["elements"].append(style.element_id)

            # 3. Border color
            border_parsed = parse_css_color(style.border_color)
            if border_parsed:
                hex_c, rgb, alpha = border_parsed
                key = (hex_c, "border")
                if key not in aggregated:
                    aggregated[key] = {"rgb": rgb, "alpha": alpha, "count": 0, "elements": []}
                aggregated[key]["count"] += 1
                if style.element_id not in aggregated[key]["elements"]:
                    aggregated[key]["elements"].append(style.element_id)

        # Convert to ColorRecord list sorted by frequency descending
        records: list[ColorRecord] = []
        for (hex_c, usage), data in aggregated.items():
            records.append(
                ColorRecord(
                    hex=hex_c,
                    rgb=data["rgb"],
                    alpha=data["alpha"],
                    usage=usage,
                    occurrence_count=data["count"],
                    sample_element_ids=data["elements"][:5],
                    source="computed_css",
                )
            )

        records.sort(key=lambda c: c.occurrence_count, reverse=True)
        return records
