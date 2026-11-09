"""Discovery subsystem for Site DNA: secure crawling, parsing, and evidence collection."""

from site_dna.discovery.classifier import classify_page
from site_dna.discovery.crawler import DeterministicCrawler
from site_dna.discovery.evidence import EvidenceCollector
from site_dna.discovery.extractor import extract_page_content
from site_dna.discovery.frontier import IntelligentFrontier
from site_dna.discovery.http_client import (
    FetchError,
    HttpResponseData,
    InvalidContentTypeError,
    ResponseTooLargeError,
    SecureHttpClient,
)
from site_dna.discovery.robots_policy import RobotsPolicy
from site_dna.discovery.service import WebsiteDiscoveryService
from site_dna.discovery.sitemap import SitemapResult, discover_sitemaps
from site_dna.discovery.url_validator import (
    extract_canonical_origin,
    is_same_origin,
    normalize_url,
    validate_url_and_resolve,
)

__all__ = [
    "DeterministicCrawler",
    "EvidenceCollector",
    "IntelligentFrontier",
    "SecureHttpClient",
    "HttpResponseData",
    "FetchError",
    "ResponseTooLargeError",
    "InvalidContentTypeError",
    "RobotsPolicy",
    "SitemapResult",
    "discover_sitemaps",
    "extract_page_content",
    "classify_page",
    "WebsiteDiscoveryService",
    "normalize_url",
    "extract_canonical_origin",
    "is_same_origin",
    "validate_url_and_resolve",
]
