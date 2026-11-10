"""Phase 4 tests for visual identity aggregation and the palette fixture."""

import functools
import http.server
import threading
from pathlib import Path

import pytest

from site_dna.analyzers.visual_identity import (
    VisualIdentityExtractor,
    build_visual_identity,
)
from site_dna.models.common import ModuleStatus
from site_dna.services.browser import BrowserRequestGuard


def _sample(
    tag="p",
    *,
    color="rgb(34, 34, 34)",
    background="rgba(0, 0, 0, 0)",
    border_color="rgb(0, 0, 0)",
    border_width=0,
    fill=None,
    stroke=None,
    font_family='"PaletteBrand", "Helvetica Neue", Arial, sans-serif',
    font_size="16px",
    font_weight="400",
    has_text=True,
    text_length=100,
    area=1000,
    effective_bg="rgb(255, 255, 255)",
):
    return {
        "tag": tag,
        "color": color,
        "backgroundColor": background,
        "borderColor": border_color,
        "borderWidth": border_width,
        "fill": fill,
        "stroke": stroke,
        "fontFamily": font_family,
        "fontSize": font_size,
        "fontWeight": font_weight,
        "hasText": has_text,
        "textLength": text_length,
        "area": area,
        "effectiveBg": effective_bg,
    }


def _heading(color="rgb(34, 34, 34)", size="48px", weight="700", family='"PaletteBrand", "Helvetica Neue", Arial, sans-serif'):
    return {
        "color": color,
        "fontSize": size,
        "fontWeight": weight,
        "fontFamily": family,
        "lineHeight": "1.1",
        "letterSpacing": "-1px",
        "textTransform": "none",
    }


def _synthetic_samples():
    body = _sample(
        "body",
        background="rgb(255, 255, 255)",
        has_text=False,
        text_length=0,
        area=1_000_000,
    )
    body_text = _sample("p", color="rgb(34, 34, 34)", text_length=200, area=50_000)
    section = _sample(
        "section",
        background="rgb(241, 250, 238)",
        has_text=False,
        text_length=0,
        area=200_000,
    )
    brand_button = _sample(
        "button",
        background="rgb(230, 57, 70)",
        color="rgb(255, 255, 255)",
        text_length=9,
        area=8_000,
    )
    outline_button = _sample(
        "button",
        background="rgba(0, 0, 0, 0)",
        color="rgb(29, 53, 87)",
        border_color="rgb(69, 123, 157)",
        border_width=2,
        text_length=10,
        area=8_000,
    )
    link = _sample("a", color="rgb(29, 53, 87)", text_length=24, area=3_000)
    overlay = _sample(
        "div",
        background="rgba(0, 0, 0, 0)",
        has_text=False,
        text_length=0,
        area=30_000,
    )
    serif = _sample(
        "p",
        font_family='Georgia, "Times New Roman", serif',
        text_length=25,
        area=5_000,
    )
    mono = _sample(
        "p",
        font_family='"Courier New", monospace',
        text_length=25,
        area=5_000,
    )

    return {
        "samples": [body, body_text, section, brand_button, outline_button, link, overlay, serif, mono],
        "buttons": [brand_button, outline_button],
        "links": [link],
        "headings": {
            "h1": [_heading(size="48px", weight="700")],
            "h2": [_heading(size="32px", weight="600")],
            "h3": [_heading(size="24px", weight="500")],
        },
        "cssVariables": {
            "--brand-primary": "#E63946",
            "--not-a-color": "16px",
            "--transparent-overlay": "rgba(0, 0, 0, 0)",
        },
        "fonts": [
            {"family": "PaletteBrand", "weight": "400", "status": "loaded"},
            {"family": "Georgia", "weight": "400", "status": "loaded"},
            {"family": "Courier New", "weight": "400", "status": "loaded"},
        ],
        "sampledElements": 9,
        "truncatedSampling": False,
    }


def test_build_visual_identity_ranks_colors_and_assigns_roles():
    visual = build_visual_identity(_synthetic_samples())

    colors = {record.hex: record for record in visual.colors.all}
    assert "#FFFFFF" in colors
    assert "#F1FAEE" in colors
    assert "#E63946" in colors
    assert "#222222" in colors
    assert "#FF00FF" not in colors
    assert "#000000" not in colors
    assert visual.colors.all[0].hex == "#FFFFFF"
    assert visual.colors.all[0].source == "computed"
    assert sum(record.share for record in visual.colors.all) == pytest.approx(1.0, abs=0.01)

    assert visual.colors.roles.background[0].hex == "#FFFFFF"
    assert visual.colors.roles.background[1].hex == "#F1FAEE"
    assert visual.colors.roles.text[0].hex == "#222222"
    assert visual.colors.roles.primary[0].hex == "#E63946"
    assert visual.colors.roles.secondary[0].hex == "#1D3557"
    assert visual.colors.roles.primary[0].source == "inferred"
    assert visual.colors.roles.roles_method


def test_build_visual_identity_parses_typography_and_css_variables():
    visual = build_visual_identity(_synthetic_samples())

    primary = next(record for record in visual.typography.font_families if record.primary)
    assert primary.family == "PaletteBrand"
    assert primary.fallbacks == ["Helvetica Neue", "Arial", "sans-serif"]
    assert primary.loaded is True

    assert visual.typography.heading_styles["h1"].font_size == "48px"
    assert visual.typography.heading_styles["h2"].font_size == "32px"
    assert visual.typography.heading_styles["h3"].font_size == "24px"
    assert visual.typography.heading_styles["h1"].font_weight == "700"
    assert visual.typography.font_sizes["16px"] >= 1
    assert visual.typography.font_weights["400"] >= 1

    assert visual.css_variables == {"--brand-primary": "#E63946"}
    assert visual.sampled_elements == 9
    assert visual.truncated_sampling is False
    assert visual.screenshot is None


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture
def palette_server():
    site_dir = Path(__file__).parent.parent / "fixtures" / "visual"
    handler = functools.partial(_QuietHandler, directory=str(site_dir))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        yield f"http://127.0.0.1:{port}/palette.html", port
    finally:
        server.shutdown()
        server.server_close()


@pytest.mark.browser
@pytest.mark.anyio
async def test_palette_fixture_end_to_end(palette_server):
    url, port = palette_server
    guard = BrowserRequestGuard(
        allow_private_hosts=True,
        allowed_ports={80, 443, port},
    )
    extractor = VisualIdentityExtractor(guard=guard)

    result = await extractor.extract(url)

    assert result.status == ModuleStatus.ok
    assert result.data is not None
    visual = result.data

    colors = {record.hex: record for record in visual.colors.all}
    assert "#FF00FF" not in colors
    assert "#000000" not in colors
    assert visual.colors.roles.background[0].hex == "#FFFFFF"
    assert visual.colors.roles.text[0].hex == "#222222"
    assert visual.colors.roles.primary[0].hex == "#E63946"

    primary = next(record for record in visual.typography.font_families if record.primary)
    assert primary.family == "PaletteBrand"
    assert primary.fallbacks == ["Helvetica Neue", "Arial", "sans-serif"]
    assert isinstance(primary.loaded, bool)

    assert visual.typography.heading_styles["h1"].font_size == "48px"
    assert visual.typography.heading_styles["h2"].font_size == "32px"
    assert visual.typography.heading_styles["h3"].font_size == "24px"
    assert visual.sampled_elements > 0
    assert visual.truncated_sampling is False
    assert guard.blocked_count == 0
