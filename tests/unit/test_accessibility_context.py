"""Unit tests for Accessibility Context Builder and Sampling Heuristics."""

import pytest

from site_dna.analysis.accessibility.context_builder import (
    validate_crawl_run_id,
)
from site_dna.analysis.accessibility.sampling import AccessibilitySampler
from site_dna.schemas.accessibility import AccessibilityPageRecord


def test_validate_crawl_run_id_safe():
    assert validate_crawl_run_id("crawl-a") == "crawl-a"
    assert validate_crawl_run_id("run-1234_abc") == "run-1234_abc"
    assert validate_crawl_run_id("98b5cd6a-3225-4c00-9b75-0d13061d85f1") == "98b5cd6a-3225-4c00-9b75-0d13061d85f1"


def test_validate_crawl_run_id_rejects_path_traversal():
    with pytest.raises(ValueError, match="Invalid characters"):
        validate_crawl_run_id("../etc/passwd")

    with pytest.raises(ValueError, match="Invalid characters"):
        validate_crawl_run_id("..\\windows\\system32")

    with pytest.raises(ValueError, match="Invalid characters"):
        validate_crawl_run_id("run/123")


def test_validate_crawl_run_id_rejects_empty():
    with pytest.raises(ValueError, match="non-empty"):
        validate_crawl_run_id("")


def test_accessibility_sampler_diverse_selection():
    sampler = AccessibilitySampler(max_pages=3)

    pages = [
        AccessibilityPageRecord(
            page_url="https://example.com/", page_title="الرئيسية", interactive_elements_count=5, form_controls_count=0
        ),
        AccessibilityPageRecord(
            page_url="https://example.com/about",
            page_title="عن الموقع",
            interactive_elements_count=2,
            form_controls_count=0,
        ),
        AccessibilityPageRecord(
            page_url="https://example.com/contact",
            page_title="اتصل بنا",
            interactive_elements_count=8,
            form_controls_count=6,
        ),
        AccessibilityPageRecord(
            page_url="https://example.com/products",
            page_title="المنتجات",
            interactive_elements_count=35,
            form_controls_count=1,
        ),
        AccessibilityPageRecord(
            page_url="https://example.com/login", page_title="دخول", interactive_elements_count=6, form_controls_count=3
        ),
    ]

    sampling_record = sampler.sample_pages(pages, total_discovered=5)
    assert sampling_record.total_pages_discovered == 5
    assert sampling_record.sampled_pages_count <= 3
    urls = [p.page_url for p in sampling_record.sampled_pages]
    # Homepage and high form count page should be prioritized
    assert "https://example.com/" in urls
    assert "https://example.com/contact" in urls
    assert sampling_record.sampling_limitations_ar != ""
