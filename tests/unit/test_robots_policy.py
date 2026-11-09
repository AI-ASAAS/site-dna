"""Unit tests for RFC 9309 robots.txt compliance and matching logic."""

from site_dna.discovery.robots_policy import RobotsPolicy


def test_robots_policy_allows_all_by_default_when_not_present():
    policy = RobotsPolicy(origin="https://example.com", is_present=False)
    assert policy.is_allowed("https://example.com/admin") is True
    assert policy.is_allowed("https://example.com/") is True


def test_robots_policy_fail_closed_on_server_error():
    policy = RobotsPolicy(origin="https://example.com", is_present=False, fail_closed=True)
    assert policy.is_allowed("https://example.com/") is False
    assert policy.is_allowed("https://example.com/about") is False


def test_robots_policy_rfc9309_longest_match_and_allow_precedence():
    sample = """
User-agent: *
Disallow: /admin/
Allow: /admin/public
Disallow: /private/
Crawl-delay: 2.5
Sitemap: https://example.com/sitemap.xml
"""
    policy = RobotsPolicy.parse(sample, origin="https://example.com")

    # /admin/ is disallowed
    assert policy.is_allowed("https://example.com/admin/secret") is False
    assert policy.is_allowed("https://example.com/admin/") is False

    # /admin/public has a longer match than /admin/, and is an Allow rule -> allowed!
    assert policy.is_allowed("https://example.com/admin/public") is True
    assert policy.is_allowed("https://example.com/admin/public/profile") is True

    # Root and about are allowed
    assert policy.is_allowed("https://example.com/") is True
    assert policy.is_allowed("https://example.com/about") is True

    # Crawl delay & sitemap extraction
    assert policy.get_crawl_delay() == 2.5
    assert policy.sitemaps == ["https://example.com/sitemap.xml"]


def test_robots_policy_wildcard_patterns():
    sample = """
User-agent: SiteDNABot
Disallow: /*.pdf$
Disallow: /temp*
"""
    policy = RobotsPolicy.parse(sample, origin="https://example.com")

    assert policy.is_allowed("https://example.com/document.pdf", user_agent="SiteDNABot") is False
    assert policy.is_allowed("https://example.com/document.pdf?ref=1", user_agent="SiteDNABot") is True
    assert policy.is_allowed("https://example.com/temp/cache", user_agent="SiteDNABot") is False
    assert policy.is_allowed("https://example.com/normal-page", user_agent="SiteDNABot") is True
