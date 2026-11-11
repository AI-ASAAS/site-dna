"""Phase 6 tests for the PageSpeed Insights client."""

import json
import logging
from pathlib import Path

import httpx
import pytest
import respx

from site_dna.integrations.pagespeed import PageSpeedClient
from site_dna.models.common import ModuleStatus

FIXTURES = Path(__file__).parent.parent / "fixtures" / "psi"
PSI_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
TARGET_URL = "https://example.com/"


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _client(**overrides) -> PageSpeedClient:
    options = {"api_key": None, "retry_wait": 0}
    options.update(overrides)
    return PageSpeedClient(**options)


@pytest.mark.anyio
async def test_fetch_parses_mobile_success_fixture():
    payload = _fixture("mobile_success.json")

    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(PSI_URL).mock(return_value=httpx.Response(200, json=payload))
        async with _client() as client:
            result = await client.fetch(TARGET_URL, "mobile")

    assert route.call_count == 1
    assert result.status == ModuleStatus.ok
    assert result.data is not None
    data = result.data
    assert data.status == ModuleStatus.ok
    assert data.score == 72
    assert data.lab.lcp_ms == 3200
    assert data.lab.fcp_ms == 1800
    assert data.lab.speed_index_ms == 3000
    assert data.lab.tbt_ms == 420
    assert data.lab.cls == pytest.approx(0.08)
    assert data.field.source == "crux_url"
    assert data.field.lcp is not None
    assert data.field.lcp.percentile == 3200
    assert data.field.lcp.category == "AVERAGE"
    assert data.field.inp is not None
    assert data.field.inp.percentile == 180
    assert data.field.cls is not None
    assert data.field.cls.percentile == pytest.approx(0.08)
    assert data.lighthouse_version == "12.6.0"
    assert data.fetch_time == "2026-11-10T12:00:00.000Z"
    assert data.final_url == "https://example.com/"
    assert data.runtime_errors == ["Lighthouse run completed with warnings"]

    opportunities = {item.id: item for item in data.opportunities}
    assert opportunities["render-blocking-resources"].savings_ms == 1200
    assert opportunities["unused-css-rules"].savings_bytes == 45000
    assert opportunities["uses-responsive-images"].savings_ms == 800
    assert "https://developer.chrome.com" not in (
        opportunities["render-blocking-resources"].description or ""
    )

    diagnostics = {item.id: item for item in data.diagnostics}
    assert {"uses-optimized-images", "dom-size", "third-party-summary", "insight-lcp-breakdown"} <= set(
        diagnostics
    )
    assert diagnostics["insight-lcp-breakdown"].display_value == "Time to first byte 800 ms"


@pytest.mark.anyio
async def test_fetch_uses_origin_field_data_as_fallback():
    payload = _fixture("desktop_success.json")

    with respx.mock(assert_all_called=False) as mock:
        mock.get(PSI_URL).mock(return_value=httpx.Response(200, json=payload))
        async with _client() as client:
            result = await client.fetch(TARGET_URL, "desktop")

    assert result.status == ModuleStatus.ok
    assert result.data is not None
    data = result.data
    assert data.score == 95
    assert data.field.source == "crux_origin"
    assert data.field.lcp is not None
    assert data.field.lcp.percentile == 4000
    assert data.field.cls is not None
    assert data.field.cls.percentile == pytest.approx(0.15)
    assert data.opportunities == []


@pytest.mark.anyio
async def test_fetch_performance_runs_both_strategies_and_adds_inp_note():
    mobile = _fixture("mobile_success.json")
    desktop = _fixture("desktop_success.json")

    def handler(request: httpx.Request) -> httpx.Response:
        payload = mobile if request.url.params.get("strategy") == "mobile" else desktop
        return httpx.Response(200, json=payload)

    with respx.mock(assert_all_called=False) as mock:
        mock.get(PSI_URL).mock(side_effect=handler)
        async with _client() as client:
            result = await client.fetch_performance(TARGET_URL)

    assert result.status == ModuleStatus.ok
    assert result.data is not None
    assert result.data.mobile.score == 72
    assert result.data.desktop.score == 95
    assert result.data.notes
    assert "INP" in result.data.notes[0]


@pytest.mark.anyio
async def test_fetch_performance_is_partial_when_one_strategy_fails():
    desktop = _fixture("desktop_success.json")
    quota = _fixture("recorded_429.json")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.params.get("strategy") == "mobile":
            return httpx.Response(429, json=quota)
        return httpx.Response(200, json=desktop)

    with respx.mock(assert_all_called=False) as mock:
        mock.get(PSI_URL).mock(side_effect=handler)
        async with _client() as client:
            result = await client.fetch_performance(TARGET_URL)

    assert result.status == ModuleStatus.partial
    assert result.data is not None
    assert result.data.mobile.status == ModuleStatus.failed
    assert result.data.mobile.reason == "quota_exceeded"
    assert result.data.desktop.status == ModuleStatus.ok
    assert result.data.notes


@pytest.mark.anyio
async def test_fetch_retries_429_then_succeeds():
    payload = _fixture("mobile_success.json")
    quota = _fixture("recorded_429.json")
    responses = [
        httpx.Response(429, json=quota),
        httpx.Response(200, json=payload),
    ]

    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(PSI_URL).mock(side_effect=responses)
        async with _client() as client:
            result = await client.fetch(TARGET_URL, "mobile")

    assert result.status == ModuleStatus.ok
    assert route.call_count == 2


@pytest.mark.anyio
async def test_fetch_maps_persistent_429_to_quota_exceeded():
    quota = _fixture("recorded_429.json")

    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(PSI_URL).mock(return_value=httpx.Response(429, json=quota))
        async with _client() as client:
            result = await client.fetch(TARGET_URL, "mobile")

    assert result.status == ModuleStatus.failed
    assert result.data is not None
    assert result.data.reason == "quota_exceeded"
    assert route.call_count == 4


@pytest.mark.anyio
async def test_fetch_maps_persistent_500_to_http_error():
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(PSI_URL).mock(return_value=httpx.Response(500, text="server error"))
        async with _client() as client:
            result = await client.fetch(TARGET_URL, "mobile")

    assert result.status == ModuleStatus.failed
    assert result.data is not None
    assert result.data.reason == "http_error"
    assert route.call_count == 4


@pytest.mark.anyio
async def test_fetch_maps_timeout():
    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(PSI_URL).mock(side_effect=httpx.TimeoutException("timed out"))
        async with _client() as client:
            result = await client.fetch(TARGET_URL, "mobile")

    assert result.status == ModuleStatus.failed
    assert result.data is not None
    assert result.data.reason == "timeout"
    assert route.call_count == 4


@pytest.mark.anyio
async def test_fetch_maps_malformed_json_to_bad_response():
    with respx.mock(assert_all_called=False) as mock:
        mock.get(PSI_URL).mock(return_value=httpx.Response(200, text="not json"))
        async with _client() as client:
            result = await client.fetch(TARGET_URL, "mobile")

    assert result.status == ModuleStatus.failed
    assert result.data is not None
    assert result.data.reason == "bad_response"


@pytest.mark.anyio
async def test_fetch_maps_google_unreachable_error_without_retry():
    error_payload = {
        "error": {
            "code": 400,
            "message": "Lighthouse returned error: FAILED_DOCUMENT_REQUEST. The URL cannot be fetched.",
        }
    }

    with respx.mock(assert_all_called=False) as mock:
        route = mock.get(PSI_URL).mock(return_value=httpx.Response(400, json=error_payload))
        async with _client() as client:
            result = await client.fetch(TARGET_URL, "mobile")

    assert result.status == ModuleStatus.failed
    assert result.data is not None
    assert result.data.reason == "invalid_url_or_unreachable"
    assert route.call_count == 1


@pytest.mark.anyio
async def test_fetch_handles_missing_loading_experience():
    payload = {
        "lighthouseResult": {
            "categories": {"performance": {"score": 0.5, "auditRefs": []}},
            "audits": {},
        }
    }

    with respx.mock(assert_all_called=False) as mock:
        mock.get(PSI_URL).mock(return_value=httpx.Response(200, json=payload))
        async with _client() as client:
            result = await client.fetch(TARGET_URL, "mobile")

    assert result.status == ModuleStatus.ok
    assert result.data is not None
    assert result.data.field.source is None
    assert result.data.field.lcp is None
    assert result.data.field.inp is None
    assert result.data.field.cls is None


@pytest.mark.anyio
async def test_fetch_without_key_adds_warning():
    payload = _fixture("mobile_success.json")

    with respx.mock(assert_all_called=False) as mock:
        mock.get(PSI_URL).mock(return_value=httpx.Response(200, json=payload))
        async with _client() as client:
            result = await client.fetch(TARGET_URL, "mobile")

    assert result.status == ModuleStatus.ok
    assert any("PSI_API_KEY" in warning for warning in result.warnings)


@pytest.mark.anyio
async def test_api_key_never_appears_in_logs(caplog):
    payload = _fixture("mobile_success.json")
    secret = "SECRET_PSI_KEY_1234567890"
    caplog.set_level(logging.DEBUG)

    with respx.mock(assert_all_called=False) as mock:
        mock.get(PSI_URL).mock(return_value=httpx.Response(200, json=payload))
        async with _client(api_key=secret) as client:
            result = await client.fetch(TARGET_URL, "mobile")

    assert result.status == ModuleStatus.ok
    assert secret not in caplog.text
