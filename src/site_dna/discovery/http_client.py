"""Secure HTTP client with connection-time SSRF protection and streaming size limits."""

import time
from typing import Optional
from urllib.parse import urljoin

import httpcore
import httpx

from site_dna.core.config import get_settings
from site_dna.core.logging import get_logger
from site_dna.core.security import SecurityValidationError, resolve_and_validate_host
from site_dna.discovery.url_validator import normalize_url

logger = get_logger("discovery.http_client")


class ResponseTooLargeError(Exception):
    """Raised when an HTTP response exceeds the maximum configured byte ceiling."""


class InvalidContentTypeError(Exception):
    """Raised when the fetched resource has a non-HTML/XML MIME type."""


class FetchError(Exception):
    """General error occurred during HTTP fetch."""


class HttpResponseData:
    """Encapsulates the result of a secure HTTP fetch."""

    def __init__(
        self,
        url: str,
        final_url: str,
        status_code: int,
        headers: dict[str, str],
        content: bytes,
        duration_ms: float,
        redirect_history: list[str],
    ):
        self.url = url
        self.final_url = final_url
        self.status_code = status_code
        self.headers = headers
        self.content = content
        self.duration_ms = duration_ms
        self.redirect_history = redirect_history

    @property
    def text(self) -> str:
        """Decode response body using detected charset or fallback to utf-8."""
        content_type = self.headers.get("content-type", "")
        encoding = "utf-8"
        if "charset=" in content_type:
            try:
                encoding = content_type.split("charset=")[-1].split(";")[0].strip().strip('"').strip("'")
            except Exception:
                encoding = "utf-8"

        try:
            return self.content.decode(encoding, errors="replace")
        except (LookupError, UnicodeDecodeError):
            return self.content.decode("utf-8", errors="replace")


class SSRFProtectedBackend(httpcore._backends.anyio.AnyIOBackend):
    """Network backend that enforces connection-time IP verification on every TCP connect.

    Prevents TOCTOU DNS rebinding by resolving and validating host IPs at socket creation.
    """

    async def connect_tcp(
        self,
        host: str,
        port: int,
        timeout: Optional[float] = None,
        local_address: Optional[str] = None,
        socket_options=None,
    ):
        verified_ips = resolve_and_validate_host(host)
        # Connect specifically to the first validated public IP
        return await super().connect_tcp(
            verified_ips[0],
            port,
            timeout=timeout,
            local_address=local_address,
            socket_options=socket_options,
        )


class SSRFProtectedTransport(httpx.AsyncHTTPTransport):
    """Async transport utilizing SSRFProtectedBackend for all outbound connections."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._pool = httpcore.AsyncConnectionPool(
            ssl_context=self._pool._ssl_context,
            max_connections=self._pool._max_connections,
            max_keepalive_connections=self._pool._max_keepalive_connections,
            keepalive_expiry=self._pool._keepalive_expiry,
            http1=self._pool._http1,
            http2=self._pool._http2,
            retries=self._pool._retries,
            network_backend=SSRFProtectedBackend(),
        )


class SecureHttpClient:
    """Async HTTP client configured for secure, polite, and constrained web crawling."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        connect_timeout: Optional[float] = None,
        read_timeout: Optional[float] = None,
        max_redirects: Optional[int] = None,
        max_html_bytes: Optional[int] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ):
        settings = get_settings()
        self.user_agent = user_agent or settings.crawler_user_agent
        self.connect_timeout = connect_timeout or settings.crawler_connect_timeout_seconds
        self.read_timeout = read_timeout or settings.crawler_read_timeout_seconds
        self.max_redirects = max_redirects or settings.crawler_max_redirects
        self.max_html_bytes = max_html_bytes or settings.crawler_max_html_bytes

        self.timeout = httpx.Timeout(
            connect=self.connect_timeout,
            read=self.read_timeout,
            write=10.0,
            pool=10.0,
        )
        self.transport = transport or SSRFProtectedTransport(verify=True)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "SecureHttpClient":
        if self._client is None:
            self._client = httpx.AsyncClient(
                transport=self.transport,
                timeout=self.timeout,
                headers={
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "ar,en-US;q=0.8,en;q=0.7",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                },
                follow_redirects=False,  # We manage redirects manually for strict security verification
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def fetch(
        self,
        url: str,
        allow_xml: bool = False,
        allow_plain_text: bool = False,
    ) -> HttpResponseData:
        """Fetch a single URL securely with size limits, redirect validation, and SSRF checks.

        Args:
            url: The normalized target URL.
            allow_xml: Whether to accept XML content types (e.g. for sitemaps).

        Raises:
            SecurityValidationError: If the URL or any redirect target fails SSRF validation.
            ResponseTooLargeError: If response exceeds byte limit.
            InvalidContentTypeError: If response content-type is non-HTML/XML.
            FetchError: On network errors, timeouts, or excessive redirects.
        """
        if not self._client:
            raise RuntimeError("SecureHttpClient must be used within an 'async with' context block.")

        current_url = normalize_url(url)
        redirect_history: list[str] = []
        start_time = time.perf_counter()

        for redirect_count in range(self.max_redirects + 1):
            try:
                # Pre-validate URL and DNS
                current_url = normalize_url(current_url)

                async with self._client.stream("GET", current_url) as response:
                    # Check for redirect status (301, 302, 303, 307, 308)
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise FetchError(f"Redirect response {response.status_code} missing Location header")

                        redirect_history.append(current_url)
                        current_url = normalize_url(urljoin(current_url, location))
                        logger.debug("Following redirect (%d): %s -> %s", redirect_count + 1, response.url, current_url)
                        continue

                    # Validate Content-Type
                    content_type = response.headers.get("content-type", "").lower()
                    allowed_types = ["text/html", "application/xhtml+xml"]
                    if allow_xml:
                        allowed_types.extend(["application/xml", "text/xml"])
                    if allow_plain_text:
                        allowed_types.extend(["text/plain"])

                    if response.status_code == 200 and not any(t in content_type for t in allowed_types):
                        raise InvalidContentTypeError(
                            f"Disallowed Content-Type '{content_type}' at {current_url}. Expected HTML/XML/Text."
                        )

                    # Validate Content-Length header if provided
                    content_length_header = response.headers.get("content-length")
                    if content_length_header and content_length_header.isdigit():
                        if int(content_length_header) > self.max_html_bytes:
                            raise ResponseTooLargeError(
                                f"Response Content-Length ({content_length_header} bytes) exceeds limit ({self.max_html_bytes} bytes)"
                            )

                    # Stream content with running size enforcement
                    chunks: list[bytes] = []
                    total_bytes = 0

                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        total_bytes += len(chunk)
                        if total_bytes > self.max_html_bytes:
                            raise ResponseTooLargeError(
                                f"Downloaded {total_bytes} bytes exceeding limit of {self.max_html_bytes} bytes"
                            )
                        chunks.append(chunk)

                    duration_ms = (time.perf_counter() - start_time) * 1000.0
                    body = b"".join(chunks)

                    return HttpResponseData(
                        url=url,
                        final_url=current_url,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        content=body,
                        duration_ms=duration_ms,
                        redirect_history=redirect_history,
                    )

            except (SecurityValidationError, ResponseTooLargeError, InvalidContentTypeError):
                raise
            except httpx.TimeoutException as e:
                raise FetchError(f"HTTP request timed out for {current_url}: {e}") from e
            except httpx.RequestError as e:
                raise FetchError(f"Network transport error for {current_url}: {e}") from e
            except Exception as e:
                raise FetchError(f"Unexpected error fetching {current_url}: {e}") from e

        raise FetchError(f"Exceeded maximum redirects ({self.max_redirects}) for {url}")
