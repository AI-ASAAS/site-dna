"""Unit tests for WebsiteDiscoveryTool and DiscoveryFlow execution."""

from unittest.mock import patch

from site_dna.flows.discovery_flow import DiscoveryFlow
from site_dna.schemas.discovery import CrawlResult, CrawlStatistics, WebsiteInfo
from site_dna.tools.website_discovery_tool import WebsiteDiscoveryTool


def test_website_discovery_tool_sync_execution():
    mock_result = CrawlResult(
        run_id="tool-run-1",
        website_info=WebsiteInfo(
            initial_url="https://example.com",
            canonical_origin="https://example.com",
        ),
        pages=[],
        discovered_internal_links=[],
        evidence=[],
        errors=[],
        statistics=CrawlStatistics(total_pages_crawled=2),
    )

    with patch("site_dna.discovery.service.WebsiteDiscoveryService.discover_sync", return_value=mock_result):
        tool = WebsiteDiscoveryTool()
        output_json = tool.run(url="https://example.com", max_pages=2)
        assert "tool-run-1" in output_json
        assert "https://example.com" in output_json


def test_discovery_flow_execution():
    mock_result = CrawlResult(
        run_id="flow-run-1",
        website_info=WebsiteInfo(
            initial_url="https://example.com",
            canonical_origin="https://example.com",
        ),
        pages=[],
        discovered_internal_links=[],
        evidence=[],
        errors=[],
        statistics=CrawlStatistics(total_pages_crawled=1),
    )

    with patch("site_dna.discovery.service.WebsiteDiscoveryService.discover_sync", return_value=mock_result):
        flow = DiscoveryFlow(target_url="https://example.com", max_pages=3)
        flow.kickoff()

        assert flow.state.execution_status == "completed"
        assert flow.state.crawl_result is not None
        assert flow.state.crawl_result.run_id == "flow-run-1"
        assert flow.state.started_at is not None
        assert flow.state.completed_at is not None
