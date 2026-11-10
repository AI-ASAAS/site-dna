# Decisions & Assumptions

This file records every assumption made while implementing the Website Intelligence MVP (Phases 1-9).

## Phase 1 — Project Structure

- **Layout adaptation.** The repository already contained the `site_dna` platform with its own Phases 1-12. Phase 1 of the Website Intelligence MVP is implemented inside that package instead of creating a parallel `website_intel/` tree. The new report contracts live in `src/site_dna/models/`, the timing helper in `src/site_dna/services/timing.py`, and the scan entry point in `src/site_dna/scan.py`.
- **CLI framework.** The existing CLI uses `argparse`. The `scan` subcommand extends that parser rather than introducing Typer.
- **Settings naming.** Existing `crawler_*` settings are left untouched. MVP defaults are exposed as `scan_*` fields (for example `scan_max_pages`) to avoid collisions with the existing crawler configuration.
- **Placeholder scan status.** A Phase 1 report has every module `skipped`, which the Phase 8 status rules do not cover. It is recorded as `scan_status="completed"` until the real pipeline computes status from module outcomes.
- **Permission.** `--i-have-permission` is mandatory. Without it the CLI exits with code 2 before any network access or file write. The report records `permission_attested: true`.
- **Logging.** The existing `setup_logging` (stdout) is preserved for the current CLI. `setup_scan_logging` adds JSON-lines output to `storage/{scan_id}/scan.log` plus human-readable stderr, and both handlers apply the secret-redaction filter. In addition to API-key patterns, `key=` query parameters are redacted.
- **Lazy Gemini import.** The CLI imports the Gemini diagnostics service only inside `run_smoke`, so `scan` and its tests do not require the Google SDK.
- **Lint baseline.** Pre-existing `ruff` findings in unrelated modules were fixed mechanically (unused imports, import order, f-strings, one whitespace line, and dead assignments) so `ruff check .` passes for the phase.
- **Null/array policy.** The report models encode the shared rule: unknown values default to `None`, and every list field defaults to an empty list.

## Phase 2 — URL Validator and Crawler

- **Module mapping.** The spec names `services/security.py`, `services/http_client.py`, and `crawler/{robots,crawl_manager,categorizer}.py`. These are implemented as new modules inside the existing `site_dna` package. The pre-existing `site_dna.discovery.*` crawler is left untouched so its tests and API remain stable; the Phase 2 modules are additive.
- **Crawl4AI fallback.** Crawl4AI is not a dependency of this repository. The spec explicitly allows implementing our own BFS loop when Crawl4AI cannot enforce the required limits and per-URL validation, so `crawler/crawl_manager.py` is a deterministic BFS loop over `SafeHttpClient`.
- **Registrable domain.** `tldextract` is used with `suffix_list_urls=()` so no network fetch is needed at runtime; it falls back to the exact host when a suffix is unknown (for example reserved `.test` hosts).
- **robots.txt status.** A 2xx response is `found`; a 4xx response is `missing` and allows all; a 5xx or network failure is `error`, which also allows all but records a warning. This matches the Phase 2 spec rather than the older `discovery.robots_policy` fail-closed behavior.
- **Redirects and DNS rebinding.** `SafeHttpClient` re-validates every redirect hop with `validate_url`. The client does not pin the validated IP in this phase, so a DNS-rebinding race between validation and connection remains possible; this is the documented residual risk allowed by the spec. The existing `discovery.http_client` still provides connect-time IP pinning for the older crawler.
- **Retry policy.** `tenacity` retries timeouts and 5xx responses twice with exponential backoff. 4xx responses are returned without retry.
- **Rate limiting.** Per-host token buckets are keyed by hostname; `per_host_rps` defaults to the `scan_per_host_rps` setting when the manager is wired into a scan.
- **Private hosts.** `validate_url` honors `ALLOW_PRIVATE_HOSTS` only through `Settings.private_hosts_allowed()`, which additionally requires `APP_ENV=test`.
- **Canonicalization.** Fragments are dropped, tracking parameters (`utm_*`, `gclid`, `fbclid`, and similar) are removed, query parameters are sorted, default ports are removed, and trailing slashes are normalized except for the root path.
- **Crawler output.** `DiscoveredUrl` records `url`, `depth`, `discovered_from`, heuristic `category`, and a status of `fetched`, `skipped_robots`, `skipped_scope`, `skipped_limit`, or `failed`.

## Phase 3 — Content Extractor

- **Package location.** The spec's `analyzers/` package is created as `src/site_dna/analyzers/`. The pre-existing `site_dna.analysis` package is left untouched for the older platform.
- **Crawl-to-extractor contract.** `CrawlManager` stays discovery-only and returns `DiscoveredUrl` records. `ContentExtractor` receives those records and renders each fetched URL through Crawl4AI, matching the Phase 3 wording "for each crawled URL, obtain rendered HTML and Markdown from Crawl4AI". This avoids retaining page bodies in the Phase 2 crawl result while still preventing an extra discovery pass.
- **Crawl4AI version and browser.** `crawl4ai==0.9.5` is used with Playwright Chromium. Its default strategy is `AsyncPlaywrightCrawlerStrategy`; the optional Patchright browser is not required. Playwright Chromium is installed locally.
- **selectolax backend.** `selectolax==1.0.2` deprecates the Modest backend, so parsing uses `selectolax.lexbor.LexborHTMLParser`.
- **Noise removal.** Excluded tags and selector blocklists live in `analyzers/noise.py` as constants. They are passed to Crawl4AI and also applied locally before counting headings, links, and images so extraction is deterministic. The approach is documented as heuristic.
- **Raw HTML retention.** `PageData.raw_html` is an internal field with `exclude=True`; it is available to later analyzers (SEO) without appearing in `report.json`.
- **Non-HTTP links.** `javascript:`, `mailto:`, `tel:`, and `data:` links are dropped from `PageData.links` and counted in the internal, non-serialized `non_http_link_counts` field.
- **Markdown storage.** Markdown longer than `inline_markdown_limit` (default 100,000 chars) is written to `storage/{scan_id}/pages/{n}.md`; `PageData.markdown` is `None` and `PageData.markdown_file` points to the file.
- **Fit Markdown fallback.** When Crawl4AI's fit Markdown is empty but raw Markdown is not, the extractor records raw/fit character counts in module warnings and uses the raw Markdown.
- **Dependency lock.** `uv.lock` was regenerated after adding `tldextract`, `crawl4ai`, and `selectolax`.

