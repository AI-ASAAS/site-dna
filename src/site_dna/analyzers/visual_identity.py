"""Visual identity extraction and palette aggregation (Phase 4)."""

import time
from collections import Counter
from pathlib import Path
from typing import Any

from site_dna.analyzers.color_utils import (
    RGBA,
    composite,
    hue_distance,
    is_neutral,
    parse_color,
    rgb_to_hsl,
    to_hex,
)
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.models.common import ModuleError, ModuleResult, ModuleStatus
from site_dna.models.visual import (
    ColorRecord,
    ColorRoleRecord,
    ColorRoles,
    ColorsAnalysis,
    ColorUsage,
    FontFamilyRecord,
    HeadingStyle,
    TypographyAnalysis,
    VisualIdentity,
)
from site_dna.services.browser import BrowserManager, BrowserRequestGuard

logger = get_logger("analyzers.visual_identity")

COLLECT_STYLES_JS = (Path(__file__).parent / "js" / "collect_styles.js").read_text(encoding="utf-8")
WHITE = RGBA(255, 255, 255, 1.0)
ROLE_LIMIT = 10
SECONDARY_HUE_DISTANCE = 20


def build_visual_identity(raw: dict[str, Any]) -> VisualIdentity:
    """Aggregate raw browser samples into ranked colors and typography evidence."""
    samples = list(raw.get("samples") or [])
    buttons = list(raw.get("buttons") or [])
    links = list(raw.get("links") or [])
    fonts = list(raw.get("fonts") or [])

    records: dict[str, dict[str, Any]] = {}

    def add(sample: dict[str, Any], color_value: Any, usage: str, weight: float) -> None:
        parsed = parse_color(color_value)
        if parsed is None or parsed.a <= 0.01:
            return
        background = parse_color(sample.get("effectiveBg")) or WHITE
        if parsed.a < 1:
            parsed = composite(parsed, background)
        hex_value = to_hex(parsed)
        record = records.setdefault(
            hex_value,
            {
                "hex": hex_value,
                "count": 0,
                "weight": 0.0,
                "usages": ColorUsage(),
                "usage_weights": {},
            },
        )
        record["count"] += 1
        record["weight"] += weight
        usage_weights = record["usage_weights"]
        usage_weights[usage] = usage_weights.get(usage, 0.0) + weight
        setattr(record["usages"], usage, getattr(record["usages"], usage) + 1)

    for sample in samples:
        area = float(sample.get("area") or 0)
        text_length = int(sample.get("textLength") or 0)
        border_width = float(sample.get("borderWidth") or 0)

        if sample.get("hasText") and text_length > 0:
            add(sample, sample.get("color"), "text", text_length)
        if area > 0:
            add(sample, sample.get("backgroundColor"), "background", area)
        if border_width > 0:
            add(sample, sample.get("borderColor"), "border", 1)
        if sample.get("fill"):
            add(sample, sample.get("fill"), "svg", 1)
        if sample.get("stroke"):
            add(sample, sample.get("stroke"), "svg", 1)

    for sample in buttons:
        area = float(sample.get("area") or 0)
        text_length = int(sample.get("textLength") or 0)
        border_width = float(sample.get("borderWidth") or 0)

        if sample.get("hasText") and text_length > 0:
            add(sample, sample.get("color"), "text", text_length)
            add(sample, sample.get("color"), "button", text_length)
        if area > 0:
            add(sample, sample.get("backgroundColor"), "background", area)
            add(sample, sample.get("backgroundColor"), "button", area)
        if border_width > 0:
            add(sample, sample.get("borderColor"), "border", 1)
            add(sample, sample.get("borderColor"), "button", 1)

    for sample in links:
        area = float(sample.get("area") or 0)
        text_length = int(sample.get("textLength") or 0)
        border_width = float(sample.get("borderWidth") or 0)

        if sample.get("hasText") and text_length > 0:
            add(sample, sample.get("color"), "text", text_length)
            add(sample, sample.get("color"), "link", text_length)
        if area > 0:
            add(sample, sample.get("backgroundColor"), "background", area)
            add(sample, sample.get("backgroundColor"), "link", area)
        if border_width > 0:
            add(sample, sample.get("borderColor"), "border", 1)
            add(sample, sample.get("borderColor"), "link", 1)

    total_weight = sum(record["weight"] for record in records.values()) or 1.0
    all_colors = [
        ColorRecord(
            hex=record["hex"],
            count=record["count"],
            weight=record["weight"],
            share=record["weight"] / total_weight,
            usages=record["usages"],
            source="computed",
        )
        for record in records.values()
    ]
    all_colors.sort(key=lambda color: (-color.weight, -color.count, color.hex))

    roles = _build_color_roles(all_colors, records)
    colors = ColorsAnalysis(all=all_colors, roles=roles)
    typography = _build_typography(samples, fonts, raw.get("headings") or {})

    css_variables: dict[str, str] = {}
    for name, value in (raw.get("cssVariables") or {}).items():
        parsed = parse_color(value)
        if parsed is not None and parsed.a > 0.01:
            css_variables[str(name)] = str(value)

    return VisualIdentity(
        colors=colors,
        typography=typography,
        screenshot=None,
        css_variables=css_variables,
        sampled_elements=int(raw.get("sampledElements") or len(samples)),
        truncated_sampling=bool(raw.get("truncatedSampling", False)),
    )


def _build_color_roles(
    all_colors: list[ColorRecord],
    records: dict[str, dict[str, Any]],
) -> ColorRoles:
    def usage_weight(color: ColorRecord, usage: str) -> float:
        return float(records[color.hex]["usage_weights"].get(usage, 0.0))

    background = sorted(
        (color for color in all_colors if usage_weight(color, "background") > 0),
        key=lambda color: (-usage_weight(color, "background"), -color.weight, color.hex),
    )[:ROLE_LIMIT]
    text = sorted(
        (color for color in all_colors if usage_weight(color, "text") > 0),
        key=lambda color: (-usage_weight(color, "text"), -color.weight, color.hex),
    )[:ROLE_LIMIT]

    non_neutral = [color for color in all_colors if not is_neutral(color.hex)]
    button_link = [
        color
        for color in non_neutral
        if usage_weight(color, "button") + usage_weight(color, "link") > 0
    ]
    if button_link:
        candidates = sorted(
            button_link,
            key=lambda color: (
                -(usage_weight(color, "button") + usage_weight(color, "link")),
                -color.weight,
                color.hex,
            ),
        )
    else:
        candidates = sorted(non_neutral, key=lambda color: (-color.weight, color.hex))

    primary: list[ColorRoleRecord] = []
    secondary: list[ColorRoleRecord] = []
    if candidates:
        primary_color = candidates[0]
        primary = [_role_record(primary_color)]
        primary_hue = _hue_of(primary_color.hex)
        for color in sorted(non_neutral, key=lambda item: (-item.weight, item.hex)):
            if color.hex == primary_color.hex:
                continue
            color_hue = _hue_of(color.hex)
            if primary_hue is not None and color_hue is not None:
                if hue_distance(primary_hue, color_hue) <= SECONDARY_HUE_DISTANCE:
                    continue
            secondary.append(_role_record(color))
            if len(secondary) >= ROLE_LIMIT:
                break

    assigned = {color.hex for color in background + text + primary + secondary}
    other = [_role_record(color) for color in all_colors if color.hex not in assigned][:ROLE_LIMIT]

    method = (
        "background=area-weighted; text=text-length-weighted; "
        "primary=highest-weight non-neutral button/link color, fallback all non-neutral; "
        "secondary=remaining non-neutral colors with hue distance > 20 degrees; "
        "other=unassigned colors"
    )
    return ColorRoles(
        background=[_role_record(color) for color in background],
        text=[_role_record(color) for color in text],
        primary=primary,
        secondary=secondary,
        other=other,
        roles_method=method,
    )


def _role_record(color: ColorRecord) -> ColorRoleRecord:
    return ColorRoleRecord(
        hex=color.hex,
        count=color.count,
        weight=color.weight,
        share=color.share,
        usages=color.usages,
        source="inferred",
    )


def _hue_of(hex_value: str) -> float | None:
    parsed = parse_color(hex_value)
    if parsed is None:
        return None
    return rgb_to_hsl(parsed.r, parsed.g, parsed.b)[0]


def _build_typography(
    samples: list[dict[str, Any]],
    fonts: list[dict[str, Any]],
    headings: dict[str, Any],
) -> TypographyAnalysis:
    loaded_families = {
        _strip_quotes(str(font.get("family") or "")).lower()
        for font in fonts
        if font.get("status") == "loaded"
    }

    family_weights: dict[str, float] = {}
    family_fallbacks: dict[str, list[str]] = {}
    for sample in samples:
        family_stack = sample.get("fontFamily")
        if not family_stack:
            continue
        primary, fallbacks = _parse_font_stack(str(family_stack))
        if not primary:
            continue
        weight = float(sample.get("area") or 1.0)
        family_weights[primary] = family_weights.get(primary, 0.0) + weight
        existing = family_fallbacks.setdefault(primary, [])
        for fallback in fallbacks:
            if fallback not in existing:
                existing.append(fallback)

    font_families = [
        FontFamilyRecord(
            family=family,
            weight=weight,
            primary=False,
            fallbacks=family_fallbacks.get(family, []),
            loaded=family.lower() in loaded_families,
        )
        for family, weight in sorted(family_weights.items(), key=lambda item: (-item[1], item[0]))
    ]
    if font_families:
        font_families[0].primary = True

    sizes = Counter(
        str(sample.get("fontSize"))
        for sample in samples
        if sample.get("fontSize")
    )
    weights = Counter(
        str(sample.get("fontWeight"))
        for sample in samples
        if sample.get("fontWeight")
    )

    heading_styles: dict[str, HeadingStyle] = {}
    for level in ("h1", "h2", "h3"):
        level_samples = headings.get(level) or []
        if level_samples:
            heading = level_samples[0]
            heading_styles[level] = HeadingStyle(
                color=heading.get("color"),
                font_size=heading.get("fontSize"),
                font_weight=heading.get("fontWeight"),
                font_family=heading.get("fontFamily"),
                line_height=heading.get("lineHeight"),
                letter_spacing=heading.get("letterSpacing"),
                text_transform=heading.get("textTransform"),
            )
        else:
            heading_styles[level] = HeadingStyle()
    return TypographyAnalysis(
        font_families=font_families,
        font_sizes=dict(sorted(sizes.items(), key=lambda item: (-item[1], item[0]))),
        font_weights=dict(sorted(weights.items(), key=lambda item: (-item[1], item[0]))),
        heading_styles=heading_styles,
    )


def _parse_font_stack(value: str) -> tuple[str, list[str]]:
    parts: list[str] = []
    current: list[str] = []
    quote: str | None = None

    for char in value:
        if char in "\"'":
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            current.append(char)
        elif char == "," and quote is None:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(char)

    if current:
        parts.append("".join(current).strip())

    cleaned = [_strip_quotes(part) for part in parts if part.strip()]
    if not cleaned:
        return "", []
    return cleaned[0], cleaned[1:]


def _strip_quotes(value: str) -> str:
    return value.strip().strip("\"'")


class VisualIdentityExtractor:
    """Render a page and extract its visual identity evidence."""

    def __init__(
        self,
        *,
        settings: Settings | None = None,
        guard: BrowserRequestGuard | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._guard = guard

    async def extract(self, url: str) -> ModuleResult[VisualIdentity]:
        started = time.perf_counter()
        guard = self._guard or BrowserRequestGuard(
            allow_private_hosts=self._settings.private_hosts_allowed()
        )

        try:
            async with BrowserManager(settings=self._settings) as manager:
                page = await manager.open_page(guard)
                await page.goto(
                    url,
                    wait_until="load",
                    timeout=self._settings.visual_navigation_timeout_ms,
                )
                try:
                    await page.wait_for_load_state("networkidle", timeout=3000)
                except Exception:  # noqa: BLE001 - bounded wait is allowed to fail
                    pass
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(250)
                await page.evaluate("window.scrollTo(0, 0)")
                raw = await page.evaluate(COLLECT_STYLES_JS)
        except Exception as exc:  # noqa: BLE001 - module boundary reports a failed result
            logger.warning("visual identity extraction failed", extra={"url": url})
            return ModuleResult[VisualIdentity](
                status=ModuleStatus.failed,
                reason=str(exc),
                duration_ms=_elapsed_ms(started),
                warnings=list(guard.warnings),
                errors=[
                    ModuleError(
                        code="visual_extraction_failed",
                        message=str(exc),
                        url=url,
                    )
                ],
            )

        visual = build_visual_identity(raw or {})
        warnings = list(guard.warnings)
        status = ModuleStatus.ok
        if guard.blocked_count:
            status = ModuleStatus.partial
            warnings.append(f"{guard.blocked_count} browser request(s) blocked")
        if visual.sampled_elements == 0:
            status = ModuleStatus.partial
            warnings.append("no visible elements sampled")

        return ModuleResult[VisualIdentity](
            status=status,
            duration_ms=_elapsed_ms(started),
            data=visual,
            warnings=warnings,
        )


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
