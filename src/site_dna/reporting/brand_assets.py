"""Official ASAAS AI brand assets and Thmanyah font embedding for Site DNA PDF reports."""

import base64
from functools import lru_cache
from pathlib import Path

# Paths to assets
_ASSETS_DIR = Path(__file__).resolve().parent / "assets"
_LOGOS_DIR = _ASSETS_DIR / "logos"
_FONTS_DIR = _ASSETS_DIR / "fonts"

# Brand color tokens per ASAAS AI Guidelines
BRAND_COLORS = {
    "ink": "#221f1f",
    "gold": "#ba9555",
    "gold_accent": "#d8b36f",
    "sand": "#d3c6b4",
    "clay": "#c3ad8d",
    "cream": "#ede7da",
    "paper": "#fcf9f5",
    "white": "#ffffff",
    "hairline": "rgba(34, 31, 31, 0.12)",
    "glass_tint": "rgba(252, 249, 245, 0.75)",
}


@lru_cache(maxsize=4)
def get_logo_data_uri(variant: str = "dark") -> str:
    """Return official ASAAS AI logo as base64 data URI."""
    filename = "logo-light.png" if variant == "light" else "logo-dark.png"
    logo_path = _LOGOS_DIR / filename
    if not logo_path.exists():
        # Fallback to alternative logo file or favicon
        fav_path = _LOGOS_DIR / "favicon.png"
        if fav_path.exists():
            data = base64.b64encode(fav_path.read_bytes()).decode("ascii")
            return f"data:image/png;base64,{data}"
        return ""

    data = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


@lru_cache(maxsize=8)
def _get_font_b64(subpath: str) -> str:
    """Read a woff2 font file and return base64 string."""
    font_path = _FONTS_DIR / subpath
    if not font_path.exists():
        return ""
    return base64.b64encode(font_path.read_bytes()).decode("ascii")


@lru_cache(maxsize=1)
def get_thmanyah_font_css() -> str:
    """Generate standalone @font-face CSS blocks with embedded base64 WOFF2 fonts."""
    # We embed:
    # 1. Thmanyah Sans (Regular 400 & Bold 700)
    # 2. Thmanyah Serif Display (Bold 700)
    # 3. Thmanyah Serif Text (Regular 400)
    sans_reg = _get_font_b64("sans/thmanyahsans-Regular.woff2")
    sans_bold = _get_font_b64("sans/thmanyahsans-Bold.woff2")
    serif_disp_bold = _get_font_b64("serif-display/thmanyahserifdisplay-Bold.woff2")
    serif_text_reg = _get_font_b64("serif-text/thmanyahseriftext-Regular.woff2")

    css_parts = []
    if sans_reg:
        css_parts.append(f"""
@font-face {{
  font-family: 'Thmanyah Sans';
  src: url('data:font/woff2;base64,{sans_reg}') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: block;
}}
""")

    if sans_bold:
        css_parts.append(f"""
@font-face {{
  font-family: 'Thmanyah Sans';
  src: url('data:font/woff2;base64,{sans_bold}') format('woff2');
  font-weight: 700;
  font-style: normal;
  font-display: block;
}}
""")

    if serif_disp_bold:
        css_parts.append(f"""
@font-face {{
  font-family: 'Thmanyah Serif Display';
  src: url('data:font/woff2;base64,{serif_disp_bold}') format('woff2');
  font-weight: 700;
  font-style: normal;
  font-display: block;
}}
""")

    if serif_text_reg:
        css_parts.append(f"""
@font-face {{
  font-family: 'Thmanyah Serif Text';
  src: url('data:font/woff2;base64,{serif_text_reg}') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: block;
}}
""")

    return "\n".join(css_parts)


def get_brand_css() -> str:
    """Return complete embedded brand styling for PDF report generation."""
    font_css = get_thmanyah_font_css()
    return f"""
{font_css}

:root {{
  --ink: {BRAND_COLORS["ink"]};
  --gold: {BRAND_COLORS["gold"]};
  --gold-accent: {BRAND_COLORS["gold_accent"]};
  --sand: {BRAND_COLORS["sand"]};
  --clay: {BRAND_COLORS["clay"]};
  --cream: {BRAND_COLORS["cream"]};
  --paper: {BRAND_COLORS["paper"]};
  --hairline: {BRAND_COLORS["hairline"]};
  
  --font-sans: 'Thmanyah Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-display: 'Thmanyah Serif Display', 'Thmanyah Sans', serif;
  --font-text: 'Thmanyah Serif Text', 'Thmanyah Sans', serif;
}}
"""
