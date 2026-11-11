"""Phase 5 tests for the screenshot engine and its fixtures."""

import base64
import functools
import hashlib
import http.server
import threading
from pathlib import Path

import pytest

from site_dna.analyzers.screenshot import ScreenshotEngine, read_png_dimensions
from site_dna.core.config import Settings
from site_dna.models.common import ModuleStatus
from site_dna.services.browser import BrowserRequestGuard

FIXTURES = Path(__file__).parent.parent / "fixtures"
ONE_PIXEL_PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl2nQAAAABJRU5ErkJggg=="
)


class _RecordingHandler(http.server.SimpleHTTPRequestHandler):
    requests: list[str] = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        type(self).requests.append(self.path)
        super().do_GET()


@pytest.fixture
def fixture_server():
    _RecordingHandler.requests = []
    handler = functools.partial(_RecordingHandler, directory=str(FIXTURES))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    try:
        yield f"http://127.0.0.1:{port}", port, _RecordingHandler.requests
    finally:
        server.shutdown()
        server.server_close()


def _guard(port: int) -> BrowserRequestGuard:
    return BrowserRequestGuard(
        allow_private_hosts=True,
        allowed_ports={80, 443, port},
    )


def _settings(tmp_path: Path, **overrides) -> Settings:
    values = {
        "app_env": "test",
        "storage_dir": str(tmp_path),
        "allow_private_hosts": True,
    }
    values.update(overrides)
    return Settings(**values)


def test_read_png_dimensions_parses_ihdr():
    assert read_png_dimensions(ONE_PIXEL_PNG) == (1, 1)


def test_read_png_dimensions_rejects_invalid_data():
    with pytest.raises(ValueError):
        read_png_dimensions(b"not a png")


@pytest.mark.browser
@pytest.mark.anyio
async def test_capture_writes_png_with_matching_metadata(fixture_server, tmp_path):
    base_url, port, _ = fixture_server
    settings = _settings(tmp_path)
    engine = ScreenshotEngine(settings=settings, guard=_guard(port))

    result = await engine.capture(f"{base_url}/visual/palette.html", "scan-one")

    assert result.status == ModuleStatus.ok
    assert result.data is not None
    data = result.data
    path = Path(data.file.path)
    assert path.exists()
    assert path == tmp_path / "scan-one" / "homepage.png"

    raw = path.read_bytes()
    assert data.file.format == "png"
    assert data.file.bytes == len(raw)
    assert data.file.sha256 == hashlib.sha256(raw).hexdigest()
    assert (data.file.width, data.file.height) == read_png_dimensions(raw)
    assert data.file.width == 1440
    assert data.file.height == min(data.document_height, settings.scan_screenshot_max_height)
    assert data.viewport.width == 1440
    assert data.viewport.height == 900
    assert data.truncated is False
    assert data.scrolled_steps >= 1
    assert data.base64 is None


@pytest.mark.browser
@pytest.mark.anyio
async def test_capture_can_embed_png_base64(fixture_server, tmp_path):
    base_url, port, _ = fixture_server
    engine = ScreenshotEngine(settings=_settings(tmp_path), guard=_guard(port))

    result = await engine.capture(
        f"{base_url}/visual/palette.html",
        "scan-embed",
        embed_images=True,
    )

    assert result.status == ModuleStatus.ok
    assert result.data is not None
    raw = Path(result.data.file.path).read_bytes()
    assert result.data.base64 == base64.b64encode(raw).decode("ascii")


@pytest.mark.browser
@pytest.mark.anyio
async def test_capture_forces_lazy_images_to_load(fixture_server, tmp_path):
    base_url, port, requests = fixture_server
    engine = ScreenshotEngine(settings=_settings(tmp_path), guard=_guard(port))

    result = await engine.capture(f"{base_url}/site_lazy/index.html", "scan-lazy")

    assert result.status == ModuleStatus.ok
    assert "/site_lazy/lazy-red.svg" in requests
    assert "/site_lazy/lazy-blue.svg" in requests


@pytest.mark.browser
@pytest.mark.anyio
async def test_capture_clips_tall_page_and_marks_truncated(fixture_server, tmp_path):
    base_url, port, _ = fixture_server
    settings = _settings(tmp_path, scan_screenshot_max_height=16000)
    engine = ScreenshotEngine(settings=settings, guard=_guard(port))

    result = await engine.capture(f"{base_url}/site_tall/index.html", "scan-tall")

    assert result.status == ModuleStatus.ok
    assert result.data is not None
    data = result.data
    assert data.truncated is True
    assert data.document_height > settings.scan_screenshot_max_height
    assert data.file.height == settings.scan_screenshot_max_height
    assert data.file.width == 1440
    assert Path(data.file.path).exists()
