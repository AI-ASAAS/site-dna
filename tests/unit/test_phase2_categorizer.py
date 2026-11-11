"""Phase 2 unit tests for the table-driven page categorizer."""

import pytest

from site_dna.crawler.categorizer import categorize_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://example.com/", "home"),
        ("https://example.com", "home"),
        ("https://example.com/blog/post-1", "blog"),
        ("https://example.com/news/2026", "blog"),
        ("https://example.com/products/widget", "product"),
        ("https://example.com/shop/widget", "product"),
        ("https://example.com/category/electronics", "category"),
        ("https://example.com/collections/sale", "category"),
        ("https://example.com/contact", "contact"),
        ("https://example.com/contact-us", "contact"),
        ("https://example.com/about-us", "about"),
        ("https://example.com/company", "about"),
        ("https://example.com/pricing", "pricing"),
        ("https://example.com/plans", "pricing"),
        ("https://example.com/terms", "legal"),
        ("https://example.com/privacy-policy", "legal"),
        ("https://example.com/login", "auth"),
        ("https://example.com/signup", "auth"),
        ("https://example.com/docs/getting-started", "docs"),
        ("https://example.com/faq", "docs"),
        ("https://example.com/team", "other"),
    ],
)
def test_categorize_url_table(url, expected):
    assert categorize_url(url, depth=1) == expected


def test_categorize_depth_zero_is_home():
    assert categorize_url("https://example.com/contact", depth=0) == "home"


def test_categorize_uses_title_when_path_is_uninformative():
    assert categorize_url("https://example.com/x1", depth=1, title="Contact Us") == "contact"
    assert categorize_url("https://example.com/x2", depth=1, title="Pricing Plans") == "pricing"
