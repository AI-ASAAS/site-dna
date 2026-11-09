"""Automated Browser QA and Screenshot Collection for Site DNA Phase 07.5 Frontend."""

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

SCREENSHOTS_DIR = Path("docs/screenshots")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


async def run_frontend_qa():
    print("Launching Chromium browser via Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # 1. Desktop Test (1280x850)
        context_desktop = await browser.new_context(
            viewport={"width": 1280, "height": 850},
            locale="ar-SA",
        )
        page = await context_desktop.new_page()

        print("Testing Desktop Dashboard at http://127.0.0.1:8000/ ...")
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "desktop_dashboard.png"), full_page=True)
        print("Captured desktop_dashboard.png")

        # 2. Desktop New Analysis Page
        print("Testing New Analysis Page at http://127.0.0.1:8000/analyses/new ...")
        await page.goto("http://127.0.0.1:8000/analyses/new", wait_until="networkidle")
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "desktop_new_analysis.png"), full_page=True)
        print("Captured desktop_new_analysis.png")

        # 3. Agents Directory Page (Phases 01-12)
        print("Testing Agents Directory at http://127.0.0.1:8000/agents ...")
        await page.goto("http://127.0.0.1:8000/agents", wait_until="networkidle")
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "desktop_agents.png"), full_page=True)
        print("Captured desktop_agents.png")

        # 4. Existing Run Monitor Page (using 98b5cd6a-3225-4c00-9b75-0d13061d85f1)
        print("Testing Analysis Monitor at http://127.0.0.1:8000/analyses/98b5cd6a-3225-4c00-9b75-0d13061d85f1 ...")
        await page.goto("http://127.0.0.1:8000/analyses/98b5cd6a-3225-4c00-9b75-0d13061d85f1", wait_until="networkidle")
        await page.wait_for_timeout(800)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "desktop_monitor.png"), full_page=True)
        print("Captured desktop_monitor.png")

        # 5. Settings & Theme Toggle
        print("Testing Settings at http://127.0.0.1:8000/settings ...")
        await page.goto("http://127.0.0.1:8000/settings", wait_until="networkidle")
        await page.wait_for_timeout(500)
        await page.screenshot(path=str(SCREENSHOTS_DIR / "desktop_settings.png"), full_page=True)
        print("Captured desktop_settings.png")

        # Test Dark Theme Toggle
        theme_btn = await page.query_selector("button[title='Toggle Theme']")
        if theme_btn:
            await theme_btn.click()
            await page.wait_for_timeout(300)
            await page.screenshot(path=str(SCREENSHOTS_DIR / "dark_theme.png"), full_page=True)
            print("Captured dark_theme.png")

        # 6. Mobile Test (375x812 - iPhone X / Standard Mobile)
        print("Testing Mobile Responsiveness at 375px...")
        context_mobile = await browser.new_context(
            viewport={"width": 375, "height": 812},
            is_mobile=True,
            has_touch=True,
            locale="ar-SA",
        )
        page_mobile = await context_mobile.new_page()
        await page_mobile.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        await page_mobile.wait_for_timeout(500)

        # Check horizontal scroll width rule: document.documentElement.scrollWidth == window.innerWidth
        scroll_width = await page_mobile.evaluate("document.documentElement.scrollWidth")
        inner_width = await page_mobile.evaluate("window.innerWidth")
        print(f"Mobile Width Check: scrollWidth={scroll_width}, innerWidth={inner_width}")
        assert scroll_width <= inner_width + 1, f"Horizontal overflow detected! {scroll_width} > {inner_width}"

        await page_mobile.screenshot(path=str(SCREENSHOTS_DIR / "mobile_dashboard.png"), full_page=True)
        print("Captured mobile_dashboard.png (Zero horizontal overflow verified!)")

        # Mobile New Analysis
        await page_mobile.goto("http://127.0.0.1:8000/analyses/new", wait_until="networkidle")
        await page_mobile.wait_for_timeout(500)
        scroll_width_new = await page_mobile.evaluate("document.documentElement.scrollWidth")
        inner_width_new = await page_mobile.evaluate("window.innerWidth")
        print(f"Mobile New Analysis Width Check: scrollWidth={scroll_width_new}, innerWidth={inner_width_new}")
        assert scroll_width_new <= inner_width_new + 1, "Horizontal overflow on New Analysis page!"
        await page_mobile.screenshot(path=str(SCREENSHOTS_DIR / "mobile_new_analysis.png"), full_page=True)
        print("Captured mobile_new_analysis.png")

        await browser.close()
        print("QA & Screenshot Capture successfully completed!")


if __name__ == "__main__":
    asyncio.run(run_frontend_qa())
