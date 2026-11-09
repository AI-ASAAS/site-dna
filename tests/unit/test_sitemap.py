"""Unit tests for safe XML sitemap parsing and discovery."""

from pathlib import Path

from site_dna.discovery.sitemap import _extract_loc_values, _is_sitemap_index


def test_extract_loc_values_from_standard_urlset():
    fixture_path = Path("tests/fixtures/discovery/sample_sitemap.xml")
    content = fixture_path.read_bytes()

    locs = _extract_loc_values(content, target_parent_tag="url")
    assert "https://example.com/" in locs
    assert "https://example.com/about-us" in locs
    assert "https://example.com/services" in locs
    assert "https://example.com/pricing" in locs
    assert "https://external-domain.com/unrelated" in locs
    assert len(locs) == 5


def test_is_sitemap_index():
    index_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
       <sitemap>
          <loc>https://example.com/sitemap-pages.xml</loc>
       </sitemap>
    </sitemapindex>"""
    assert _is_sitemap_index(index_xml) is True

    urlset_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
       <url><loc>https://example.com/</loc></url>
    </urlset>"""
    assert _is_sitemap_index(urlset_xml) is False
