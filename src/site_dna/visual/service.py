"""Visual evidence collection service orchestrating Playwright rendering, extraction, and storage."""

import asyncio
import time
from typing import Any, Optional
from uuid import uuid4

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.discovery import CrawlResult
from site_dna.schemas.visual import (
    VisualCaptureResult,
    VisualCaptureStatistics,
    VisualPageResult,
)
from site_dna.visual.browser_manager import BrowserManager
from site_dna.visual.browser_security import BrowserSecurityPolicy
from site_dna.visual.color_extractor import ColorExtractor
from site_dna.visual.css_extractor import CSSExtractor
from site_dna.visual.dom_extractor import DOMExtractor
from site_dna.visual.evidence import VisualEvidenceCollector
from site_dna.visual.layout_extractor import LayoutExtractor
from site_dna.visual.renderer import PageRenderer
from site_dna.visual.responsive import ResponsiveAnalyzer
from site_dna.visual.screenshots import ScreenshotCapture
from site_dna.visual.storage import VisualStorageManager, generate_safe_page_id
from site_dna.visual.typography_extractor import TypographyExtractor

logger = get_logger("visual.service")


class VisualCollectionService:
    """Coordinates browser automation, multi-viewport rendering, visual extraction, and artifact storage."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def collect_visual_evidence(
        self,
        crawl_result: CrawlResult,
        max_pages: Optional[int] = None,
        allow_test_loopback: bool = False,
        test_fixture_origin: Optional[str] = None,
    ) -> VisualCaptureResult:
        """Execute visual rendering and evidence collection for eligible crawl pages."""
        start_time = time.perf_counter()
        visual_run_id = f"vis-{uuid4().hex[:12]}"
        crawl_run_id = crawl_result.run_id
        target_origin = crawl_result.website_info.canonical_origin

        storage_manager = VisualStorageManager(
            crawl_run_id=crawl_run_id,
            visual_run_id=visual_run_id,
        )
        evidence_collector = VisualEvidenceCollector(
            crawl_run_id=crawl_run_id,
            visual_run_id=visual_run_id,
        )

        renderer = PageRenderer(settings=self.settings)
        screenshot_capturer = ScreenshotCapture(settings=self.settings)
        dom_extractor = DOMExtractor(settings=self.settings)
        css_extractor = CSSExtractor(settings=self.settings)
        typography_extractor = TypographyExtractor(settings=self.settings)
        layout_extractor = LayoutExtractor(settings=self.settings)

        limit_pages = max_pages or self.settings.visual_max_pages
        eligible_pages = crawl_result.pages[:limit_pages]

        page_results: list[VisualPageResult] = []
        desktop_success_count = 0
        mobile_success_count = 0
        screenshots_saved = 0
        dom_elements_total = 0
        css_records_total = 0

        # Configure network egress security
        security_policy = BrowserSecurityPolicy(
            allowed_origin=target_origin,
            allow_test_loopback=allow_test_loopback,
            test_fixture_origin=test_fixture_origin,
        )

        async with BrowserManager(settings=self.settings) as browser_mgr:
            for index, page_record in enumerate(eligible_pages):
                page_url = page_record.final_url
                safe_id = generate_safe_page_id(page_url, index=index)
                page_dir = storage_manager.get_page_dir(safe_id)
                render_errors: list[str] = []

                logger.info("Starting visual capture for [%d/%d]: %s", index + 1, len(eligible_pages), page_url)

                desktop_screenshots = []
                mobile_screenshots = []
                dom_elements = []
                computed_styles = []
                typography_records = []
                layout_records = []
                responsive_observations = []

                desktop_metrics: dict[str, int] = {}
                mobile_metrics: dict[str, int] = {}

                # 1. Desktop Capture
                desktop_ctx = await browser_mgr.create_context("desktop", security_policy)
                try:
                    d_render = await renderer.render_page(page_url, desktop_ctx)
                    if d_render.success and d_render.page:
                        desktop_success_count += 1
                        d_page = d_render.page

                        # Screenshots
                        d_shots = await screenshot_capturer.capture_screenshots(d_page, page_dir, "desktop")
                        desktop_screenshots.extend(d_shots)
                        screenshots_saved += sum(1 for s in d_shots if s.success)

                        for s in d_shots:
                            if s.success:
                                evidence_collector.add(
                                    page_url=page_url,
                                    viewport_profile="desktop",
                                    evidence_category="screenshot",
                                    field_reference=f"visual.screenshot.desktop_{s.screenshot_type}",
                                    observed_value={
                                        "path": s.relative_path,
                                        "sha256": s.sha256,
                                        "size": s.file_size_bytes,
                                    },
                                    screenshot_reference=s.relative_path,
                                )

                        # Metrics & Extraction
                        desktop_metrics = await ResponsiveAnalyzer.measure_viewport_metrics(d_page)
                        dom_elements = await dom_extractor.extract_dom_elements(d_page)
                        dom_elements_total += len(dom_elements)

                        computed_styles = await css_extractor.extract_computed_styles(d_page, "desktop")
                        css_records_total += len(computed_styles)

                        typography_records = await typography_extractor.extract_typography(d_page, "desktop")
                        layout_records = await layout_extractor.extract_layout(d_page)

                        await d_page.close()
                    else:
                        render_errors.append(f"Desktop render error: {d_render.error}")
                except Exception as exc:
                    render_errors.append(f"Desktop capture exception: {exc}")
                finally:
                    await browser_mgr.close_context(desktop_ctx)

                # 2. Mobile Capture
                mobile_ctx = await browser_mgr.create_context("mobile", security_policy)
                try:
                    m_render = await renderer.render_page(page_url, mobile_ctx)
                    if m_render.success and m_render.page:
                        mobile_success_count += 1
                        m_page = m_render.page

                        # Screenshots
                        m_shots = await screenshot_capturer.capture_screenshots(m_page, page_dir, "mobile")
                        mobile_screenshots.extend(m_shots)
                        screenshots_saved += sum(1 for s in m_shots if s.success)

                        for s in m_shots:
                            if s.success:
                                evidence_collector.add(
                                    page_url=page_url,
                                    viewport_profile="mobile",
                                    evidence_category="screenshot",
                                    field_reference=f"visual.screenshot.mobile_{s.screenshot_type}",
                                    observed_value={
                                        "path": s.relative_path,
                                        "sha256": s.sha256,
                                        "size": s.file_size_bytes,
                                    },
                                    screenshot_reference=s.relative_path,
                                )

                        # Metrics & Responsive Comparison
                        mobile_metrics = await ResponsiveAnalyzer.measure_viewport_metrics(m_page)
                        if desktop_metrics and mobile_metrics:
                            responsive_observations = ResponsiveAnalyzer.compare_viewports(
                                desktop_metrics, mobile_metrics
                            )
                            for obs in responsive_observations:
                                evidence_collector.add(
                                    page_url=page_url,
                                    viewport_profile="responsive",
                                    evidence_category="responsive_measurement",
                                    field_reference=f"visual.responsive.{obs.observation_type}",
                                    observed_value=obs.model_dump(),
                                )

                        await m_page.close()
                    else:
                        render_errors.append(f"Mobile render error: {m_render.error}")
                except Exception as exc:
                    render_errors.append(f"Mobile capture exception: {exc}")
                finally:
                    await browser_mgr.close_context(mobile_ctx)

                # 3. Aggregate Color Palette from computed styles
                colors = ColorExtractor.extract_palette(computed_styles)
                for color in colors[:8]:
                    evidence_collector.add(
                        page_url=page_url,
                        viewport_profile="desktop",
                        evidence_category="color_observation",
                        field_reference="visual.color.observed",
                        observed_value=color.model_dump(),
                    )

                # Determine per-page status
                if desktop_screenshots and mobile_screenshots:
                    page_status = "completed"
                elif desktop_screenshots or mobile_screenshots:
                    page_status = "partial"
                else:
                    page_status = "failed"

                page_res = VisualPageResult(
                    page_url=page_url,
                    safe_page_id=safe_id,
                    status=page_status,
                    desktop_screenshots=desktop_screenshots,
                    mobile_screenshots=mobile_screenshots,
                    dom_elements=dom_elements,
                    computed_styles=computed_styles,
                    colors=colors,
                    typography=typography_records,
                    layout_records=layout_records,
                    responsive_observations=responsive_observations,
                    evidence_records=evidence_collector.get_for_page(page_url),
                    render_errors=render_errors,
                )
                page_results.append(page_res)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Overall Run Status
        if all(p.status == "completed" for p in page_results) and page_results:
            overall_status = "completed"
        elif any(p.status in ("completed", "partial") for p in page_results):
            overall_status = "partial"
        else:
            overall_status = "failed"

        stats = VisualCaptureStatistics(
            total_pages_attempted=len(eligible_pages),
            desktop_captures_completed=desktop_success_count,
            mobile_captures_completed=mobile_success_count,
            screenshots_saved=screenshots_saved,
            dom_elements_extracted=dom_elements_total,
            css_records_extracted=css_records_total,
            evidence_records_created=evidence_collector.count(),
            total_duration_ms=round(duration_ms, 2),
            errors_count=sum(len(p.render_errors) for p in page_results),
        )

        final_result = VisualCaptureResult(
            crawl_run_id=crawl_run_id,
            visual_run_id=visual_run_id,
            status=overall_status,
            target_origin=target_origin,
            pages=page_results,
            statistics=stats,
        )

        # Save artifacts: visual.json and manifest.json
        storage_manager.save_visual_result(final_result)
        manifest_p = storage_manager.save_manifest(final_result)
        final_result.manifest_path = str(manifest_p)

        logger.info(
            "Visual collection finished [%s]: %d pages, %d screenshots in %.1f ms",
            overall_status,
            len(page_results),
            screenshots_saved,
            duration_ms,
        )
        return final_result

    async def collect_evidence(
        self,
        crawl_result: CrawlResult,
        max_pages: Optional[int] = None,
        run_id: Optional[str] = None,
        **kwargs: Any,
    ) -> VisualCaptureResult:
        """Alias for collect_visual_evidence supporting coordinator calls."""
        return await self.collect_visual_evidence(crawl_result, max_pages=max_pages)

    def collect_visual_evidence_sync(
        self,
        crawl_result: CrawlResult,
        max_pages: Optional[int] = None,
        allow_test_loopback: bool = False,
        test_fixture_origin: Optional[str] = None,
    ) -> VisualCaptureResult:
        """Synchronous wrapper for VisualCollectionService."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(
                    lambda: asyncio.run(
                        self.collect_visual_evidence(
                            crawl_result=crawl_result,
                            max_pages=max_pages,
                            allow_test_loopback=allow_test_loopback,
                            test_fixture_origin=test_fixture_origin,
                        )
                    )
                )
                return future.result()
        else:
            return asyncio.run(
                self.collect_visual_evidence(
                    crawl_result=crawl_result,
                    max_pages=max_pages,
                    allow_test_loopback=allow_test_loopback,
                    test_fixture_origin=test_fixture_origin,
                )
            )
