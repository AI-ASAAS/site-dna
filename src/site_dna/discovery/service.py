"""WebsiteDiscoveryService providing high-level entry points for CLI, API, and CrewAI."""

import asyncio
from pathlib import Path
from typing import Optional

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.discovery.crawler import DeterministicCrawler
from site_dna.schemas.discovery import CrawlRequest, CrawlResult

logger = get_logger("discovery.service")


class WebsiteDiscoveryService:
    """Service facade for orchestrating website discovery and crawl runs."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    async def discover(self, request: CrawlRequest) -> CrawlResult:
        """Execute website discovery asynchronously."""
        crawler = DeterministicCrawler(
            settings=self.settings,
            max_pages=request.max_pages,
            max_depth=request.max_depth,
        )
        return await crawler.crawl(request.url)

    # Alias crawl -> discover for backward and multi-service compatibility
    crawl = discover

    def discover_sync(self, request: CrawlRequest) -> CrawlResult:
        """Synchronous wrapper for discovery crawl execution."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If already inside an event loop, run in a separate thread
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(lambda: asyncio.run(self.discover(request)))
                return future.result()
        else:
            return asyncio.run(self.discover(request))

    @staticmethod
    def save_run_result(result: CrawlResult, base_dir: str = "runs") -> Path:
        """Persist crawl result to runs/<run_id>/crawl.json."""
        target_dir = Path(base_dir) / result.run_id
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / "crawl.json"

        # Serialize Pydantic model to json
        json_data = result.model_dump_json(indent=2)
        file_path.write_text(json_data, encoding="utf-8")
        logger.info("Saved crawl result to %s", file_path)
        return file_path
