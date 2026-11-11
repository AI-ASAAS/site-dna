"""SEO rule identifiers, thresholds, and documented check definitions (Phase 7).

Every check emitted by the analyzer maps to one entry in ``RULES``. The
docstring on each rule is the single source of truth for what the check means
and how its thresholds are interpreted.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class SeoRule:
    """Static definition for a single SEO check."""

    id: str
    scope: str
    docstring: str
    thresholds: dict[str, object]


TITLE_MIN_CHARS = 30
TITLE_MAX_CHARS = 60
META_DESCRIPTION_MIN_CHARS = 70
META_DESCRIPTION_MAX_CHARS = 160
SITEMAP_MAX_BYTES = 10 * 1024 * 1024
SITEMAP_MAX_URLS = 50_000
SITEMAP_MAX_DEPTH = 3
BROKEN_LINK_MAX_CHECKS = 200
BROKEN_LINK_CONCURRENCY = 10


RULES = {
    "title": SeoRule(
        id="title",
        scope="page",
        docstring="Page title must exist and be 30-60 characters; shorter or longer titles warn.",
        thresholds={"min": TITLE_MIN_CHARS, "max": TITLE_MAX_CHARS},
    ),
    "meta_description": SeoRule(
        id="meta_description",
        scope="page",
        docstring="Meta description must exist and be 70-160 characters; outside that range warns.",
        thresholds={"min": META_DESCRIPTION_MIN_CHARS, "max": META_DESCRIPTION_MAX_CHARS},
    ),
    "meta_robots": SeoRule(
        id="meta_robots",
        scope="page",
        docstring="Meta robots or X-Robots-Tag directives are surfaced; noindex/nofollow warn.",
        thresholds={},
    ),
    "canonical": SeoRule(
        id="canonical",
        scope="page",
        docstring="A self-referencing absolute canonical URL is expected; missing or mismatched canonical warns.",
        thresholds={},
    ),
    "open_graph": SeoRule(
        id="open_graph",
        scope="page",
        docstring="Open Graph title, description, and image tags are checked together.",
        thresholds={"required": ["og:title", "og:description", "og:image"]},
    ),
    "headings": SeoRule(
        id="headings",
        scope="page",
        docstring="Exactly one H1 is expected; zero H1 fails and multiple H1s warn.",
        thresholds={"h1": 1},
    ),
    "heading_hierarchy": SeoRule(
        id="heading_hierarchy",
        scope="page",
        docstring="Heading levels must not skip downward (for example H1 directly to H3).",
        thresholds={},
    ),
    "images_alt": SeoRule(
        id="images_alt",
        scope="page",
        docstring="Every content image should have non-empty alt text; any missing alt fails the page.",
        thresholds={},
    ),
    "lang": SeoRule(
        id="lang",
        scope="page",
        docstring="The html element must declare a language.",
        thresholds={},
    ),
    "viewport": SeoRule(
        id="viewport",
        scope="page",
        docstring="A viewport meta tag is required for mobile rendering.",
        thresholds={},
    ),
    "robots_txt": SeoRule(
        id="robots_txt",
        scope="site",
        docstring="robots.txt should be reachable and must not block the scanned origin root.",
        thresholds={},
    ),
    "sitemap": SeoRule(
        id="sitemap",
        scope="site",
        docstring="A sitemap should be declared or discoverable at /sitemap.xml and parse successfully.",
        thresholds={"max_bytes": SITEMAP_MAX_BYTES, "max_urls": SITEMAP_MAX_URLS},
    ),
    "status_codes": SeoRule(
        id="status_codes",
        scope="site",
        docstring="Crawled pages should return 2xx; 4xx/5xx fail and 3xx warn.",
        thresholds={},
    ),
    "links": SeoRule(
        id="links",
        scope="site",
        docstring="Internal and external link totals are reported for the crawled site.",
        thresholds={},
    ),
    "broken_links": SeoRule(
        id="broken_links",
        scope="site",
        docstring="HTTP link targets returning 4xx/5xx or failing at transport are broken.",
        thresholds={"max_checks": BROKEN_LINK_MAX_CHECKS, "concurrency": BROKEN_LINK_CONCURRENCY},
    ),
    "duplicates": SeoRule(
        id="duplicates",
        scope="site",
        docstring="Repeated titles or content hashes across crawled pages warn about duplicate content.",
        thresholds={},
    ),
}
