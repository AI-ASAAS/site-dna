"""Phase 9 integration test: crawl, extract, SEO, and report assembly."""

import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

import jsonschema
import pytest

from site_dna.analyzers.content_extractor import ContentExtractor, RenderedPage
from site_dna.app.pipeline import ScanPipeline
from site_dna.core.config import ScanConfig, Settings
from site_dna.core.context import ScanContext
from site_dna.crawler.crawl_manager import CrawlManager
from site_dna.crawler.robots import RobotsTxt
from site_dna.models.common import FileRef, ModuleResult, ModuleStatus
from site_dna.models.performance import Performance, StrategyPerformance
from site_dna.models.visual import ScreenshotResult, ScreenshotViewport, VisualIdentity
from site_dna.schema.schema_export import build_schema
from site_dna.services.http_client import SafeHttpClient
from site_dna.services.report_generator import write_report
from site_dna.services.security import ValidatedUrl

HOME = """<html lang="en"><head>
<title>Reliable Website Auditing Services for Teams</title>
<meta name="description" content="A sufficiently long meta description for the page that should pass the configured minimum length requirement.">
<meta name="viewport" content="width=device-width">
<link rel="canonical" href="/">
<meta property="og:title" content="Home">
<meta property="og:description" content="Home description">
<meta property="og:image" content="/og.png">
</head><body><h1>Home</h1><h2>Intro</h2><a href="/about">About</a></body></html>"""

ABOUT = """<html lang="en"><head>
<title>About Our Website Auditing Team and Services</title>
<meta name="description" content="A sufficiently long meta description for the about page that should pass the configured minimum length requirement.">
<meta name="viewport" content="width=device-width">
<link rel="canonical" href="/about">
<meta property="og:title" content="About">
<meta property="og:description" content="About description">
<meta property="og:image" content="/og.png">
</head><body><h1>About</h1><h2>Team</h2></body></html>"""

SITEMAP = """<?xml version="1.0"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>{origin}/</loc></url>
  <url><loc>{origin}/about</loc></url>
</urlset>"""


class Handler(BaseHTTPRequestHandler):
    origin = ""

    def do_GET(self):
        if self.path == "/":
            body = HOME.replace('href="/"', f'href="{self.origin}/"')
            content_type = "text/html; charset=utf-8"
        elif self.path == "/about":
            body = ABOUT.replace('href="/about"', f'href="{self.origin}/about"')
            content_type = "text/html; charset=utf-8"
        elif self.path == "/sitemap.xml":
            body = SITEMAP.format(origin=self.origin)
            content_type = "application/xml"
        elif self.path == "/robots.txt":
            body = "User-agent: *\nAllow: /\n"
            content_type = "text/plain"
        else:
            self.send_response(404)
            self.end_headers()
            return
        payload = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        return None


class FakeRenderer:
    def __init__(self, pages):
        self.pages = pages

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return None

    async def render(self, url):
        return self.pages[url]


class FakeVisual:
    async def extract(self, url):
        return ModuleResult[VisualIdentity](
            status=ModuleStatus.ok,
            duration_ms=1,
            data=VisualIdentity(sampled_elements=1),
        )


class FakeScreenshot:
    async def capture(self, url, scan_id, *, embed_images=False):
        return ModuleResult[ScreenshotResult](
            status=ModuleStatus.ok,
            duration_ms=1,
            data=ScreenshotResult(
                file=FileRef(path="homepage.png", format="png", bytes=1, sha256="a" * 64),
                document_height=100,
                viewport=ScreenshotViewport(width=1440, height=900),
                truncated=False,
                scrolled_steps=0,
            ),
        )


class FakePerformance:
    async def fetch_performance(self, url):
        return ModuleResult[Performance](
            status=ModuleStatus.ok,
            duration_ms=1,
            data=Performance(
                mobile=StrategyPerformance(status=ModuleStatus.ok, score=88),
                desktop=StrategyPerformance(status=ModuleStatus.ok, score=92),
            ),
        )


async def _validator(url: str) -> ValidatedUrl:
    parts = urlsplit(url)
    return ValidatedUrl(
        url=url,
        scheme=parts.scheme,
        host=parts.hostname or "127.0.0.1",
        port=parts.port or 80,
        ips=["127.0.0.1"],
    )


@pytest.mark.anyio
async def test_local_site_end_to_end_report(tmp_path):
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    origin = f"http://127.0.0.1:{server.server_port}"
    Handler.origin = origin
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    home = RenderedPage(
            url=f"{origin}/",
            final_url=f"{origin}/",
            status_code=200,
            html=HOME.replace('href="/"', f'href="{origin}/"'),
            raw_markdown="Home\n\nIntro",
            fit_markdown="Home\n\nIntro",
            fetch_ms=1,
        )
    pages = {
        origin: home,
        f"{origin}/": home,
        f"{origin}/about": RenderedPage(
            url=f"{origin}/about",
            final_url=f"{origin}/about",
            status_code=200,
            html=ABOUT.replace('href="/about"', f'href="{origin}/about"'),
            raw_markdown="About\n\nTeam",
            fit_markdown="About\n\nTeam",
            fetch_ms=1,
        ),
    }

    settings = Settings(app_env="test", log_level="WARNING")
    context = ScanContext(
        config=ScanConfig(
            input_url=origin,
            permission_attested=True,
            max_pages=2,
            max_depth=1,
        ),
        settings=settings,
        scan_id="integration9",
        output_dir=tmp_path / "integration9",
        logger=None,
    )
    client = SafeHttpClient(
        validator=_validator,
        per_host_rps=10_000,
        retry_wait=0,
    )
    robots = RobotsTxt.from_text(origin, "User-agent: *\nAllow: /\n")
    crawler = CrawlManager(
        client=client,
        max_pages=2,
        max_depth=1,
        max_total_seconds=10,
        validator=_validator,
        robots=robots,
    )
    extractor = ContentExtractor(
        scan_id="integration9",
        storage_dir=tmp_path / "integration9",
        renderer=FakeRenderer(pages),
    )

    try:
        pipeline = ScanPipeline(
            context,
            http_client=client,
            crawler=crawler,
            content_extractor=extractor,
            visual_extractor=FakeVisual(),
            screenshot_engine=FakeScreenshot(),
            performance_client=FakePerformance(),
            robots=robots,
        )
        report = await pipeline.run()
        report_path = write_report(report, context.output_dir)
    finally:
        await client.aclose()
        server.shutdown()
        thread.join(timeout=5)

    assert report.website_content.data.total_pages == 2
    assert report.website_content.data.pages_failed == 0
    assert (report.project_info.final_url or "").rstrip("/") == origin
    assert report.visual_identity.data.screenshot is not None
    assert report.seo_analysis.data.summary.failed == 0
    checks = {check.id: check for check in report.seo_analysis.data.checks}
    assert checks["title"].status.value == "passed"
    assert checks["sitemap"].status.value == "passed"
    assert report_path.exists()
    jsonschema.validate(report.model_dump(mode="json"), build_schema())

