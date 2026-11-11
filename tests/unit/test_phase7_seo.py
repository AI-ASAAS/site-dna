"""Phase 7 tests for the technical SEO analyzer and sitemap parsing."""

import gzip

import pytest

from site_dna.analyzers.seo import (
    SeoAnalyzer,
    SitemapResult,
    SitemapStatus,
    check_broken_links,
    fetch_sitemap,
)
from site_dna.crawler.robots import RobotsTxt
from site_dna.models.common import CheckStatus, ModuleStatus
from site_dna.models.page import LinkItem, PageData

URL = "https://example.com/page"
GOOD_TITLE = "Reliable Website Auditing Services for Teams"
GOOD_DESCRIPTION = (
    "Run a clear technical website audit with page-level SEO checks, link validation, "
    "and actionable findings for your team."
)
GOOD_HTML = f"""<!doctype html>
<html lang="en">
<head>
  <title>{GOOD_TITLE}</title>
  <meta name="description" content="{GOOD_DESCRIPTION}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="{URL}">
  <meta property="og:title" content="Audit">
  <meta property="og:description" content="Audit description">
  <meta property="og:image" content="https://example.com/og.png">
</head>
<body>
  <h1>Audit your site</h1>
  <h2>What we check</h2>
  <img src="/logo.png" alt="Site DNA logo">
</body>
</html>"""


def _page(
    *,
    url=URL,
    html=GOOD_HTML,
    title=GOOD_TITLE,
    status=200,
    links=None,
    images=None,
    html_sha256=None,
    headers=None,
    language="en",
):
    return PageData(
        url=url,
        final_url=url,
        http_status=status,
        title=title,
        language=language,
        raw_html=html,
        links=links or [],
        images=images or [],
        html_sha256=html_sha256,
        http_headers=headers or {},
    )


def _by_id(result, url=URL):
    return {check.id: check for check in result.data.checks if check.url == url}


def _site(result):
    return {check.id: check for check in result.data.checks if check.scope == "site"}


class FakeResponse:
    def __init__(self, status_code=200, content=b""):
        self.status_code = status_code
        self.content = content


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def safe_get(self, url):
        self.calls.append(url)
        value = self.responses[url]
        if isinstance(value, Exception):
            raise value
        return value


@pytest.mark.anyio
async def test_good_page_passes_core_page_checks():
    result = await SeoAnalyzer().analyze([_page()])

    assert result.status is ModuleStatus.ok
    checks = _by_id(result)
    for rule_id in (
        "title",
        "meta_description",
        "meta_robots",
        "canonical",
        "open_graph",
        "headings",
        "heading_hierarchy",
        "images_alt",
        "lang",
        "viewport",
    ):
        assert checks[rule_id].status is CheckStatus.passed


@pytest.mark.anyio
async def test_missing_page_signals_are_reported_as_issues():
    html = """<html><head></head><body><img src="/no-alt.png"></body></html>"""
    page = _page(html=html, title="", language=None)

    result = await SeoAnalyzer().analyze([page])

    checks = _by_id(result)
    for rule_id in ("title", "meta_description", "headings", "images_alt"):
        assert checks[rule_id].status is CheckStatus.failed
    for rule_id in ("lang", "viewport"):
        assert checks[rule_id].status is CheckStatus.warning
    issue_ids = {issue.id for issue in result.data.issues}
    assert {"title", "meta_description", "headings", "images_alt", "lang", "viewport"} <= issue_ids


@pytest.mark.anyio
async def test_title_and_description_lengths_warn():
    html = GOOD_HTML.replace(GOOD_TITLE, "Short").replace(GOOD_DESCRIPTION, "Too short")
    page = _page(html=html, title="Short")

    result = await SeoAnalyzer().analyze([page])

    checks = _by_id(result)
    assert checks["title"].status is CheckStatus.warning
    assert checks["meta_description"].status is CheckStatus.warning


@pytest.mark.anyio
async def test_multiple_h1_and_skipped_heading_levels_warn():
    html = """<html lang="en"><head>
    <title>Reliable Website Auditing Services for Teams</title>
    <meta name="description" content="A sufficiently long meta description for the page that should pass the configured minimum length requirement.">
    <meta name="viewport" content="width=device-width">
    <link rel="canonical" href="https://example.com/page">
    <meta property="og:title" content="t">
    <meta property="og:description" content="d">
    <meta property="og:image" content="i">
    </head><body><h1>One</h1><h1>Two</h1><h3>Deep</h3></body></html>"""

    result = await SeoAnalyzer().analyze([_page(html=html)])

    checks = _by_id(result)
    assert checks["headings"].status is CheckStatus.warning
    assert checks["heading_hierarchy"].status is CheckStatus.warning


@pytest.mark.anyio
async def test_restrictive_meta_robots_and_header_warn():
    html = GOOD_HTML.replace(
        '<meta name="robots" content="index,follow">',
        '<meta name="robots" content="noindex,nofollow">',
    )
    page = _page(html=html, headers={"x-robots-tag": "noarchive"})

    result = await SeoAnalyzer().analyze([page])

    check = _by_id(result)["meta_robots"]
    assert check.status is CheckStatus.warning
    assert "noindex" in check.value


@pytest.mark.anyio
async def test_canonical_mismatch_warns():
    html = GOOD_HTML.replace(f'<link rel="canonical" href="{URL}">', '<link rel="canonical" href="/other">')

    result = await SeoAnalyzer().analyze([_page(html=html)])

    check = _by_id(result)["canonical"]
    assert check.status is CheckStatus.warning
    assert check.value == "https://example.com/other"


@pytest.mark.anyio
async def test_site_checks_cover_robots_sitemap_status_links_and_duplicates():
    robots = RobotsTxt.from_text(
        "https://example.com",
        "User-agent: *\nAllow: /\nSitemap: https://example.com/sitemap.xml\n",
    )
    sitemap = SitemapResult(
        status=SitemapStatus.found,
        urls=["https://example.com/", "https://example.com/page"],
        source="https://example.com/sitemap.xml",
        warnings=[],
        truncated=False,
    )
    pages = [
        _page(url="https://example.com/", html_sha256="same"),
        _page(url=URL, html_sha256="same"),
    ]

    result = await SeoAnalyzer().analyze(pages, robots=robots, sitemap=sitemap)

    checks = _site(result)
    assert checks["robots_txt"].status is CheckStatus.passed
    assert checks["sitemap"].status is CheckStatus.passed
    assert checks["status_codes"].status is CheckStatus.passed
    assert checks["links"].status is CheckStatus.passed
    assert checks["broken_links"].status is CheckStatus.not_available
    assert checks["duplicates"].status is CheckStatus.warning
    assert checks["duplicates"].value["duplicate_content_hashes"] == {"same": [pages[0].url, pages[1].url]}


@pytest.mark.anyio
async def test_broken_links_are_internal_first_and_capped():
    internal = LinkItem(url="https://example.com/missing", text="Missing", internal=True)
    external = LinkItem(url="https://external.test/ok", text="External", internal=False)
    client = FakeClient(
        {
            "https://example.com/missing": FakeResponse(404),
            "https://external.test/ok": FakeResponse(200),
        }
    )

    broken, checked, truncated, warnings, total = await check_broken_links(
        client,
        [_page(links=[external, internal])],
        max_checks=1,
    )

    assert truncated is True
    assert checked == 1
    assert client.calls == ["https://example.com/missing"]
    assert warnings == []
    assert total == 2
    assert broken[0].url == "https://example.com/missing"
    assert broken[0].status_code == 404


@pytest.mark.anyio
async def test_broken_links_respect_robots_and_transport_errors():
    robots = RobotsTxt.from_text(
        "https://example.com",
        "User-agent: *\nDisallow: /private\nAllow: /public\n",
    )
    private = LinkItem(url="https://example.com/private/x", text="Private", internal=True)
    public = LinkItem(url="https://example.com/public/x", text="Public", internal=True)
    client = FakeClient({"https://example.com/public/x": ConnectionError("boom")})

    broken, checked, truncated, warnings, total = await check_broken_links(
        client,
        [_page(links=[private, public])],
        robots=robots,
    )

    assert truncated is False
    assert checked == 1
    assert client.calls == ["https://example.com/public/x"]
    assert warnings == []
    assert total == 2
    assert broken[0].error == "boom"


@pytest.mark.anyio
async def test_fetch_sitemap_flattens_sitemap_index():
    index = b"""<?xml version="1.0"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <sitemap><loc>https://example.com/child.xml</loc></sitemap>
    </sitemapindex>"""
    child = b"""<?xml version="1.0"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.com/</loc></url>
      <url><loc>https://example.com/about</loc></url>
    </urlset>"""
    client = FakeClient(
        {
            "https://example.com/sitemap.xml": FakeResponse(200, index),
            "https://example.com/child.xml": FakeResponse(200, child),
        }
    )

    result = await fetch_sitemap(client, "https://example.com")

    assert result.status is SitemapStatus.found
    assert result.source == "https://example.com/sitemap.xml"
    assert result.urls == ["https://example.com/", "https://example.com/about"]


@pytest.mark.anyio
async def test_fetch_sitemap_handles_gzip_and_missing():
    urlset = b"""<?xml version="1.0"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.com/gzip</loc></url>
    </urlset>"""
    client = FakeClient({"https://example.com/sitemap.xml": FakeResponse(200, gzip.compress(urlset))})

    result = await fetch_sitemap(client, "https://example.com")
    assert result.status is SitemapStatus.found
    assert result.urls == ["https://example.com/gzip"]

    missing_client = FakeClient({"https://example.com/sitemap.xml": FakeResponse(404)})
    missing = await fetch_sitemap(missing_client, "https://example.com")
    assert missing.status is SitemapStatus.missing


@pytest.mark.anyio
async def test_summary_counts_every_check_and_issues_are_actionable_only():
    result = await SeoAnalyzer().analyze([_page()])

    summary = result.data.summary
    assert summary.passed + summary.warning + summary.failed + summary.not_available == len(result.data.checks)
    assert {issue.id for issue in result.data.issues} == {
        check.id
        for check in result.data.checks
        if check.status in (CheckStatus.failed, CheckStatus.warning)
    }


@pytest.mark.anyio
async def test_no_pages_returns_partial_module_result():
    result = await SeoAnalyzer().analyze([])

    assert result.status is ModuleStatus.partial
    assert result.reason == "no_pages"
    assert result.data is not None
    assert result.data.summary.not_available >= 1

