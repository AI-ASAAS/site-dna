"""Unit tests for Client-Side Observations Analyzer in Site DNA Phase 09."""

from site_dna.analysis.security_privacy.client_side_observations import ClientSideObservationsAnalyzer
from site_dna.schemas.security_privacy import SecurityPageRecord


def test_client_side_observations_inline_external_sri():
    """Verify counting of inline scripts, external scripts, and SRI attributes."""
    analyzer = ClientSideObservationsAnalyzer()

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <script>console.log("inline 1");</script>
        <script type="text/javascript">var x = 1;</script>
        <script src="https://cdn.example.com/lib.js" integrity="sha384-abc123456" crossorigin="anonymous"></script>
        <script src="https://untrusted.cdn.org/bad.js"></script>
    </head>
    <body>
        <script>document.write("unsafe");</script>
    </body>
    </html>
    """

    page = SecurityPageRecord(
        page_url="https://example.com/app",
        scheme="https",
        status_code=200,
    )

    crawl_dataset = {
        "pages": [
            {
                "url": "https://example.com/app",
                "raw_html": html,
            }
        ]
    }

    obs = analyzer.analyze([page], crawl_dataset=crawl_dataset)

    assert obs.inline_scripts_count == 3
    assert obs.external_scripts_count == 2
    assert obs.scripts_with_sri_count == 1
    assert obs.scripts_lacking_sri_count == 1
    assert obs.has_unpinned_external_scripts is True
    assert any("document.write" in p for p in obs.unsafe_patterns_observed)


def test_client_side_observations_empty_pages():
    """Verify graceful handling when no pages are provided."""
    analyzer = ClientSideObservationsAnalyzer()
    obs = analyzer.analyze([])

    assert obs.inline_scripts_count == 0
    assert obs.external_scripts_count == 0
    assert obs.scripts_with_sri_count == 0
