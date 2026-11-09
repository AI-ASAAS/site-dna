"""Unit tests for HTTPSAnalyzer and TLSObservationsAnalyzer (Phase 09)."""

from site_dna.analysis.security_privacy.https_analyzer import HTTPSAnalyzer
from site_dna.analysis.security_privacy.tls_observations import TLSObservationsAnalyzer
from site_dna.schemas.security_privacy import SecurityPageRecord
from tests.fixtures.security_privacy.test_fixtures import (
    FIXTURE_A_STRONG_HEADERS,
    FIXTURE_B_MISSING_HEADERS,
)


def test_https_analyzer_enforced_hsts():
    """Verify HTTPS detection and HSTS header parsing."""
    analyzer = HTTPSAnalyzer()
    p1 = SecurityPageRecord(
        page_url="https://secure.example.com/",
        scheme="https",
        status_code=200,
        headers=FIXTURE_A_STRONG_HEADERS,
    )
    res = analyzer.analyze([p1])
    assert res.is_https is True
    assert res.status == "https_observed"
    assert res.hsts_present is True
    assert res.hsts_max_age == 31536000
    assert res.hsts_preload is True
    assert res.hsts_include_subdomains is True


def test_https_analyzer_cleartext_http():
    """Verify unencrypted HTTP detection."""
    analyzer = HTTPSAnalyzer()
    p1 = SecurityPageRecord(
        page_url="http://insecure.example.com/",
        scheme="http",
        status_code=200,
        headers=FIXTURE_B_MISSING_HEADERS,
    )
    res = analyzer.analyze([p1])
    assert res.is_https is False
    assert res.status == "http_only_observed"
    assert res.hsts_present is False


def test_tls_observations_metadata_extraction():
    """Verify safe certificate metadata extraction without active probing."""
    analyzer = TLSObservationsAnalyzer()
    p1 = SecurityPageRecord(
        page_url="https://secure.example.com/",
        scheme="https",
        status_code=200,
    )
    crawl_meta = {
        "ssl_info": {
            "subject": "secure.example.com",
            "issuer": "Let's Encrypt",
            "valid_from": "2026-01-01T00:00:00Z",
            "valid_to": "2026-12-31T00:00:00Z",
            "protocol_version": "TLSv1.3",
        }
    }
    tls = analyzer.analyze("https://secure.example.com", [p1], crawl_meta)
    assert tls.protocol_version == "TLSv1.3"
    assert tls.certificate_issuer == "Let's Encrypt"
    assert tls.is_expired is False
    assert len(tls.evidence_ids) > 0
