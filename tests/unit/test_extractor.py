"""Unit tests for HTML content extractor parsing metadata, headings, text, and elements."""

from pathlib import Path

from site_dna.discovery.extractor import extract_page_content


def test_extract_page_content_english_homepage():
    fixture_path = Path("tests/fixtures/discovery/sample_homepage.html")
    html = fixture_path.read_text(encoding="utf-8")

    content = extract_page_content(html, url="https://example.com/")

    # 1. Metadata
    assert content.metadata.title == "Acme Corporation - Leading AI & Cloud Solutions"
    assert "enterprise cloud infrastructure" in (content.metadata.description or "")
    assert content.metadata.language == "en"
    assert content.metadata.canonical_url == "https://example.com/"
    assert content.metadata.og_title == "Acme Corporation - Cloud AI"
    assert content.metadata.og_image == "https://example.com/images/og-banner.png"

    # 2. Headings hierarchy
    assert len(content.headings) == 3
    assert content.headings[0].level == 1
    assert content.headings[0].text == "Empowering Enterprise Intelligence"
    assert content.headings[1].level == 2
    assert content.headings[1].text == "Our Core Capabilities"
    assert content.headings[2].level == 3
    assert content.headings[2].text == "Enterprise Automation"

    # 3. Main content text & words
    assert "Empowering Enterprise Intelligence" in content.main_content_text
    assert content.word_count > 10

    # 4. Navigation & Internal links
    nav_urls = [link.url for link in content.navigation_links]
    assert "https://example.com/about-us" in nav_urls
    assert "https://example.com/services" in nav_urls
    assert "https://example.com/pricing" in nav_urls
    assert "https://example.com/contact" in nav_urls

    internal_urls = [u for u, _ in content.all_internal_links]
    assert "https://example.com/about-us" in internal_urls
    assert "https://external.org/partner" not in internal_urls  # external link omitted

    # 5. Buttons & CTAs
    assert "Explore Services" in content.buttons
    assert "Request Demo" in content.buttons

    # 6. Images
    assert len(content.images) == 1
    assert content.images[0].src == "https://example.com/images/hero-dashboard.png"
    assert content.images[0].alt == "Analytics Dashboard"
    assert content.images[0].width == 800
    assert content.images[0].height == 600

    # 7. Forms
    assert len(content.forms) == 1
    assert content.forms[0].action == "https://example.com/newsletter-signup"
    assert content.forms[0].method == "POST"
    assert "user_email" in content.forms[0].input_names
    assert content.forms[0].has_submit_button is True

    # 8. JSON-LD
    assert len(content.json_ld) == 1
    assert content.json_ld[0]["@type"] == "Organization"
    assert content.json_ld[0]["name"] == "Acme Corporation"


def test_extract_page_content_arabic_page():
    fixture_path = Path("tests/fixtures/discovery/sample_arabic.html")
    html = fixture_path.read_text(encoding="utf-8")

    content = extract_page_content(html, url="https://asaas.ai/")

    assert content.metadata.language == "ar"
    assert "أساس للذكاء الاصطناعي" in (content.metadata.title or "")
    assert content.headings[0].level == 1
    assert "ريادة الأعمال" in content.headings[0].text
    assert "ابدأ الآن مجاناً" in content.buttons
    assert len(content.forms) == 1
    assert "client_name" in content.forms[0].input_names
    assert "client_email" in content.forms[0].input_names
