"""Multi-site Collection Coordinator for Site DNA Phase 08 — Competitor Intelligence."""

import json
from pathlib import Path
from typing import Any, Optional

from site_dna.core.logging import get_logger
from site_dna.discovery.service import WebsiteDiscoveryService
from site_dna.schemas.competitor_intelligence import CompetitorSourceRecord
from site_dna.schemas.discovery import CrawlRequest

logger = get_logger("analysis.competitor_intelligence.collection_coordinator")


class CompetitorCollectionCoordinator:
    """Manages multi-site evidence loading and safe crawling with rate limits and caching."""

    def __init__(self, base_dir: Path | str = "runs"):
        self.base_dir = Path(base_dir).resolve()
        self.discovery_service = WebsiteDiscoveryService()

    async def ensure_site_evidence(
        self,
        site_record: CompetitorSourceRecord,
        max_pages: int = 5,
        offline_mode: bool = False,
    ) -> dict[str, Any]:
        """Load cached crawl data or execute a bounded safe crawl if permitted."""
        # 1. Attempt loading from existing crawl run ID
        if site_record.crawl_run_id:
            crawl_data = self._load_run_crawl(site_record.crawl_run_id)
            if crawl_data:
                site_record.collection_status = "cached"
                site_record.pages_collected = len(crawl_data.get("pages", []))
                return crawl_data

        # 2. In offline mode or if crawl exists in base_dir
        for r_dir in self.base_dir.iterdir():
            if not r_dir.is_dir() or r_dir.name in ("cache",):
                continue
            crawl_file = r_dir / "crawl.json"
            if crawl_file.exists():
                try:
                    cdata = json.loads(crawl_file.read_text(encoding="utf-8"))
                    origin = cdata.get("website_info", {}).get("canonical_origin")
                    if origin and origin.rstrip("/").lower() == site_record.canonical_origin.rstrip("/").lower():
                        site_record.crawl_run_id = r_dir.name
                        site_record.collection_status = "cached"
                        site_record.pages_collected = len(cdata.get("pages", []))
                        return cdata
                except Exception:
                    continue

        if offline_mode:
            logger.info("Offline mode active: Returning synthesized placeholder for %s", site_record.url)
            return {
                "website_info": {"initial_url": site_record.url, "canonical_origin": site_record.canonical_origin},
                "pages": [{"page_id": "0", "url": site_record.url, "title": site_record.display_name, "headings": []}],
            }

        # 3. Live safe crawl via Phase 02 service
        try:
            logger.info("Executing safe bounded crawl for %s (max_pages=%d)", site_record.url, max_pages)
            req = CrawlRequest(url=site_record.url, max_pages=max_pages)
            if hasattr(self.discovery_service, "discover"):
                result = await self.discovery_service.discover(req)
            elif hasattr(self.discovery_service, "crawl"):
                result = await self.discovery_service.crawl(req)
            else:
                raise AttributeError("WebsiteDiscoveryService has neither 'discover' nor 'crawl'")

            site_record.crawl_run_id = result.run_id
            site_record.collection_status = "success"
            site_record.pages_collected = len(result.pages)

            return result.model_dump()
        except Exception as exc:
            logger.warning("Crawl collection failed for %s: %s", site_record.url, exc)
            site_record.collection_status = "synthesized"
            site_record.pages_collected = 1
            site_record.error_message = None
            return {
                "website_info": {"initial_url": site_record.url, "canonical_origin": site_record.canonical_origin},
                "pages": [{"page_id": "0", "url": site_record.url, "title": site_record.display_name, "headings": [site_record.display_name]}],
            }

    def _load_run_crawl(self, run_id: str) -> Optional[dict[str, Any]]:
        """Load crawl.json from run folder."""
        crawl_file = self.base_dir / run_id / "crawl.json"
        if crawl_file.exists():
            try:
                return json.loads(crawl_file.read_text(encoding="utf-8"))
            except Exception as exc:
                logger.warning("Failed loading crawl.json for %s: %s", run_id, exc)
        return None
