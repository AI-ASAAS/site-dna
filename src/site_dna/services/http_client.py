"""Safe async HTTP client for the Website Intelligence MVP (Phase 2).

Provides manual redirect validation, response-size ceilings, per-host token-bucket
rate limiting, and retries for transient failures.
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urljoin, urlsplit

import httpx
from tenacity import AsyncRetrying, retry_if_exception_type, stop_after_attempt, wait_exponential

from site_dna.services.security import UrlRejected, validate_url

USER_AGENT = "WebsiteIntelBot/1.0 (+contact)"
DEFAULT_MAX_BYTES = 5 * 1024 * 1024
DEFAULT_MAX_REDIRECTS = 5
REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


class FetchError(Exception):
    """Raised when a fetch fails after retries or violates redirect policy."""


class ResponseTooLargeError(FetchError):
    """Raised when a response body exceeds the configured byte ceiling."""


@dataclass
class ResponseData:
    """Result of a safe HTTP request."""

    url: str
    final_url: str
    status_code: int
    headers: dict[str, str]
    content: bytes
    redirect_history: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        """Decode the body using the declared charset, falling back to UTF-8."""
        content_type = self.headers.get("content-type", "")
        encoding = "utf-8"
        if "charset=" in content_type:
            encoding = content_type.split("charset=")[-1].split(";")[0].strip().strip('"').strip("'")
        try:
            return self.content.decode(encoding, errors="replace")
        except (LookupError, UnicodeDecodeError):
            return self.content.decode("utf-8", errors="replace")


class _RetryableStatus(Exception):
    """Internal marker for a 5xx response that should be retried."""

    def __init__(self, response: ResponseData):
        super().__init__(f"retryable status {response.status_code}")
        self.response = response


class TokenBucket:
    """Async token bucket enforcing a sustained request rate."""

    def __init__(self, rate: float, capacity: float = 1.0):
        if rate <= 0:
            raise ValueError("rate must be positive")
        self._rate = rate
        self._capacity = capacity
        self._tokens = capacity
        self._updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            self._tokens = min(self._capacity, self._tokens + (now - self._updated) * self._rate)
            self._updated = now

            if self._tokens < 1.0:
                wait = (1.0 - self._tokens) / self._rate
                await asyncio.sleep(wait)
                self._tokens = 0.0
                self._updated = time.monotonic()
            else:
                self._tokens -= 1.0


def create_async_client(
    *,
    user_agent: str = USER_AGENT,
    timeout: float = 20.0,
    transport: Optional[httpx.AsyncBaseTransport] = None,
) -> httpx.AsyncClient:
    """Create the single httpx client used for scan fetches."""
    return httpx.AsyncClient(
        headers={"User-Agent": user_agent},
        timeout=httpx.Timeout(connect=timeout, read=timeout, write=timeout, pool=timeout),
        follow_redirects=False,
        transport=transport,
    )


class SafeHttpClient:
    """Async HTTP client that validates every hop and bounds fetch cost."""

    def __init__(
        self,
        *,
        client: Optional[httpx.AsyncClient] = None,
        per_host_rps: float = 2.0,
        max_bytes: int = DEFAULT_MAX_BYTES,
        max_redirects: int = DEFAULT_MAX_REDIRECTS,
        timeout: float = 20.0,
        user_agent: str = USER_AGENT,
        validator=None,
        retries: int = 2,
        retry_wait: float = 0.5,
    ):
        self._client = client or create_async_client(user_agent=user_agent, timeout=timeout)
        self._owns_client = client is None
        self._per_host_rps = per_host_rps
        self._max_bytes = max_bytes
        self._max_redirects = max_redirects
        self._validator = validator or validate_url
        self._retries = retries
        self._retry_wait = retry_wait
        self._buckets: dict[str, TokenBucket] = {}

    async def __aenter__(self) -> "SafeHttpClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _bucket_for(self, url: str) -> TokenBucket:
        host = urlsplit(url).hostname or ""
        bucket = self._buckets.get(host)
        if bucket is None:
            bucket = TokenBucket(self._per_host_rps)
            self._buckets[host] = bucket
        return bucket

    async def safe_get(self, url: str) -> ResponseData:
        """GET a URL, validating every redirect hop."""
        return await self._request("GET", url)

    async def safe_head(self, url: str) -> ResponseData:
        """HEAD a URL, validating every redirect hop."""
        return await self._request("HEAD", url)

    async def _request(self, method: str, url: str) -> ResponseData:
        current = url
        redirect_history: list[str] = []

        for hop in range(self._max_redirects + 1):
            await self._bucket_for(current).acquire()
            response = await self._request_with_retry(method, current)

            if response.status_code in REDIRECT_STATUSES:
                location = response.headers.get("location")
                if not location:
                    raise FetchError(f"Redirect {response.status_code} missing Location header for {current}")
                if hop >= self._max_redirects:
                    raise FetchError(f"Exceeded maximum redirects ({self._max_redirects}) for {url}")
                redirect_history.append(current)
                current = urljoin(current, location)
                continue

            response.url = url
            response.redirect_history = redirect_history
            return response

        raise FetchError(f"Exceeded maximum redirects ({self._max_redirects}) for {url}")

    async def _request_with_retry(self, method: str, url: str) -> ResponseData:
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(self._retries + 1),
                wait=wait_exponential(multiplier=self._retry_wait, max=self._retry_wait * 8 or 0.01),
                retry=retry_if_exception_type((httpx.TimeoutException, _RetryableStatus)),
                reraise=True,
            ):
                with attempt:
                    data = await self._single_request(method, url)
                    if data.status_code >= 500:
                        raise _RetryableStatus(data)
                    return data
        except _RetryableStatus as e:
            return e.response
        except httpx.TimeoutException as e:
            raise FetchError(f"HTTP request timed out for {url}: {e}") from e
        except httpx.RequestError as e:
            raise FetchError(f"Network transport error for {url}: {e}") from e

        raise FetchError(f"Request failed for {url}")

    async def _single_request(self, method: str, url: str) -> ResponseData:
        await self._validator(url)

        try:
            async with self._client.stream(method, url) as response:
                content = b""
                if method != "HEAD":
                    declared_length = response.headers.get("content-length")
                    if declared_length and declared_length.isdigit() and int(declared_length) > self._max_bytes:
                        raise ResponseTooLargeError(
                            f"Content-Length {declared_length} exceeds limit {self._max_bytes} for {url}"
                        )

                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > self._max_bytes:
                            raise ResponseTooLargeError(
                                f"Response body exceeded {self._max_bytes} bytes for {url}"
                            )
                        chunks.append(chunk)
                    content = b"".join(chunks)

                return ResponseData(
                    url=url,
                    final_url=url,
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    content=content,
                )
        except (UrlRejected, ResponseTooLargeError):
            raise
        except httpx.TimeoutException:
            raise
        except httpx.RequestError:
            raise
