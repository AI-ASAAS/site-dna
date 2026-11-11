"""Phase 3 unit and browser tests for the content extractor."""

import hashlib
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

from site_dna.analyzers.content_extractor import (
    ContentExtractor,
    Crawl4AIRenderer,
    RenderedPage,
)
from site_dna.crawler.crawl_manager import DiscoveredUrl
from site_dna.models.common import ModuleStatus

STATIC_HTML = """<!doctype html>
<html lang="en">
<head><title>Acme About</title></head>
<body>
  <nav><a href="/nav-link">Nav</a></nav>
  <main>
    <h1>About Acme</h1>
    <h2>Our Mission</h2>
    <h2>Our Team</h2>
    <h3>Leadership</h3>
    <p>First paragraph.</p>
    <p>Second paragraph.</p>
    <ul><li>One</li></ul>
    <ol><li>Two</li></ol>
    <a href="/about/team">Team</a>
    <a href="https://external.org/page">External</a>
    <a href="mailto:hello@example.com">Email</a>
    <a href="tel:+123">Phone</a>
    <a href="javascript:void(0)">JS</a>
    <a href="/about#frag">Frag</a>
    <img src="/img/logo.png" alt="Logo" width="100" height="50" loading="lazy">
    <img data-src="/img/lazy.png" alt="">
    <img srcset="/img/a.png 1x, /img/b.png 2x" alt="Srcset">
    <img src="/img/no-alt.png">
  </main>
  <footer><a href="/footer">Footer</a></footer>
  <script>console.log('noise')</script>
</body>
</html>"""


class FakeRenderer:
    def __init__(self, pages):
        self.pages = pages

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None

    async def render(self, url):
        page = self.pages[url]
        if isinstance(page, Exception):
            raise page
        return page


def _rendered(url="https://example.com/about", html=STATIC_HTML, **kwargs):
    options = {
        "url": url,
        "final_url": url,
        "status_code": 200,
        "html": html,
        "raw_markdown": "About Acme\n\nOur Mission",
        "fit_markdown": "About Acme\n\nOur Mission",
        "fetch_ms": 12,
    }
    options.update(kwargs)
    return RenderedPage(**options)


def _target(url="https://example.com/about", depth=1, category="about"):
    return DiscoveredUrl(url=url, depth=depth, category=category)


async def _extract(tmp_path, renderer, targets):
    extractor = ContentExtractor(scan_id="scan123", storage_dir=tmp_path, renderer=renderer)
    return await extractor.extract(targets)


@pytest.mark.anyio
async def test_static_page_yields_exact_heading_link_and_image_counts(tmp_path):
    renderer = FakeRenderer({_target().url: _rendered()})

    result = await _extract(tmp_path, renderer, [_target()])

    assert result.status == ModuleStatus.ok
    page = result.data.pages[0]
    assert page.url == "https://example.com/about"
    assert page.final_url == "https://example.com/about"
    assert page.http_status == 200
    assert page.title == "Acme About"
    assert page.language == "en"
    assert page.category == "about"
    assert page.depth == 1

    assert page.headings.h1 == ["About Acme"]
    assert page.headings.h2 == ["Our Mission", "Our Team"]
    assert page.headings.h3 == ["Leadership"]
    assert [item.level for item in page.heading_outline] == [1, 2, 2, 3]

    assert page.paragraphs_count == 2
    assert page.lists_count == 2

    links = {link.url: link for link in page.links}
    assert set(links) == {
        "https://example.com/about/team",
        "https://external.org/page",
        "https://example.com/about",
    }
    assert links["https://example.com/about/team"].internal is True
    assert links["https://external.org/page"].internal is False
    assert links["https://example.com/about"].internal is True
    assert page.non_http_link_counts == {"mailto": 1, "tel": 1, "javascript": 1}

    images = page.images
    assert len(images) == 4
    assert images[0].src == "https://example.com/img/logo.png"
    assert images[0].alt == "Logo"
    assert images[0].width == 100
    assert images[0].height == 50
    assert images[0].loading == "lazy"
    assert images[1].src == "https://example.com/img/lazy.png"
    assert images[1].alt == ""
    assert images[2].src == "https://example.com/img/a.png"
    assert images[2].alt == "Srcset"
    assert images[3].alt is None

    assert page.markdown == "About Acme\n\nOur Mission"
    assert page.markdown_chars == len("About Acme\n\nOur Mission")
    assert page.word_count == 4
    assert page.html_sha256 == hashlib.sha256(STATIC_HTML.encode("utf-8")).hexdigest()


@pytest.mark.anyio
async def test_raw_html_is_retained_but_excluded_from_serialization(tmp_path):
    renderer = FakeRenderer({_target().url: _rendered()})

    result = await _extract(tmp_path, renderer, [_target()])

    page = result.data.pages[0]
    assert page.raw_html == STATIC_HTML
    assert "raw_html" not in page.model_dump()
    assert "raw_html" not in result.data.model_dump()["pages"][0]
    assert '"raw_html"' not in page.model_dump_json()


@pytest.mark.anyio
async def test_fit_markdown_fallback_records_warning(tmp_path):
    renderer = FakeRenderer(
        {_target().url: _rendered(fit_markdown="", raw_markdown="Raw content only")}
    )

    result = await _extract(tmp_path, renderer, [_target()])

    page = result.data.pages[0]
    assert page.markdown == "Raw content only"
    assert any("fit" in warning and "raw=" in warning for warning in result.warnings)


@pytest.mark.anyio
async def test_large_markdown_is_written_to_storage(tmp_path):
    long_markdown = "x" * 1200
    renderer = FakeRenderer(
        {_target().url: _rendered(fit_markdown=None, raw_markdown=long_markdown)}
    )
    extractor = ContentExtractor(
        scan_id="scan123",
        storage_dir=tmp_path,
        renderer=renderer,
        inline_markdown_limit=1000,
    )

    result = await extractor.extract([_target()])

    page = result.data.pages[0]
    assert page.markdown is None
    assert page.markdown_file is not None
    assert page.markdown_chars == 1200
    stored = tmp_path / "scan123" / "pages" / "1.md"
    assert stored.exists()
    assert stored.read_text(encoding="utf-8") == long_markdown
    assert page.markdown_file.bytes == len(long_markdown.encode("utf-8"))
    assert page.markdown_file.sha256 == hashlib.sha256(long_markdown.encode("utf-8")).hexdigest()


@pytest.mark.anyio
async def test_404_page_is_recorded_without_aborting(tmp_path):
    ok_url = "https://example.com/"
    missing_url = "https://example.com/missing"
    renderer = FakeRenderer(
        {
            ok_url: _rendered(url=ok_url, final_url=ok_url, html="<html><body><h1>Home</h1></body></html>"),
            missing_url: _rendered(
                url=missing_url,
                final_url=missing_url,
                status_code=404,
                html="<html><body><h1>Not Found</h1></body></html>",
                raw_markdown="Not Found",
                fit_markdown="Not Found",
            ),
        }
    )

    result = await _extract(
        tmp_path,
        renderer,
        [_target(ok_url, depth=0, category="home"), _target(missing_url, depth=1, category="other")],
    )

    assert result.status == ModuleStatus.partial
    assert len(result.data.pages) == 2
    missing = result.data.pages[1]
    assert missing.url == missing_url
    assert missing.http_status == 404
    assert "404" in (missing.error or "")
    assert result.data.pages_failed == 1


@pytest.mark.anyio
async def test_renderer_exception_marks_page_failed_and_continues(tmp_path):
    ok_url = "https://example.com/"
    broken_url = "https://example.com/broken"
    renderer = FakeRenderer(
        {
            ok_url: _rendered(url=ok_url, final_url=ok_url),
            broken_url: RuntimeError("renderer crashed"),
        }
    )

    result = await _extract(
        tmp_path,
        renderer,
        [_target(ok_url, depth=0, category="home"), _target(broken_url, depth=1)],
    )

    assert result.status == ModuleStatus.partial
    assert len(result.data.pages) == 2
    assert result.data.pages[1].error == "renderer crashed"
    assert result.data.pages[1].url == broken_url
    assert result.data.pages_failed == 1


@pytest.mark.anyio
async def test_start_url_failure_marks_module_failed(tmp_path):
    start_url = "https://example.com/"
    renderer = FakeRenderer({start_url: RuntimeError("start failed")})

    result = await _extract(tmp_path, renderer, [_target(start_url, depth=0, category="home")])

    assert result.status == ModuleStatus.failed
    assert result.data.pages[0].error == "start failed"


@pytest.mark.anyio
async def test_start_url_404_marks_module_failed(tmp_path):
    start_url = "https://example.com/"
    renderer = FakeRenderer(
        {
            start_url: _rendered(
                url=start_url,
                final_url=start_url,
                status_code=404,
                html="<html><body>missing</body></html>",
            )
        }
    )

    result = await _extract(tmp_path, renderer, [_target(start_url, depth=0, category="home")])

    assert result.status == ModuleStatus.failed
    assert result.data.pages[0].http_status == 404


@pytest.mark.anyio
async def test_every_page_has_url(tmp_path):
    renderer = FakeRenderer(
        {
            "https://example.com/": _rendered(url="https://example.com/", final_url="https://example.com/"),
            "https://example.com/about": _rendered(),
        }
    )

    result = await _extract(
        tmp_path,
        renderer,
        [
            _target("https://example.com/", depth=0, category="home"),
            _target("https://example.com/about", depth=1, category="about"),
        ],
    )

    assert all(page.url for page in result.data.pages)


@pytest.mark.browser
@pytest.mark.anyio
async def test_crawl4ai_renders_javascript_injected_content(tmp_path):
    page_html = b"""<!doctype html>
<html><head><title>JS Page</title></head>
<body>
  <div id="app">raw text only</div>
  <script>
    const parts = ['Injected', 'by', 'JavaScript'];
    document.getElementById('app').textContent = parts.join(' ');
  </script>
</body></html>"""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page_html)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/"
    try:
        raw = httpx.get(url, timeout=10.0).text
        assert "Injected by JavaScript" not in raw

        extractor = ContentExtractor(
            scan_id="scanjs",
            storage_dir=tmp_path,
            renderer=Crawl4AIRenderer(),
        )
        result = await extractor.extract([_target(url, depth=0, category="home")])

        page = result.data.pages[0]
        assert "Injected by JavaScript" in (page.markdown or "")
        assert "Injected by JavaScript" in page.raw_html
    finally:
        server.shutdown()
        server.server_close()
