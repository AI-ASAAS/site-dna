"""Phase 9 tests for the unified pipeline and CLI wiring."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import jsonschema
import pytest

from site_dna.app.pipeline import ScanPipeline
from site_dna.app.scan import run_scan_cli, run_schema_cli
from site_dna.core.config import ScanConfig, Settings
from site_dna.core.context import ScanContext
from site_dna.crawler.crawl_manager import DiscoveredStatus, DiscoveredUrl
from site_dna.crawler.robots import RobotsTxt
from site_dna.models.common import FileRef, ModuleResult, ModuleStatus
from site_dna.models.page import PageData
from site_dna.models.performance import Performance, StrategyPerformance
from site_dna.models.report import WebsiteContent
from site_dna.models.seo import CheckRecord, SeoAnalysis
from site_dna.models.visual import ScreenshotResult, ScreenshotViewport, VisualIdentity
from site_dna.scan import build_placeholder_report
from site_dna.schema.schema_export import build_schema

URL = "https://example.com/"
GOOD_HTML = """<html lang="en"><head>
<title>Reliable Website Auditing Services for Teams</title>
<meta name="description" content="A sufficiently long meta description for the page that should pass the configured minimum length requirement.">
<meta name="viewport" content="width=device-width">
<link rel="canonical" href="https://example.com/">
<meta property="og:title" content="t">
<meta property="og:description" content="d">
<meta property="og:image" content="i">
</head><body><h1>Home</h1><h2>Sub</h2></body></html>"""


def _context(tmp_path: Path) -> ScanContext:
    settings = Settings(app_env="test", log_level="WARNING")
    config = ScanConfig(input_url=URL, permission_attested=True, max_pages=2, max_depth=1)
    return ScanContext(
        config=config,
        settings=settings,
        scan_id="scan9",
        output_dir=tmp_path / "scan9",
        logger=logging.getLogger("test.phase9"),
        started_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _robots() -> RobotsTxt:
    return RobotsTxt.from_text("https://example.com", "User-agent: *\nAllow: /\n")


class FakeClient:
    def __init__(self):
        self.calls = []

    async def safe_get(self, url):
        self.calls.append(url)
        return type("Response", (), {"status_code": 404, "content": b""})()

    async def aclose(self):
        return None


class FakeCrawler:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    async def crawl(self, seed_url):
        self.calls.append(seed_url)
        if self.error:
            raise self.error
        return [
            DiscoveredUrl(
                url=seed_url,
                depth=0,
                category="home",
                status=DiscoveredStatus.fetched,
            )
        ]


class FakeExtractor:
    def __init__(self):
        self.targets = []

    async def extract(self, targets):
        self.targets = list(targets)
        page = PageData(
            url=URL,
            final_url=URL,
            http_status=200,
            title="Reliable Website Auditing Services for Teams",
            language="en",
            raw_html=GOOD_HTML,
        )
        return ModuleResult[WebsiteContent](
            status=ModuleStatus.ok,
            duration_ms=10,
            data=WebsiteContent(pages=[page], total_pages=1, total_words=2),
        )


class FakeVisual:
    async def extract(self, url):
        return ModuleResult[VisualIdentity](
            status=ModuleStatus.ok,
            duration_ms=20,
            data=VisualIdentity(sampled_elements=3),
        )


class FakeScreenshot:
    async def capture(self, url, scan_id, *, embed_images=False):
        file_ref = FileRef(path="homepage.png", format="png", bytes=10, sha256="a" * 64)
        return ModuleResult[ScreenshotResult](
            status=ModuleStatus.ok,
            duration_ms=30,
            data=ScreenshotResult(
                file=file_ref,
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
            duration_ms=40,
            data=Performance(
                mobile=StrategyPerformance(status=ModuleStatus.ok, score=90),
                desktop=StrategyPerformance(status=ModuleStatus.ok, score=95),
            ),
        )


class FakeSeo:
    def __init__(self):
        self.pages = []

    async def analyze(self, pages, **kwargs):
        self.pages = list(pages)
        return ModuleResult[SeoAnalysis](
            status=ModuleStatus.ok,
            duration_ms=50,
            data=SeoAnalysis(
                checks=[
                    CheckRecord(
                        id="title",
                        scope="page",
                        url=URL,
                        status="passed",
                        confidence="high",
                    )
                ]
            ),
        )


@pytest.mark.anyio
async def test_pipeline_wires_all_modules_and_attaches_screenshot(tmp_path):
    visual = FakeVisual()
    performance = FakePerformance()
    seo = FakeSeo()
    pipeline = ScanPipeline(
        _context(tmp_path),
        http_client=FakeClient(),
        crawler=FakeCrawler(),
        content_extractor=FakeExtractor(),
        visual_extractor=visual,
        screenshot_engine=FakeScreenshot(),
        performance_client=performance,
        seo_analyzer=seo,
        robots=_robots(),
    )

    report = await pipeline.run()

    assert report.project_info.final_url == URL
    assert report.project_info.scan_status == "completed"
    assert report.website_content.data.total_pages == 1
    assert report.visual_identity.data.screenshot.path == "homepage.png"
    assert report.performance.data.mobile.score == 90
    assert report.seo_analysis.data.checks[0].id == "title"
    assert seo.pages[0].url == URL
    assert report.execution_summary.module_results == {
        "website_content": "ok",
        "visual_identity": "ok",
        "performance": "ok",
        "seo_analysis": "ok",
    }


@pytest.mark.anyio
async def test_pipeline_preserves_other_modules_when_one_fails(tmp_path):
    class FailingVisual:
        async def extract(self, url):
            raise RuntimeError("visual boom")

    class FailingPerformance:
        async def fetch_performance(self, url):
            raise RuntimeError("psi boom")

    pipeline = ScanPipeline(
        _context(tmp_path),
        http_client=FakeClient(),
        crawler=FakeCrawler(),
        content_extractor=FakeExtractor(),
        visual_extractor=FailingVisual(),
        screenshot_engine=FakeScreenshot(),
        performance_client=FailingPerformance(),
        seo_analyzer=FakeSeo(),
        robots=_robots(),
    )

    report = await pipeline.run()

    assert report.website_content.status is ModuleStatus.ok
    assert report.visual_identity.status is ModuleStatus.partial
    assert report.visual_identity.data.screenshot is not None
    assert report.performance.status is ModuleStatus.failed
    assert report.performance.errors[0].code == "performance_failed"
    assert report.seo_analysis.status is ModuleStatus.ok
    assert report.project_info.scan_status == "partial"


@pytest.mark.anyio
async def test_pipeline_continues_after_crawl_failure(tmp_path):
    pipeline = ScanPipeline(
        _context(tmp_path),
        http_client=FakeClient(),
        crawler=FakeCrawler(error=RuntimeError("crawl boom")),
        content_extractor=FakeExtractor(),
        visual_extractor=FakeVisual(),
        screenshot_engine=FakeScreenshot(),
        performance_client=FakePerformance(),
        seo_analyzer=FakeSeo(),
        robots=_robots(),
    )

    report = await pipeline.run()

    assert report.website_content.status is ModuleStatus.failed
    assert report.website_content.data.pages == []
    assert report.visual_identity.status is ModuleStatus.ok
    assert report.performance.status is ModuleStatus.ok
    assert report.seo_analysis.status is ModuleStatus.ok
    assert report.project_info.scan_status == "partial"


@pytest.mark.anyio
async def test_pipeline_uses_real_seo_analyzer_with_crawled_pages(tmp_path):
    pipeline = ScanPipeline(
        _context(tmp_path),
        http_client=FakeClient(),
        crawler=FakeCrawler(),
        content_extractor=FakeExtractor(),
        visual_extractor=FakeVisual(),
        screenshot_engine=FakeScreenshot(),
        performance_client=FakePerformance(),
        robots=_robots(),
    )

    report = await pipeline.run()

    assert report.seo_analysis.status is ModuleStatus.ok
    checks = {check.id: check for check in report.seo_analysis.data.checks}
    assert checks["title"].status.value == "passed"
    assert checks["meta_description"].status.value == "passed"
    assert checks["sitemap"].status.value == "warning"


class FakePipeline:
    def __init__(self, context):
        self.context = context

    async def run(self, url=None):
        return build_placeholder_report(
            scan_id=self.context.scan_id,
            input_url=url or self.context.config.input_url,
            config=self.context.config.model_dump(mode="json"),
        )


def test_cli_requires_permission_and_writes_nothing(tmp_path):
    exit_code = run_scan_cli(
        url=URL,
        i_have_permission=False,
        output_dir=str(tmp_path),
    )

    assert exit_code == 2
    assert list(tmp_path.iterdir()) == []


def test_cli_runs_pipeline_and_writes_report_and_log(tmp_path):
    exit_code = run_scan_cli(
        url=URL,
        i_have_permission=True,
        output_dir=str(tmp_path),
        pipeline_factory=FakePipeline,
    )

    assert exit_code == 0
    report_paths = list(tmp_path.glob("*/report.json"))
    assert len(report_paths) == 1
    report = json.loads(report_paths[0].read_text(encoding="utf-8"))
    assert report["project_info"]["input_url"] == URL
    assert (report_paths[0].parent / "scan.log").exists()


def test_schema_cli_exports_valid_schema(tmp_path):
    path = tmp_path / "schema.json"

    assert run_schema_cli(str(path)) == 0
    assert json.loads(path.read_text(encoding="utf-8")) == build_schema()


def test_pipeline_report_validates_against_schema(tmp_path):
    report = build_placeholder_report(
        scan_id="x",
        input_url=URL,
        config={"max_pages": 1},
    )
    jsonschema.validate(json.loads(report.model_dump_json()), build_schema())


def test_committed_sample_report_is_schema_valid():
    path = Path(__file__).parents[1] / "fixtures" / "phase9" / "sample_report.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    jsonschema.validate(payload, build_schema())
    assert payload["project_info"]["scan_status"] == "partial"
    assert payload["website_content"]["data"]["total_pages"] == 2


@pytest.mark.anyio
async def test_pipeline_rejects_invalid_url(tmp_path):
    pipeline = ScanPipeline(
        _context(tmp_path),
        http_client=FakeClient(),
        crawler=FakeCrawler(),
        content_extractor=FakeExtractor(),
        visual_extractor=FakeVisual(),
        screenshot_engine=FakeScreenshot(),
        performance_client=FakePerformance(),
        seo_analyzer=FakeSeo(),
        robots=_robots(),
    )

    report = await pipeline.run("not-a-url")

    assert report.project_info.scan_status == "rejected"
    assert report.execution_summary.errors[0].code == "rejected"


@pytest.mark.anyio
async def test_pipeline_module_timeout_is_partial(tmp_path):
    class SlowVisual:
        async def extract(self, url):
            await asyncio.sleep(0.05)
            return ModuleResult[VisualIdentity](status=ModuleStatus.ok, duration_ms=50, data=VisualIdentity())

    context = _context(tmp_path)
    context.config.max_total_seconds = 0.01
    pipeline = ScanPipeline(
        context,
        http_client=FakeClient(),
        crawler=FakeCrawler(),
        content_extractor=FakeExtractor(),
        visual_extractor=SlowVisual(),
        screenshot_engine=FakeScreenshot(),
        performance_client=FakePerformance(),
        seo_analyzer=FakeSeo(),
        robots=_robots(),
    )

    report = await pipeline.run()

    assert report.visual_identity.status is ModuleStatus.partial
    assert any("timed out" in error.message for error in report.visual_identity.errors)
    assert report.performance.status is ModuleStatus.ok
    assert report.project_info.scan_status == "partial"
