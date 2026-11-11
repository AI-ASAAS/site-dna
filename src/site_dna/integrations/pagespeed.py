"""PageSpeed Insights client for the Website Intelligence MVP (Phase 6)."""

import asyncio
import logging
import re
import time
from typing import Any, Literal
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential, wait_fixed

from site_dna.core.logging import SensitiveDataFilter, get_logger
from site_dna.models.common import ModuleError, ModuleResult, ModuleStatus
from site_dna.models.performance import (
    Diagnostic,
    FieldMetric,
    FieldMetrics,
    LabMetrics,
    Opportunity,
    Performance,
    StrategyPerformance,
)

logger = get_logger("integrations.pagespeed")

_httpx_logger = logging.getLogger("httpx")
_httpx_logger.setLevel(logging.WARNING)
if not any(isinstance(existing, SensitiveDataFilter) for existing in _httpx_logger.filters):
    _httpx_logger.addFilter(SensitiveDataFilter())

PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
DEFAULT_TIMEOUT_SECONDS = 90.0
DEFAULT_RETRIES = 3
DEFAULT_RETRY_WAIT_SECONDS = 1.0
MISSING_API_KEY_WARNING = (
    "PSI_API_KEY is not configured; unauthenticated PageSpeed requests may be rate-limited"
)
INP_NOTE = (
    "INP (Interaction to Next Paint) is only available when Chrome UX Report field data exists; "
    "Lighthouse lab runs do not produce INP."
)

_MARKDOWN_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_KEY_QUERY = re.compile(r"([?&]key=)[^&\s\"']+", re.IGNORECASE)
_RETRYABLE_STATUSES = frozenset({429})


class _RetryablePSI(Exception):
    """Internal marker for a PSI response that should be retried."""

    def __init__(self, response: httpx.Response):
        super().__init__(f"retryable PSI status {response.status_code}")
        self.response = response


class PageSpeedClient:
    """Fetch and parse mobile and desktop PageSpeed Insights results."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client: httpx.AsyncClient | None = None,
        retries: int = DEFAULT_RETRIES,
        retry_wait: float = DEFAULT_RETRY_WAIT_SECONDS,
    ) -> None:
        self._api_key = api_key
        self._client = client or httpx.AsyncClient(timeout=httpx.Timeout(timeout))
        self._owns_client = client is None
        self._retries = retries
        self._retry_wait = retry_wait

    async def __aenter__(self) -> "PageSpeedClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def fetch(
        self,
        url: str,
        strategy: Literal["mobile", "desktop"],
    ) -> ModuleResult[StrategyPerformance]:
        """Fetch one strategy and return a strategy-level module result."""
        started = time.perf_counter()
        warnings = [] if self._api_key else [MISSING_API_KEY_WARNING]
        safe_url = _redact_url(url)
        params: dict[str, str] = {
            "url": url,
            "strategy": strategy,
            "category": "performance",
        }
        if self._api_key:
            params["key"] = self._api_key

        logger.info("Fetching PSI %s data for %s", strategy, safe_url)

        try:
            response = await self._request(params)
        except httpx.TimeoutException:
            return self._failure("timeout", "PSI request timed out", started, warnings, safe_url)
        except _RetryablePSI as exc:
            reason = "quota_exceeded" if exc.response.status_code == 429 else "http_error"
            return self._failure(
                reason,
                f"PSI returned HTTP {exc.response.status_code} after retries",
                started,
                warnings,
                safe_url,
            )
        except httpx.RequestError as exc:
            return self._failure(
                "http_error",
                _redact_text(str(exc), self._api_key),
                started,
                warnings,
                safe_url,
            )

        if response.status_code == 400:
            message = _error_message(response)
            reason = "invalid_url_or_unreachable" if _is_unreachable(message) else "http_error"
            return self._failure(
                reason,
                _redact_text(message or "PSI rejected the URL", self._api_key),
                started,
                warnings,
                safe_url,
            )
        if response.status_code == 403 and not self._api_key:
            return self._failure(
                "missing_api_key",
                "PSI requires an API key for this request",
                started,
                warnings,
                safe_url,
            )
        if response.status_code == 429:
            return self._failure("quota_exceeded", "PSI quota exceeded", started, warnings, safe_url)
        if response.status_code >= 400:
            return self._failure(
                "http_error",
                f"PSI returned HTTP {response.status_code}",
                started,
                warnings,
                safe_url,
            )

        try:
            payload = response.json()
        except ValueError:
            return self._failure(
                "bad_response", "PSI returned malformed JSON", started, warnings, safe_url
            )
        if not isinstance(payload, dict):
            return self._failure(
                "bad_response", "PSI returned an unexpected payload", started, warnings, safe_url
            )
        if "error" in payload and "lighthouseResult" not in payload:
            message = _error_message_from_payload(payload)
            reason = "invalid_url_or_unreachable" if _is_unreachable(message) else "bad_response"
            return self._failure(
                reason,
                _redact_text(message or "PSI returned an error payload", self._api_key),
                started,
                warnings,
                safe_url,
            )

        try:
            data = parse_strategy_payload(payload)
        except Exception:  # noqa: BLE001 - malformed third-party payload is a bad response
            return self._failure(
                "bad_response", "PSI returned an unexpected payload", started, warnings, safe_url
            )

        return ModuleResult[StrategyPerformance](
            status=ModuleStatus.ok,
            duration_ms=_elapsed_ms(started),
            data=data,
            warnings=warnings,
        )

    async def fetch_performance(self, url: str) -> ModuleResult[Performance]:
        """Fetch mobile and desktop concurrently and combine the outcomes."""
        started = time.perf_counter()
        mobile_result, desktop_result = await asyncio.gather(
            self.fetch(url, "mobile"),
            self.fetch(url, "desktop"),
        )

        mobile = mobile_result.data or StrategyPerformance(
            status=mobile_result.status,
            reason=mobile_result.reason,
        )
        desktop = desktop_result.data or StrategyPerformance(
            status=desktop_result.status,
            reason=desktop_result.reason,
        )

        if mobile.status == ModuleStatus.ok and desktop.status == ModuleStatus.ok:
            status = ModuleStatus.ok
        elif mobile.status == ModuleStatus.ok or desktop.status == ModuleStatus.ok:
            status = ModuleStatus.partial
        else:
            status = ModuleStatus.failed

        warnings = list(dict.fromkeys([*mobile_result.warnings, *desktop_result.warnings]))
        errors = [*mobile_result.errors, *desktop_result.errors]

        return ModuleResult[Performance](
            status=status,
            reason=None if status == ModuleStatus.ok else (mobile.reason or desktop.reason),
            duration_ms=_elapsed_ms(started),
            data=Performance(mobile=mobile, desktop=desktop, notes=[INP_NOTE]),
            warnings=warnings,
            errors=errors,
        )

    async def _request(self, params: dict[str, str]) -> httpx.Response:
        wait = (
            wait_exponential(multiplier=self._retry_wait, max=8)
            if self._retry_wait > 0
            else wait_fixed(0)
        )
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self._retries + 1),
            wait=wait,
            retry=retry_if_exception_type((httpx.TimeoutException, _RetryablePSI)),
            reraise=True,
        ):
            with attempt:
                response = await self._client.get(PSI_ENDPOINT, params=params)
                if response.status_code in _RETRYABLE_STATUSES or 500 <= response.status_code < 600:
                    raise _RetryablePSI(response)
                return response
        raise RuntimeError("unreachable")

    def _failure(
        self,
        reason: str,
        message: str,
        started: float,
        warnings: list[str],
        safe_url: str,
    ) -> ModuleResult[StrategyPerformance]:
        logger.warning("PSI request failed for %s: %s", safe_url, reason)
        data = StrategyPerformance(status=ModuleStatus.failed, reason=reason)
        return ModuleResult[StrategyPerformance](
            status=ModuleStatus.failed,
            reason=reason,
            duration_ms=_elapsed_ms(started),
            data=data,
            warnings=warnings,
            errors=[ModuleError(code=reason, message=message, url=safe_url)],
        )


def parse_strategy_payload(payload: dict[str, Any]) -> StrategyPerformance:
    """Parse a PSI response defensively; missing fields become null."""
    lighthouse = _as_dict(payload.get("lighthouseResult"))
    categories = _as_dict(lighthouse.get("categories"))
    performance = _as_dict(categories.get("performance"))
    audits = _as_dict(lighthouse.get("audits"))
    audit_refs = _as_list(performance.get("auditRefs"))

    opportunities, diagnostics = _audit_findings(audit_refs, audits)

    return StrategyPerformance(
        status=ModuleStatus.ok,
        score=_score(performance.get("score")),
        lab=_lab_metrics(audits),
        field=_field_metrics(payload),
        opportunities=opportunities,
        diagnostics=diagnostics,
        lighthouse_version=_as_string(lighthouse.get("lighthouseVersion")),
        fetch_time=_as_string(lighthouse.get("fetchTime")),
        final_url=_as_string(lighthouse.get("finalUrl") or lighthouse.get("finalDisplayedUrl")),
        runtime_errors=_runtime_errors(lighthouse),
    )


def _lab_metrics(audits: dict[str, Any]) -> LabMetrics:
    return LabMetrics(
        lcp_ms=_metric_value(audits, "largest-contentful-paint"),
        fcp_ms=_metric_value(audits, "first-contentful-paint"),
        speed_index_ms=_metric_value(audits, "speed-index"),
        tbt_ms=_metric_value(audits, "total-blocking-time"),
        cls=_metric_value(audits, "cumulative-layout-shift"),
    )


def _field_metrics(payload: dict[str, Any]) -> FieldMetrics:
    url_metrics = _as_dict(_as_dict(payload.get("loadingExperience")).get("metrics"))
    origin_metrics = _as_dict(_as_dict(payload.get("originLoadingExperience")).get("metrics"))
    used_origin = False

    def pick(key: str, *, scale: float = 1.0) -> FieldMetric | None:
        nonlocal used_origin
        metric = _as_dict(url_metrics.get(key))
        if not metric:
            metric = _as_dict(origin_metrics.get(key))
            if metric:
                used_origin = True
        if not metric:
            return None
        percentile = _as_number(metric.get("percentile"))
        if percentile is not None:
            percentile = percentile / scale
        return FieldMetric(
            percentile=percentile,
            category=_as_string(metric.get("category")),
        )

    lcp = pick("LARGEST_CONTENTFUL_PAINT_MS")
    inp = pick("INTERACTION_TO_NEXT_PAINT")
    cls = pick("CUMULATIVE_LAYOUT_SHIFT_SCORE", scale=100.0)

    source: Literal["crux_url", "crux_origin"] | None
    if lcp is None and inp is None and cls is None:
        source = None
    elif used_origin:
        source = "crux_origin"
    else:
        source = "crux_url"

    return FieldMetrics(lcp=lcp, inp=inp, cls=cls, source=source)


def _audit_findings(
    audit_refs: list[Any],
    audits: dict[str, Any],
) -> tuple[list[Opportunity], list[Diagnostic]]:
    opportunities: list[Opportunity] = []
    diagnostics: list[Diagnostic] = []
    seen: set[str] = set()

    for ref in audit_refs:
        audit_id = _as_string(_as_dict(ref).get("id"))
        if not audit_id or audit_id in seen:
            continue
        audit = _as_dict(audits.get(audit_id))
        if not audit:
            continue

        details = _as_dict(audit.get("details"))
        details_type = _as_string(details.get("type"))
        savings_ms = _as_number(details.get("overallSavingsMs"))
        savings_bytes = _as_number(details.get("overallSavingsBytes"))

        if details_type == "opportunity" and ((savings_ms or 0) > 0 or (savings_bytes or 0) > 0):
            opportunities.append(
                Opportunity(
                    id=audit_id,
                    title=_as_string(audit.get("title")),
                    description=_strip_markdown(_as_string(audit.get("description"))),
                    savings_ms=savings_ms,
                    savings_bytes=savings_bytes,
                )
            )
            seen.add(audit_id)
            continue

        score = _as_number(audit.get("score"))
        score_display_mode = _as_string(audit.get("scoreDisplayMode"))
        items = _as_list(details.get("items"))
        is_diagnostic = (
            score_display_mode in {"informative", "numeric"}
            and score is not None
            and score < 0.9
        ) or (details_type in {"table", "list"} and bool(items))

        if is_diagnostic:
            diagnostics.append(_diagnostic(audit_id, audit, score))
            seen.add(audit_id)
        elif details_type and details_type not in {
            "opportunity",
            "table",
            "list",
            "debugdata",
            "criticalrequestchain",
            "filmstrip",
            "screenshot",
            "treemap-data",
        }:
            if audit.get("title") or audit.get("displayValue") or score is not None:
                diagnostics.append(_diagnostic(audit_id, audit, score))
                seen.add(audit_id)

    return opportunities, diagnostics


def _diagnostic(audit_id: str, audit: dict[str, Any], score: float | None) -> Diagnostic:
    return Diagnostic(
        id=audit_id,
        title=_as_string(audit.get("title")),
        score=score,
        display_value=_as_string(audit.get("displayValue")),
        description=_strip_markdown(_as_string(audit.get("description"))),
    )


def _runtime_errors(lighthouse: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    runtime_error = lighthouse.get("runtimeError")
    if isinstance(runtime_error, dict):
        message = _as_string(runtime_error.get("message")) or _as_string(runtime_error.get("code"))
        if message:
            errors.append(message)
    elif runtime_error:
        errors.append(str(runtime_error))

    for warning in _as_list(lighthouse.get("runWarnings")):
        if warning:
            errors.append(str(warning))
    return errors


def _metric_value(audits: dict[str, Any], audit_id: str) -> float | None:
    return _as_number(_as_dict(audits.get(audit_id)).get("numericValue"))


def _score(value: Any) -> int | None:
    score = _as_number(value)
    if score is None:
        return None
    return int(round(score * 100))


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _as_string(value: Any) -> str | None:
    if isinstance(value, str):
        return value or None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    return None


def _strip_markdown(value: str | None) -> str | None:
    if not value:
        return None
    return _MARKDOWN_LINK.sub(r"\1", value).strip() or None


def _error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text[:500]
    return _error_message_from_payload(payload)


def _error_message_from_payload(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    error = _as_dict(payload.get("error"))
    return _as_string(error.get("message")) or _as_string(payload.get("message")) or ""


def _is_unreachable(message: str) -> bool:
    lowered = message.lower()
    return any(
        marker in lowered
        for marker in (
            "failed_document_request",
            "cannot fetch",
            "unreachable",
            "invalid url",
            "error loading page",
            "lighthouse returned error",
        )
    )


def _redact_text(value: str, api_key: str | None) -> str:
    sanitized = _KEY_QUERY.sub(r"\1***", value)
    if api_key:
        sanitized = sanitized.replace(api_key, "***")
    return sanitized


def _redact_url(url: str) -> str:
    try:
        parts = urlsplit(url)
    except ValueError:
        return url
    query = [
        (name, value)
        for name, value in parse_qsl(parts.query, keep_blank_values=True)
        if name.lower() != "key"
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _elapsed_ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
