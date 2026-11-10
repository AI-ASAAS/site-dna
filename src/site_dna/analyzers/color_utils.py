"""CSS color parsing, alpha compositing, and palette heuristics (Phase 4)."""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RGBA:
    """An sRGB color with channels 0-255 and alpha 0-1."""

    r: int
    g: int
    b: int
    a: float = 1.0


NAMED_COLORS = {
    "transparent": RGBA(0, 0, 0, 0.0),
    "black": RGBA(0, 0, 0, 1.0),
    "white": RGBA(255, 255, 255, 1.0),
    "red": RGBA(255, 0, 0, 1.0),
    "green": RGBA(0, 128, 0, 1.0),
    "blue": RGBA(0, 0, 255, 1.0),
    "gray": RGBA(128, 128, 128, 1.0),
    "grey": RGBA(128, 128, 128, 1.0),
    "silver": RGBA(192, 192, 192, 1.0),
    "maroon": RGBA(128, 0, 0, 1.0),
    "olive": RGBA(128, 128, 0, 1.0),
    "lime": RGBA(0, 255, 0, 1.0),
    "aqua": RGBA(0, 255, 255, 1.0),
    "cyan": RGBA(0, 255, 255, 1.0),
    "teal": RGBA(0, 128, 128, 1.0),
    "navy": RGBA(0, 0, 128, 1.0),
    "fuchsia": RGBA(255, 0, 255, 1.0),
    "magenta": RGBA(255, 0, 255, 1.0),
    "purple": RGBA(128, 0, 128, 1.0),
    "yellow": RGBA(255, 255, 0, 1.0),
    "orange": RGBA(255, 165, 0, 1.0),
}

_RGB_RE = re.compile(r"^rgba?\((.*)\)$", re.IGNORECASE)
_HSL_RE = re.compile(r"^hsla?\((.*)\)$", re.IGNORECASE)
_COLOR_FN_RE = re.compile(r"^color\((.*)\)$", re.IGNORECASE)
_HEX_RE = re.compile(r"^#([0-9a-f]{3,8})$", re.IGNORECASE)


def parse_color(value: str | None) -> RGBA | None:
    """Parse a computed CSS color string into RGBA, or return None."""
    if not value:
        return None

    cleaned = value.strip().lower()
    if not cleaned:
        return None
    if cleaned in {"none", "inherit", "initial", "unset", "currentcolor"}:
        return None
    if cleaned in NAMED_COLORS:
        return NAMED_COLORS[cleaned]

    hex_match = _HEX_RE.match(cleaned)
    if hex_match:
        return _parse_hex(hex_match.group(1))

    rgb_match = _RGB_RE.match(cleaned)
    if rgb_match:
        return _parse_rgb_body(rgb_match.group(1))

    hsl_match = _HSL_RE.match(cleaned)
    if hsl_match:
        return _parse_hsl_body(hsl_match.group(1))

    color_match = _COLOR_FN_RE.match(cleaned)
    if color_match:
        return _parse_color_function_body(color_match.group(1))

    return None


def _parse_hex(value: str) -> RGBA | None:
    if len(value) in (3, 4):
        channels = [int(char * 2, 16) for char in value]
    elif len(value) in (6, 8):
        channels = [int(value[index : index + 2], 16) for index in range(0, len(value), 2)]
    else:
        return None

    alpha = channels[3] / 255 if len(channels) == 4 else 1.0
    return RGBA(channels[0], channels[1], channels[2], alpha)


def _split_color_arguments(body: str) -> list[str]:
    return body.replace("/", " ").replace(",", " ").split()


def _parse_channel(token: str) -> float:
    if token.endswith("%"):
        return float(token[:-1]) * 2.55
    return float(token)


def _parse_alpha(token: str) -> float:
    if token.endswith("%"):
        value = float(token[:-1]) / 100
    else:
        value = float(token)
    return max(0.0, min(1.0, value))


def _clamp_channel(value: float) -> int:
    return max(0, min(255, int(round(value))))


def _parse_rgb_body(body: str) -> RGBA | None:
    parts = _split_color_arguments(body)
    if len(parts) < 3:
        return None
    try:
        channels = [_parse_channel(part) for part in parts[:3]]
        alpha = _parse_alpha(parts[3]) if len(parts) >= 4 else 1.0
    except ValueError:
        return None
    return RGBA(
        _clamp_channel(channels[0]),
        _clamp_channel(channels[1]),
        _clamp_channel(channels[2]),
        alpha,
    )


def _parse_hsl_body(body: str) -> RGBA | None:
    parts = _split_color_arguments(body)
    if len(parts) < 3:
        return None
    try:
        hue = float(parts[0].removesuffix("deg"))
        saturation = float(parts[1].removesuffix("%")) / 100
        lightness = float(parts[2].removesuffix("%")) / 100
        alpha = _parse_alpha(parts[3]) if len(parts) >= 4 else 1.0
    except ValueError:
        return None

    red, green, blue = _hsl_to_rgb(hue, saturation, lightness)
    return RGBA(red, green, blue, alpha)


def _parse_color_function_body(body: str) -> RGBA | None:
    parts = _split_color_arguments(body)
    if len(parts) < 4:
        return None

    try:
        channels = [float(part.removesuffix("%")) for part in parts[1:4]]
        if any(part.endswith("%") for part in parts[1:4]):
            channels = [channel * 2.55 for channel in channels]
        else:
            channels = [channel * 255 for channel in channels]
        alpha = _parse_alpha(parts[4]) if len(parts) >= 5 else 1.0
    except ValueError:
        return None

    return RGBA(
        _clamp_channel(channels[0]),
        _clamp_channel(channels[1]),
        _clamp_channel(channels[2]),
        alpha,
    )


def _hsl_to_rgb(hue: float, saturation: float, lightness: float) -> tuple[int, int, int]:
    hue = (hue % 360) / 360
    if saturation <= 0:
        channel = _clamp_channel(lightness * 255)
        return channel, channel, channel

    q = lightness * (1 + saturation) if lightness < 0.5 else lightness + saturation - lightness * saturation
    p = 2 * lightness - q
    red = _hue_to_rgb(p, q, hue + 1 / 3)
    green = _hue_to_rgb(p, q, hue)
    blue = _hue_to_rgb(p, q, hue - 1 / 3)
    return _clamp_channel(red * 255), _clamp_channel(green * 255), _clamp_channel(blue * 255)


def _hue_to_rgb(p: float, q: float, t: float) -> float:
    if t < 0:
        t += 1
    if t > 1:
        t -= 1
    if t < 1 / 6:
        return p + (q - p) * 6 * t
    if t < 1 / 2:
        return q
    if t < 2 / 3:
        return p + (q - p) * (2 / 3 - t) * 6
    return p


def composite(foreground: RGBA, background: RGBA) -> RGBA:
    """Composite a foreground color over a background color."""
    alpha = foreground.a + background.a * (1 - foreground.a)
    if alpha <= 0:
        return RGBA(0, 0, 0, 0.0)

    red = (foreground.r * foreground.a + background.r * background.a * (1 - foreground.a)) / alpha
    green = (foreground.g * foreground.a + background.g * background.a * (1 - foreground.a)) / alpha
    blue = (foreground.b * foreground.a + background.b * background.a * (1 - foreground.a)) / alpha
    return RGBA(_clamp_channel(red), _clamp_channel(green), _clamp_channel(blue), alpha)


def to_hex(color: RGBA) -> str:
    """Render an RGBA color as an uppercase six-digit hex string."""
    return f"#{color.r:02X}{color.g:02X}{color.b:02X}"


def rgb_to_hsl(red: int, green: int, blue: int) -> tuple[float, float, float]:
    """Convert sRGB channels to (hue degrees, saturation 0-1, lightness 0-1)."""
    r = red / 255
    g = green / 255
    b = blue / 255
    maximum = max(r, g, b)
    minimum = min(r, g, b)
    delta = maximum - minimum
    lightness = (maximum + minimum) / 2

    if delta == 0:
        return 0.0, 0.0, lightness

    saturation = delta / (2 - maximum - minimum) if lightness > 0.5 else delta / (maximum + minimum)

    if maximum == r:
        hue = ((g - b) / delta) % 6
    elif maximum == g:
        hue = (b - r) / delta + 2
    else:
        hue = (r - g) / delta + 4

    return hue * 60, saturation, lightness


def hue_distance(first: float, second: float) -> float:
    """Return the shortest angular distance between two hues."""
    difference = abs(first - second) % 360
    return min(difference, 360 - difference)


def is_neutral(hex_value: str) -> bool:
    """Heuristic: low saturation or near-black/near-white colors are neutral."""
    parsed = parse_color(hex_value)
    if parsed is None:
        return True
    _, saturation, lightness = rgb_to_hsl(parsed.r, parsed.g, parsed.b)
    return saturation < 0.12 or lightness < 0.06 or lightness > 0.94
