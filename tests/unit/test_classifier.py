"""Unit tests for heuristic page classification across English and Arabic signals."""

from site_dna.discovery.classifier import classify_page


def test_classify_homepage():
    cat, conf = classify_page("https://example.com/", depth=0, title="Acme Inc")
    assert cat == "home"
    assert conf >= 0.90


def test_classify_about_page_english():
    cat, conf = classify_page(
        "https://example.com/about-us",
        depth=1,
        title="About Our Company",
        h1_text="Who We Are",
        content_snippet="Our mission is to empower teams with our history and values.",
    )
    assert cat == "about"
    assert conf >= 0.70


def test_classify_about_page_arabic():
    cat, conf = classify_page(
        "https://example.com/من-نحن",
        depth=1,
        title="من نحن - شركة أساس",
        h1_text="تعرف على رؤيتنا وقيمنا",
        content_snippet="تأسست الشركة لتقديم حلول الذكاء الاصطناعي ورؤيتنا المستقبلية.",
    )
    assert cat == "about"
    assert conf >= 0.70


def test_classify_contact_page():
    cat, conf = classify_page(
        "https://example.com/contact",
        depth=1,
        title="Contact Us",
        h1_text="Get In Touch",
        content_snippet="Send us an email or phone our support office.",
    )
    assert cat == "contact"
    assert conf >= 0.70


def test_classify_pricing_page():
    cat, conf = classify_page(
        "https://example.com/pricing",
        depth=1,
        title="Subscription Plans & Pricing",
        h1_text="Transparent Pricing for Teams",
        content_snippet="Starting at $29 per month billed annually.",
    )
    assert cat == "pricing"
    assert conf >= 0.70


def test_classify_services_page():
    cat, conf = classify_page(
        "https://example.com/services",
        depth=1,
        title="Our Services and Solutions",
        h1_text="Enterprise Consulting",
        content_snippet="We offer custom software development and cloud consulting.",
    )
    assert cat == "services"
    assert conf >= 0.70
