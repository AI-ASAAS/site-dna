"""FastAPI route for secure, protected website discovery and crawling."""

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.discovery.service import WebsiteDiscoveryService
from site_dna.schemas.discovery import CrawlRequest, CrawlResult

logger = get_logger("api.routes.discovery")

router = APIRouter(prefix="/api/v1/discovery", tags=["Discovery"])


def verify_discovery_access(
    request: Request,
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> None:
    """Validate that the discovery API is enabled and authenticated."""
    # Gate 1: Enabled flag
    if not settings.discovery_api_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Website discovery API is disabled. Set DISCOVERY_API_ENABLED=true in configuration.",
        )

    # Gate 2: Localhost check in development
    if settings.app_env == "development":
        client_host = request.client.host if request.client else ""
        if client_host not in ("127.0.0.1", "::1", "localhost", "testclient"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"In development mode, discovery API only accepts requests from loopback, got {client_host}.",
            )

    # Gate 3: Bearer token verification if configured
    if settings.discovery_api_token and settings.discovery_api_token.get_secret_value().strip():
        expected_token = settings.discovery_api_token.get_secret_value().strip()
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or malformed Authorization header. Bearer token required.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization.split("Bearer ", 1)[1].strip()
        if token != expected_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid discovery API authorization token.",
                headers={"WWW-Authenticate": "Bearer"},
            )


@router.post(
    "",
    response_model=CrawlResult,
    status_code=status.HTTP_200_OK,
    summary="Trigger website discovery and structured crawling",
    dependencies=[Depends(verify_discovery_access)],
)
async def discover_website(
    request_data: CrawlRequest,
    settings: Settings = Depends(get_settings),
) -> CrawlResult:
    """Execute website discovery and crawl, returning structured evidence and page data."""
    logger.info("Received discovery API request for URL: %s", request_data.url)
    service = WebsiteDiscoveryService(settings=settings)
    result = await service.discover(request_data)
    logger.info(
        "Discovery API request finished for URL: %s, pages crawled: %d",
        request_data.url,
        result.statistics.total_pages_crawled,
    )
    return result
