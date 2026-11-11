"""Unified Website Intelligence scan pipeline (Phase 9)."""

import asyncio
import time
from typing import Any
from urllib.parse import urlsplit

from site_dna.analyzers.content_extractor import ContentExtractor
from site_dna.analyzers.screenshot import ScreenshotEngine
from site_dna.analyzers.seo import SeoAnalyzer
from site_dna.analyzers.visual_identity import VisualIdentityExtractor
from site_dna.core.context import ScanContext
from site_dna.crawler.crawl_manager import CrawlManager, DiscoveredStatus
from site_dna.crawler.robots import fetch_robots
from site_dna.integrations.pagespeed import PageSpeedClient
from site_dna.models.common import ModuleError, ModuleResult, ModuleStatus
from site_dna.models.report import Report, WebsiteContent
from site_dna.models.visual import VisualIdentity
from site_dna.services.http_client import SafeHttpClient
from site_dna.services.report_generator import MODULE_NAMES, build_report


def _origin(url: str) -> str:
    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        raise ValueError(f"invalid scan URL: {url}")
    return f"{parts.scheme}://{parts.netloc}"


def _failed(name: str, exc: Exception, *, url: str | None = None) -> ModuleResult[Any]:
    return ModuleResult[Any](
        status=ModuleStatus.failed,
        reason=str(exc) or exc.__class__.__name__,
        duration_ms=0,
        data=None,
        errors=[ModuleError(code=f"{name}_failed", message=str(exc), url=url)],
    )


def _rejected_report(context: ScanContext, target: str, message: str) -> Report:
    results = {
        name: ModuleResult[Any](
            status=ModuleStatus.failed,
            reason="rejected",
            duration_ms=0,
            errors=[ModuleError(code="rejected", message=message, url=target)],
        )
        for name in MODULE_NAMES
    }
    report = build_report(context, results, input_url=target)
    report.project_info.scan_status = "rejected"
    return report


async def _bounded(awaitable, seconds: float):
    try:
        return await asyncio.wait_for(awaitable, timeout=seconds)
    except asyncio.TimeoutError as exc:
        raise TimeoutError("module timed out") from exc


def _merge_visual(
    visual: ModuleResult[VisualIdentity],
    screenshot: ModuleResult[Any],
) -> ModuleResult[VisualIdentity]:
    data = visual.data or VisualIdentity()
    if screenshot.data is not None:
        file_ref = getattr(screenshot.data, "file", None)
        if file_ref is not None:
            data.screenshot = file_ref

    warnings = list(dict.fromkeys([*visual.warnings, *screenshot.warnings]))
    errors = [*visual.errors, *screenshot.errors]
    status = visual.status
    if status is ModuleStatus.ok and screenshot.status is ModuleStatus.partial:
        status = ModuleStatus.partial
    elif status is ModuleStatus.ok and screenshot.status is ModuleStatus.failed:
        status = ModuleStatus.partial
        warnings.append("screenshot capture failed; visual identity data was preserved")
    elif status is ModuleStatus.failed and screenshot.status is ModuleStatus.ok:
        status = ModuleStatus.partial

    return ModuleResult[VisualIdentity](
        status=status,
        reason=visual.reason or screenshot.reason,
        duration_ms=visual.duration_ms + screenshot.duration_ms,
        data=data,
        warnings=warnings,
        errors=errors,
    )


class ScanPipeline:
    """Run crawl, content, visual, performance, SEO, and report assembly."""

    def __init__(
        self,
        context: ScanContext,
        *,
        http_client=None,
        crawler=None,
        content_extractor=None,
        visual_extractor=None,
        screenshot_engine=None,
        performance_client=None,
        seo_analyzer=None,
        robots=None,
    ) -> None:
        self.context = context
        self._http_client = http_client
        self._crawler = crawler
        self._content_extractor = content_extractor
        self._visual_extractor = visual_extractor
        self._screenshot_engine = screenshot_engine
        self._performance_client = performance_client
        self._seo_analyzer = seo_analyzer
        self._robots = robots

    async def run(self, url: str | None = None) -> Report:
        target = url or self.context.config.input_url
        try:
            origin = _origin(target)
        except ValueError as exc:
            return _rejected_report(self.context, target, str(exc))
        settings = self.context.settings
        config = self.context.config
        client = self._http_client or SafeHttpClient(
            per_host_rps=config.per_host_rps,
            timeout=config.request_timeout,
            user_agent=settings.crawler_user_agent,
        )
        owns_client = self._http_client is None
        started = time.perf_counter()
        results: dict[str, ModuleResult[Any]] = {}

        try:
            if not config.permission_attested:
                return _rejected_report(
                    self.context,
                    target,
                    "permission attestation is required before scanning",
                )

            robots = self._robots
            if robots is None and settings.crawler_respect_robots:
                robots = await fetch_robots(client, origin, user_agent=settings.crawler_user_agent)
            self._robots = robots
            if robots is not None and not robots.can_fetch(target):
                return _rejected_report(
                    self.context,
                    target,
                    "robots_disallow: the start URL is disallowed by robots.txt",
                )

            crawler = self._crawler or CrawlManager(
                client=client,
                max_pages=config.max_pages,
                max_depth=config.max_depth,
                max_total_seconds=config.max_total_seconds,
                user_agent=settings.crawler_user_agent,
                robots=robots,
                respect_robots=settings.crawler_respect_robots,
            )
            try:
                discovered = await crawler.crawl(target)
                targets = [item for item in discovered if item.status is DiscoveredStatus.fetched]
            except Exception as exc:  # noqa: BLE001 - module boundary
                targets = []
                results["website_content"] = _failed("crawl", exc, url=target)

            if "website_content" not in results:
                extractor = self._content_extractor or ContentExtractor(
                    scan_id=self.context.scan_id,
                    storage_dir=self.context.output_dir,
                )
                try:
                    results["website_content"] = await extractor.extract(targets)
                except Exception as exc:  # noqa: BLE001 - module boundary
                    results["website_content"] = ModuleResult[WebsiteContent](
                        status=ModuleStatus.failed,
                        reason=str(exc),
                        duration_ms=0,
                        data=WebsiteContent(),
                        errors=[ModuleError(code="content_failed", message=str(exc), url=target)],
                    )

            content = results["website_content"]
            pages = content.data.pages if content.data is not None else []
            visual_url = next(
                (page.final_url or page.url for page in pages if page.final_url or page.url),
                target,
            )

            visual_extractor = self._visual_extractor or VisualIdentityExtractor(settings=settings)
            screenshot_engine = self._screenshot_engine or ScreenshotEngine(settings=settings)
            try:
                visual = await _bounded(
                    visual_extractor.extract(visual_url), config.max_total_seconds
                )
            except Exception as exc:  # noqa: BLE001 - module boundary
                visual = _failed("visual", exc, url=visual_url)
            try:
                screenshot = await _bounded(
                    screenshot_engine.capture(
                        visual_url,
                        self.context.scan_id,
                        embed_images=config.embed_images,
                    ),
                    config.max_total_seconds,
                )
            except Exception as exc:  # noqa: BLE001 - module boundary
                screenshot = _failed("screenshot", exc, url=visual_url)
            results["visual_identity"] = _merge_visual(visual, screenshot)

            performance_client = self._performance_client
            owns_performance = performance_client is None
            try:
                if performance_client is None:
                    api_key = (
                        settings.psi_api_key.get_secret_value()
                        if settings.psi_api_key is not None
                        else None
                    )
                    performance_client = PageSpeedClient(api_key=api_key, timeout=config.psi_timeout)
                results["performance"] = await _bounded(
                    performance_client.fetch_performance(target), config.max_total_seconds
                )
            except Exception as exc:  # noqa: BLE001 - module boundary
                results["performance"] = _failed("performance", exc, url=target)
            finally:
                if owns_performance and performance_client is not None:
                    await performance_client.aclose()

            seo = self._seo_analyzer or SeoAnalyzer()
            try:
                results["seo_analysis"] = await _bounded(
                    seo.analyze(
                        pages,
                        robots=robots,
                        client=client,
                        max_broken_links=config.max_broken_link_checks,
                    ),
                    config.max_total_seconds,
                )
            except Exception as exc:  # noqa: BLE001 - module boundary
                results["seo_analysis"] = _failed("seo", exc, url=target)

            self.context.timings["pipeline"] = round(time.perf_counter() - started, 3)
            return build_report(self.context, results, input_url=target)
        finally:
            if owns_client:
                await client.aclose()


async def run_scan(context: ScanContext, url: str | None = None) -> Report:
    """Convenience entry point for one unified scan."""
    return await ScanPipeline(context).run(url)
