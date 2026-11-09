"""Pre-flight Task B: Multi-page controlled crawl verification with English and Arabic content."""

from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from site_dna.core.config import Settings
from site_dna.discovery.crawler import DeterministicCrawler
from site_dna.discovery.http_client import SecureHttpClient


@pytest.mark.anyio
async def test_multipage_controlled_crawl():
    base_dir = Path("tests/fixtures/discovery/multipage")
    home_html = (base_dir / "home.html").read_text(encoding="utf-8")
    about_html = (base_dir / "about.html").read_text(encoding="utf-8")
    services_html = (base_dir / "services.html").read_text(encoding="utf-8")
    products_html = (base_dir / "products.html").read_text(encoding="utf-8")
    contact_html = (base_dir / "contact.html").read_text(encoding="utf-8")

    form_submission_attempted = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal form_submission_attempted
        url_str = str(request.url)

        # Ensure forms are never submitted
        if "contact-submit" in url_str:
            form_submission_attempted = True
            return httpx.Response(500, text="Form submission must never happen!")

        if url_str == "https://acme-global.test/robots.txt":
            robots_txt = "User-agent: *\nAllow: /\nDisallow: /private/\nSitemap: https://acme-global.test/sitemap.xml\n"
            return httpx.Response(200, text=robots_txt, headers={"Content-Type": "text/plain"})

        elif url_str == "https://acme-global.test/sitemap.xml":
            sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                <url><loc>https://acme-global.test/</loc></url>
                <url><loc>https://acme-global.test/about</loc></url>
                <url><loc>https://acme-global.test/services</loc></url>
            </urlset>"""
            return httpx.Response(200, text=sitemap_xml, headers={"Content-Type": "application/xml"})

        elif url_str in ("https://acme-global.test", "https://acme-global.test/"):
            return httpx.Response(200, text=home_html, headers={"Content-Type": "text/html; charset=utf-8"})

        elif url_str == "https://acme-global.test/about":
            return httpx.Response(200, text=about_html, headers={"Content-Type": "text/html; charset=utf-8"})

        elif url_str == "https://acme-global.test/services":
            return httpx.Response(200, text=services_html, headers={"Content-Type": "text/html; charset=utf-8"})

        elif url_str == "https://acme-global.test/products":
            return httpx.Response(200, text=products_html, headers={"Content-Type": "text/html; charset=utf-8"})

        elif url_str == "https://acme-global.test/contact":
            return httpx.Response(200, text=contact_html, headers={"Content-Type": "text/html; charset=utf-8"})

        elif url_str == "https://acme-global.test/old-contact":
            return httpx.Response(301, headers={"Location": "https://acme-global.test/contact"})

        elif url_str == "https://acme-global.test/privacy":
            return httpx.Response(
                200,
                text="<html><head><title>Privacy</title></head><body><h1>Privacy Policy</h1></body></html>",
                headers={"Content-Type": "text/html; charset=utf-8"},
            )

        return httpx.Response(404, text="Not Found")

    mock_transport = httpx.MockTransport(handler)
    custom_client = SecureHttpClient(transport=mock_transport)

    test_settings = Settings(
        crawler_request_delay_seconds=0.0,  # zero delay for immediate test execution
        crawler_max_pages=8,
        crawler_max_depth=2,
    )

    crawler = DeterministicCrawler(
        settings=test_settings,
        max_pages=8,
        max_depth=2,
        client=custom_client,
    )

    with patch(
        "site_dna.discovery.crawler.validate_url_and_resolve",
        return_value=("https://acme-global.test/", ["93.184.215.14"]),
    ):
        result = await crawler.crawl("https://acme-global.test/")

    # 1. Multiple pages discovered & crawled
    assert result.statistics.total_pages_crawled >= 5
    assert result.statistics.total_pages_discovered >= 5

    crawled_urls = [p.final_url for p in result.pages]
    assert "https://acme-global.test/" in crawled_urls
    assert "https://acme-global.test/about" in crawled_urls
    assert "https://acme-global.test/services" in crawled_urls
    assert "https://acme-global.test/products" in crawled_urls
    assert "https://acme-global.test/contact" in crawled_urls

    # 2. Scope restriction: External partner link MUST NOT be crawled
    assert "https://external-partner.org/info" not in crawled_urls

    # 3. Form submission check
    assert form_submission_attempted is False

    # 4. Heading & Title extraction (English & Arabic)
    home_page = next(p for p in result.pages if p.final_url == "https://acme-global.test/")
    assert home_page.metadata.title == "Acme Global — Enterprise Cloud & AI"
    assert any(h.text == "Welcome to Acme Global" and h.level == 1 for h in home_page.headings)
    assert any(h.text == "Accelerating Enterprise Automation" and h.level == 2 for h in home_page.headings)

    about_page = next(p for p in result.pages if p.final_url == "https://acme-global.test/about")
    assert "من نحن" in (about_page.metadata.title or "")
    assert any(h.level == 1 for h in about_page.headings)
    assert any("رؤيتنا" in h.text for h in about_page.headings)

    contact_page = next(p for p in result.pages if p.final_url == "https://acme-global.test/contact")
    assert contact_page.category == "contact"
    assert len(contact_page.forms) == 1
    assert "email_address" in contact_page.forms[0].input_names

    # 5. Serialization integrity
    json_export = result.model_dump_json()
    assert "https://acme-global.test/" in json_export
    assert len(result.evidence) > 10
