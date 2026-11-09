"""Unit tests for URL normalization, validation, and origin checking."""

import pytest

from site_dna.core.security import SecurityValidationError
from site_dna.discovery.url_validator import (
    extract_canonical_origin,
    is_same_origin,
    normalize_url,
)


def test_normalize_url_adds_https_scheme_by_default():
    url = "example.com/about"
    normalized = normalize_url(url)
    assert normalized == "https://example.com/about"


def test_normalize_url_strips_fragments():
    url = "https://example.com/page#section2"
    normalized = normalize_url(url)
    assert normalized == "https://example.com/page"
    assert "#" not in normalized


def test_normalize_url_removes_tracking_query_params():
    url = "https://example.com/products?utm_source=twitter&utm_medium=cpc&id=42&fbclid=xyz"
    normalized = normalize_url(url)
    assert "utm_source" not in normalized
    assert "fbclid" not in normalized
    assert "id=42" in normalized


def test_normalize_url_ensures_root_path():
    url = "https://example.com"
    normalized = normalize_url(url)
    assert normalized == "https://example.com/"


def test_normalize_url_rejects_credentials():
    with pytest.raises(SecurityValidationError, match="credentials"):
        normalize_url("https://user:pass@example.com/dashboard")


def test_normalize_url_rejects_invalid_schemes():
    with pytest.raises(SecurityValidationError, match="scheme"):
        normalize_url("ftp://example.com/file.txt")

    with pytest.raises(SecurityValidationError, match="scheme"):
        normalize_url("file:///etc/passwd")


def test_normalize_url_rejects_disallowed_ports():
    with pytest.raises(SecurityValidationError, match="Port"):
        normalize_url("https://example.com:8443/page")

    with pytest.raises(SecurityValidationError, match="Port"):
        normalize_url("http://example.com:22/")


def test_extract_canonical_origin():
    assert extract_canonical_origin("https://example.com:443/path/to/page") == "https://example.com"
    assert extract_canonical_origin("http://example.com/page?x=1") == "http://example.com"


def test_is_same_origin():
    assert is_same_origin("https://example.com/page1", "https://example.com/page2") is True
    assert is_same_origin("https://example.com/", "http://example.com/") is False
    assert is_same_origin("https://example.com/", "https://sub.example.com/") is False
    assert is_same_origin("https://example.com/", "https://other.org/") is False
