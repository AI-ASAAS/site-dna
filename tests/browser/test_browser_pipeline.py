"""Integration tests for Playwright browser rendering and visual evidence extraction pipeline."""

import functools
import hashlib
import http.server
import threading
from pathlib import Path

import pytest
from PIL import Image

from site_dna.core.config import Settings
from site_dna.flows.visual_evidence_flow import VisualEvidenceFlow
from site_dna.schemas.discovery import CrawlResult, PageData, WebsiteInfo
from site_dna.visual.browser_manager import BrowserManager
from site_dna.visual.browser_security import BrowserSecurityPolicy
from site_dna.visual.css_extractor import CSSExtractor
from site_dna.visual.dom_extractor import DOMExtractor
from site_dna.visual.evidence import VisualEvidenceCollector
from site_dna.visual.layout_extractor import LayoutExtractor
from site_dna.visual.renderer import PageRenderer
from site_dna.visual.responsive import ResponsiveAnalyzer
from site_dna.visual.screenshots import ScreenshotCapture
from site_dna.visual.service import VisualCollectionService
from site_dna.visual.typography_extractor import TypographyExtractor


@pytest.fixture(scope="module")
def fixture_server():
    """Start local threaded HTTP server serving visual fixtures."""
    site_dir = Path(__file__).parent.parent / "fixtures" / "visual" / "site"
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(site_dir))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{port}"
    yield origin
    server.shutdown()


@pytest.mark.asyncio
async def test_browser_manager_context_profiles(fixture_server: str):
    """Test desktop and mobile browser contexts initialization and viewport parameters."""
    policy = BrowserSecurityPolicy(
        allowed_origin=fixture_server,
        allow_test_loopback=True,
        test_fixture_origin=fixture_server,
    )

    async with BrowserManager() as mgr:
        # Desktop
        desktop_ctx = await mgr.create_context("desktop", policy)
        d_page = await desktop_ctx.new_page()
        d_vp = d_page.viewport_size
        assert d_vp is not None
        assert d_vp["width"] == 1440
        assert d_vp["height"] == 900
        await desktop_ctx.close()

        # Mobile
        mobile_ctx = await mgr.create_context("mobile", policy)
        m_page = await mobile_ctx.new_page()
        m_vp = m_page.viewport_size
        assert m_vp is not None
        assert m_vp["width"] == 390
        assert m_vp["height"] == 844
        await mobile_ctx.close()


@pytest.mark.asyncio
async def test_page_renderer_and_screenshots(fixture_server: str, tmp_path: Path):
    """Test rendering and capturing real viewport and full-page screenshots with dimensions and hashes."""
    policy = BrowserSecurityPolicy(
        allowed_origin=fixture_server,
        allow_test_loopback=True,
        test_fixture_origin=fixture_server,
    )
    renderer = PageRenderer()
    capturer = ScreenshotCapture()

    async with BrowserManager() as mgr:
        ctx = await mgr.create_context("desktop", policy)
        render_res = await renderer.render_page(f"{fixture_server}/index.html", ctx)
        assert render_res.success
        assert render_res.status_code == 200
        assert render_res.page is not None

        page = render_res.page
        output_dir = tmp_path / "screenshots"
        records = await capturer.capture_screenshots(page, output_dir, "desktop")

        assert len(records) == 2
        vp_rec = next(r for r in records if r.screenshot_type == "viewport")
        fp_rec = next(r for r in records if r.screenshot_type == "full_page")

        # Verify viewport screenshot
        assert vp_rec.success
        assert Path(vp_rec.file_path).exists()
        assert vp_rec.file_size_bytes > 0
        assert vp_rec.width_px == 1440
        assert vp_rec.height_px == 900
        # Verify SHA-256
        actual_sha = hashlib.sha256(Path(vp_rec.file_path).read_bytes()).hexdigest()
        assert vp_rec.sha256 == actual_sha

        # Verify full-page screenshot
        assert fp_rec.success
        assert Path(fp_rec.file_path).exists()
        assert fp_rec.file_size_bytes > 0
        assert fp_rec.width_px == 1440
        assert fp_rec.height_px >= 900  # full page covers entire document scroll height

        with Image.open(fp_rec.file_path) as img:
            assert img.size == (fp_rec.width_px, fp_rec.height_px)

        await page.close()
        await ctx.close()


@pytest.mark.asyncio
async def test_dom_and_css_extraction(fixture_server: str):
    """Test extracting bounded semantic DOM nodes and computed CSS styles."""
    policy = BrowserSecurityPolicy(
        allowed_origin=fixture_server,
        allow_test_loopback=True,
        test_fixture_origin=fixture_server,
    )
    renderer = PageRenderer()
    dom_extractor = DOMExtractor()
    css_extractor = CSSExtractor()

    async with BrowserManager() as mgr:
        ctx = await mgr.create_context("desktop", policy)
        render_res = await renderer.render_page(f"{fixture_server}/index.html", ctx)
        assert render_res.page is not None
        page = render_res.page

        # DOM extraction
        dom_records = await dom_extractor.extract_dom_elements(page)
        assert len(dom_records) > 0
        tag_names = {r.tag_name for r in dom_records}
        assert "header" in tag_names
        assert "nav" in tag_names
        assert "h1" in tag_names
        assert "button" in tag_names
        assert "footer" in tag_names

        # Security check: no input values or secrets
        for r in dom_records:
            assert "password" not in r.attributes
            assert "value" not in r.attributes

        # CSS extraction
        styles = await css_extractor.extract_computed_styles(page, "desktop")
        assert len(styles) > 0
        h1_style = next((s for s in styles if s.tag_name == "h1"), None)
        assert h1_style is not None
        assert h1_style.color is not None
        assert h1_style.font_size is not None

        await page.close()
        await ctx.close()


@pytest.mark.asyncio
async def test_typography_and_rtl_extraction(fixture_server: str):
    """Test typography metrics extraction and RTL direction support on Arabic page."""
    policy = BrowserSecurityPolicy(
        allowed_origin=fixture_server,
        allow_test_loopback=True,
        test_fixture_origin=fixture_server,
    )
    renderer = PageRenderer()
    typo_extractor = TypographyExtractor()

    async with BrowserManager() as mgr:
        ctx = await mgr.create_context("desktop", policy)
        render_res = await renderer.render_page(f"{fixture_server}/about.html", ctx)
        assert render_res.page is not None
        page = render_res.page

        typo_records = await typo_extractor.extract_typography(page, "desktop")
        assert len(typo_records) > 0

        # Verify RTL direction detected
        rtl_records = [r for r in typo_records if r.direction == "rtl"]
        assert len(rtl_records) > 0

        # Verify Arabic language detected
        ar_records = [r for r in typo_records if r.language == "ar"]
        assert len(ar_records) > 0

        await page.close()
        await ctx.close()


@pytest.mark.asyncio
async def test_layout_extraction(fixture_server: str):
    """Test structural section bounding boxes and flex/grid layout properties."""
    policy = BrowserSecurityPolicy(
        allowed_origin=fixture_server,
        allow_test_loopback=True,
        test_fixture_origin=fixture_server,
    )
    renderer = PageRenderer()
    layout_extractor = LayoutExtractor()

    async with BrowserManager() as mgr:
        ctx = await mgr.create_context("desktop", policy)
        render_res = await renderer.render_page(f"{fixture_server}/index.html", ctx)
        assert render_res.page is not None
        page = render_res.page

        layouts = await layout_extractor.extract_layout(page)
        assert len(layouts) >= 3  # header, nav, hero, footer
        section_types = {sec.section_type for sec in layouts}
        assert "header" in section_types
        assert "nav" in section_types
        assert "hero_candidate" in section_types
        assert "footer" in section_types

        for item in layouts:
            assert item.bounding_box["width"] > 0
            assert item.bounding_box["height"] > 0

        await page.close()
        await ctx.close()


@pytest.mark.asyncio
async def test_responsive_horizontal_overflow_detection(fixture_server: str):
    """Test that mobile viewport detects horizontal overflow caused by min-width 420px container."""
    policy = BrowserSecurityPolicy(
        allowed_origin=fixture_server,
        allow_test_loopback=True,
        test_fixture_origin=fixture_server,
    )
    renderer = PageRenderer()

    async with BrowserManager() as mgr:
        desktop_ctx = await mgr.create_context("desktop", policy)
        d_render = await renderer.render_page(f"{fixture_server}/index.html", desktop_ctx)
        assert d_render.page is not None
        desktop_metrics = await ResponsiveAnalyzer.measure_viewport_metrics(d_render.page)
        await desktop_ctx.close()

        mobile_ctx = await mgr.create_context("mobile", policy)
        m_render = await renderer.render_page(f"{fixture_server}/index.html", mobile_ctx)
        assert m_render.page is not None
        mobile_metrics = await ResponsiveAnalyzer.measure_viewport_metrics(m_render.page)
        await mobile_ctx.close()

        observations = ResponsiveAnalyzer.compare_viewports(desktop_metrics, mobile_metrics)
        assert len(observations) > 0

        overflow_obs = next((o for o in observations if o.observation_type == "horizontal_overflow"), None)
        assert overflow_obs is not None
        assert overflow_obs.status == "observed"
        # Mobile scrollWidth (>=420) exceeds mobile viewport width (390)
        assert overflow_obs.mobile_value["scroll_width"] >= 420


def test_visual_evidence_collector():
    """Test atomic visual evidence recording and querying."""
    collector = VisualEvidenceCollector(crawl_run_id="c-1", visual_run_id="v-1")
    collector.add(
        page_url="http://127.0.0.1/index.html",
        viewport_profile="desktop",
        evidence_category="screenshot",
        field_reference="visual.screenshot.desktop_viewport",
        observed_value={"path": "desktop-viewport.png"},
    )
    collector.add(
        page_url="http://127.0.0.1/about.html",
        viewport_profile="desktop",
        evidence_category="color_observation",
        field_reference="visual.color.primary",
        observed_value={"hex": "#4F46E5"},
    )

    assert collector.count() == 2
    assert len(collector.get_for_page("http://127.0.0.1/index.html")) == 1
    assert len(collector.get_for_page("http://127.0.0.1/about.html")) == 1
    assert len(collector.get_for_page("http://127.0.0.1/nonexistent")) == 0


@pytest.mark.asyncio
async def test_visual_collection_service_end_to_end(fixture_server: str, tmp_path: Path):
    """Test full VisualCollectionService execution on CrawlResult producing visual.json and manifest."""
    custom_settings = Settings(
        app_env="test",
        visual_capture_enabled=True,
        visual_max_pages=2,
    )
    service = VisualCollectionService(settings=custom_settings)

    crawl_result = CrawlResult(
        run_id="test-run-vis-001",
        status="completed",
        website_info=WebsiteInfo(
            initial_url=f"{fixture_server}/",
            canonical_origin=fixture_server,
        ),
        pages=[
            PageData(
                url=f"{fixture_server}/index.html",
                final_url=f"{fixture_server}/index.html",
                status_code=200,
                depth=0,
            ),
            PageData(
                url=f"{fixture_server}/about.html",
                final_url=f"{fixture_server}/about.html",
                status_code=200,
                depth=1,
            ),
        ],
    )

    result = await service.collect_visual_evidence(
        crawl_result=crawl_result,
        max_pages=2,
        allow_test_loopback=True,
        test_fixture_origin=fixture_server,
    )

    assert result.status == "completed"
    assert len(result.pages) == 2
    assert result.statistics.desktop_captures_completed == 2
    assert result.statistics.mobile_captures_completed == 2
    assert result.statistics.screenshots_saved == 8  # 2 viewports * 2 screenshot types * 2 pages

    # Verify manifest path exists on disk
    assert result.manifest_path is not None
    manifest_p = Path(result.manifest_path)
    assert manifest_p.exists()

    visual_json_p = manifest_p.parent / "visual.json"
    assert visual_json_p.exists()

    # Check that pages directory has screenshots
    pages_dir = manifest_p.parent / "pages"
    assert pages_dir.exists()
    page_subdirs = list(pages_dir.iterdir())
    assert len(page_subdirs) == 2
    for p_dir in page_subdirs:
        pngs = list(p_dir.glob("*.png"))
        assert len(pngs) == 4  # desktop vp, desktop fp, mobile vp, mobile fp


def test_visual_evidence_tool_and_flow(fixture_server: str, tmp_path: Path):
    """Test CrewAI VisualEvidenceTool and VisualEvidenceFlow synchronous execution."""
    custom_settings = Settings(
        app_env="test",
        visual_capture_enabled=True,
        visual_max_pages=1,
    )

    crawl_result = CrawlResult(
        run_id="flow-test-crawl-01",
        status="completed",
        website_info=WebsiteInfo(
            initial_url=f"{fixture_server}/",
            canonical_origin=fixture_server,
        ),
        pages=[
            PageData(
                url=f"{fixture_server}/index.html",
                final_url=f"{fixture_server}/index.html",
                status_code=200,
                depth=0,
            )
        ],
    )

    # Save mock crawl.json
    crawl_file = tmp_path / "crawl.json"
    crawl_file.write_text(crawl_result.model_dump_json(indent=2), encoding="utf-8")

    # Flow test
    flow = VisualEvidenceFlow(
        crawl_result=crawl_result,
        max_pages=1,
        allow_test_loopback=True,
        test_fixture_origin=fixture_server,
        settings=custom_settings,
    )
    state = flow.kickoff()
    assert state.execution_status == "completed"
    assert state.visual_result is not None
    assert state.visual_result.status == "completed"
    assert state.visual_result.statistics.screenshots_saved == 4
