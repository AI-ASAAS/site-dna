"""Deterministic crawler engine orchestrating HTTP, robots.txt, sitemaps, and parsing."""

import asyncio
import time
from typing import Optional
from uuid import uuid4

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.core.security import SecurityValidationError
from site_dna.discovery.classifier import classify_page
from site_dna.discovery.evidence import EvidenceCollector
from site_dna.discovery.extractor import extract_page_content
from site_dna.discovery.frontier import IntelligentFrontier
from site_dna.discovery.http_client import (
    FetchError,
    HttpResponseData,
    InvalidContentTypeError,
    ResponseTooLargeError,
    SecureHttpClient,
)
from site_dna.discovery.robots_policy import RobotsPolicy
from site_dna.discovery.sitemap import discover_sitemaps
from site_dna.discovery.url_validator import (
    extract_canonical_origin,
    is_same_origin,
    validate_url_and_resolve,
)
from site_dna.schemas.discovery import (
    CrawlError,
    CrawlResult,
    CrawlStatistics,
    WebsiteInfo,
)
from site_dna.schemas.page import PageData

logger = get_logger("discovery.crawler")


class DeterministicCrawler:
    """Bounded, polite, SSRF-safe website crawler producing structured evidence."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        max_pages: Optional[int] = None,
        max_depth: Optional[int] = None,
        run_id: Optional[str] = None,
        client: Optional[SecureHttpClient] = None,
    ):
        self.settings = settings or get_settings()
        self.max_pages = max_pages or self.settings.crawler_max_pages
        self.max_depth = max_depth if max_depth is not None else self.settings.crawler_max_depth
        self.run_id = run_id or str(uuid4())
        self.evidence_collector = EvidenceCollector(run_id=self.run_id)
        self._custom_client = client

    async def crawl(self, initial_url: str) -> CrawlResult:
        """Execute a deterministic crawl starting from initial_url."""
        start_time = time.perf_counter()
        errors: list[CrawlError] = []
        crawled_pages: list[PageData] = []
        total_bytes = 0

        # Step 1: Normalize and resolve initial seed URL
        try:
            norm_initial, verified_ips = validate_url_and_resolve(initial_url)
            canonical_origin = extract_canonical_origin(norm_initial)
        except SecurityValidationError as e:
            logger.error("Security validation failed for initial URL '%s': %s", initial_url, e)
            return CrawlResult(
                run_id=self.run_id,
                website_info=WebsiteInfo(
                    initial_url=initial_url,
                    canonical_origin=initial_url,
                ),
                errors=[
                    CrawlError(
                        url=initial_url,
                        error_type="SecurityValidationError",
                        message=str(e),
                    )
                ],
                statistics=CrawlStatistics(
                    total_pages_crawled=0,
                    total_pages_discovered=0,
                    total_duration_ms=(time.perf_counter() - start_time) * 1000.0,
                    errors_count=1,
                ),
            )

        self.evidence_collector.add(
            source_url=initial_url,
            final_url=norm_initial,
            field_reference="site.canonical_origin",
            exact_value=canonical_origin,
            evidence_type="derived",
            extraction_method="url_normalization",
        )

        frontier = IntelligentFrontier(
            canonical_origin=canonical_origin,
            max_depth=self.max_depth,
            max_candidates=self.settings.crawler_max_candidates,
        )

        website_info = WebsiteInfo(
            initial_url=initial_url,
            canonical_origin=canonical_origin,
        )

        client_instance = self._custom_client or SecureHttpClient(
            user_agent=self.settings.crawler_user_agent,
            connect_timeout=self.settings.crawler_connect_timeout_seconds,
            read_timeout=self.settings.crawler_read_timeout_seconds,
            max_redirects=self.settings.crawler_max_redirects,
            max_html_bytes=self.settings.crawler_max_html_bytes,
        )

        async with client_instance as client:
            # Step 2: Fetch and evaluate robots.txt
            robots_policy: Optional[RobotsPolicy] = None
            if self.settings.crawler_respect_robots:
                robots_policy = await RobotsPolicy.fetch_policy(
                    client=client,
                    origin=canonical_origin,
                    user_agent=self.settings.crawler_user_agent,
                )
                website_info.robots_txt_found = robots_policy.is_present
                website_info.robots_txt_allowed = not robots_policy.fail_closed

                self.evidence_collector.add(
                    source_url=f"{canonical_origin}/robots.txt",
                    field_reference="site.robots_txt",
                    exact_value={
                        "is_present": robots_policy.is_present,
                        "status_code": robots_policy.status_code,
                        "sitemaps": robots_policy.sitemaps,
                    },
                    evidence_type="observed",
                    extraction_method="robots_fetch",
                )

            # Step 3: Discover sitemaps
            robots_sitemaps = robots_policy.sitemaps if robots_policy else []
            sitemap_result = await discover_sitemaps(
                client=client,
                origin=canonical_origin,
                robots_sitemaps=robots_sitemaps,
                max_urls=self.settings.crawler_max_candidates,
            )
            website_info.sitemap_found = sitemap_result.sitemap_found
            website_info.sitemap_urls = sitemap_result.sitemap_urls

            if sitemap_result.sitemap_found:
                self.evidence_collector.add(
                    source_url=canonical_origin,
                    field_reference="site.sitemap",
                    exact_value=sitemap_result.sitemap_urls,
                    evidence_type="observed",
                    extraction_method="sitemap_xml",
                )

            # Seed the frontier with initial URL
            frontier.add_candidate(url=norm_initial, depth=0, anchor_text="Seed")

            # Seed frontier with sitemap URLs (depth=1)
            for s_url in sitemap_result.discovered_page_urls:
                frontier.add_candidate(url=s_url, depth=1, anchor_text="Sitemap")

            # Determine politeness delay
            politeness_delay = self.settings.crawler_request_delay_seconds
            if robots_policy:
                r_delay = robots_policy.get_crawl_delay(self.settings.crawler_user_agent)
                if r_delay is not None:
                    politeness_delay = max(politeness_delay, r_delay)

            # Step 4: Crawl execution loop
            while len(crawled_pages) < self.max_pages and frontier.has_candidates():
                item = frontier.pop_next()
                if not item:
                    break

                target_url = item.url
                target_depth = item.depth

                # Check robots.txt permissions
                if robots_policy and not robots_policy.is_allowed(target_url, self.settings.crawler_user_agent):
                    logger.info("URL blocked by robots.txt: %s", target_url)
                    frontier.mark_visited(target_url)
                    continue

                # Politeness delay before fetch
                if crawled_pages:
                    await asyncio.sleep(politeness_delay)

                try:
                    resp: HttpResponseData = await client.fetch(target_url, allow_xml=False)
                    frontier.mark_visited(target_url)
                    total_bytes += len(resp.content)

                    if resp.status_code != 200:
                        errors.append(
                            CrawlError(
                                url=target_url,
                                error_type="HTTPError",
                                message=f"HTTP status {resp.status_code}",
                            )
                        )
                        continue

                    # Parse HTML
                    content = extract_page_content(resp.text, resp.final_url)

                    # Classify page
                    h1_text = content.headings[0].text if content.headings else ""
                    title_text = content.metadata.title or ""
                    category, conf = classify_page(
                        url=resp.final_url,
                        depth=target_depth,
                        title=title_text,
                        h1_text=h1_text,
                        content_snippet=content.main_content_text[:400],
                    )

                    # Update website language if found on homepage
                    if target_depth == 0 and content.metadata.language:
                        website_info.declared_language = content.metadata.language

                    # Collect evidence
                    if content.metadata.title:
                        self.evidence_collector.add(
                            source_url=target_url,
                            final_url=resp.final_url,
                            field_reference="page.title",
                            exact_value=content.metadata.title,
                            evidence_type="observed",
                            extraction_method="bs4_title",
                        )

                    if content.metadata.description:
                        self.evidence_collector.add(
                            source_url=target_url,
                            final_url=resp.final_url,
                            field_reference="page.meta_description",
                            exact_value=content.metadata.description,
                            evidence_type="observed",
                            extraction_method="meta_description",
                        )

                    if content.metadata.language:
                        self.evidence_collector.add(
                            source_url=target_url,
                            final_url=resp.final_url,
                            field_reference="page.language",
                            exact_value=content.metadata.language,
                            evidence_type="observed",
                            extraction_method="html_lang",
                        )

                    for h in content.headings:
                        if h.level == 1:
                            self.evidence_collector.add(
                                source_url=target_url,
                                final_url=resp.final_url,
                                field_reference="page.headings.h1",
                                exact_value=h.text,
                                evidence_type="observed",
                                extraction_method="bs4_heading_h1",
                            )

                    self.evidence_collector.add(
                        source_url=target_url,
                        final_url=resp.final_url,
                        field_reference="page.category",
                        exact_value={"category": category, "confidence": conf},
                        evidence_type="heuristic",
                        extraction_method="heuristic_classifier",
                    )

                    # Assemble PageData
                    page_data = PageData(
                        url=target_url,
                        final_url=resp.final_url,
                        status_code=resp.status_code,
                        depth=target_depth,
                        category=category,
                        category_confidence=conf,
                        metadata=content.metadata,
                        headings=content.headings,
                        main_content_text=content.main_content_text,
                        word_count=content.word_count,
                        navigation_links=content.navigation_links,
                        buttons=content.buttons,
                        images=content.images,
                        forms=content.forms,
                        json_ld=content.json_ld,
                    )
                    crawled_pages.append(page_data)

                    # Enqueue newly discovered internal links if within depth limit
                    if target_depth < self.max_depth:
                        for next_url, anchor_text in content.all_internal_links:
                            if is_same_origin(canonical_origin, next_url):
                                frontier.add_candidate(
                                    url=next_url,
                                    depth=target_depth + 1,
                                    anchor_text=anchor_text,
                                )

                except (SecurityValidationError, ResponseTooLargeError, InvalidContentTypeError, FetchError) as e:
                    logger.warning("Error fetching '%s': %s", target_url, e)
                    frontier.mark_visited(target_url)
                    errors.append(
                        CrawlError(
                            url=target_url,
                            error_type=type(e).__name__,
                            message=str(e),
                        )
                    )
                except Exception as e:
                    logger.exception("Unexpected exception crawling '%s': %s", target_url, e)
                    frontier.mark_visited(target_url)
                    errors.append(
                        CrawlError(
                            url=target_url,
                            error_type="UnexpectedError",
                            message=str(e),
                        )
                    )

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        stats = CrawlStatistics(
            total_pages_crawled=len(crawled_pages),
            total_pages_discovered=len(frontier.get_discovered_urls()),
            total_duration_ms=round(duration_ms, 2),
            total_bytes_fetched=total_bytes,
            errors_count=len(errors),
        )

        return CrawlResult(
            run_id=self.run_id,
            website_info=website_info,
            pages=crawled_pages,
            discovered_internal_links=frontier.get_discovered_urls(),
            evidence=self.evidence_collector.get_all(),
            errors=errors,
            statistics=stats,
        )
