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

## Phase 4 — Visual Identity Extractor

- **Browser manager reuse.** The spec's `services/browser.py` is added as the new shared entry point. Its `BrowserManager` subclasses the existing `site_dna.visual.browser_manager.BrowserManager` so Playwright lifecycle, context profiles, and shutdown logic are not duplicated. Phase 5 will reuse the same service.
- **Request guard.** `BrowserRequestGuard` validates every browser request with `validate_url`, not a parallel DNS check. It caches one decision per `(scheme, host, port)`, allows `data:`, `blob:`, and `about:` without network validation, blocks WebSocket/EventSource resource types, counts blocked requests, and appends bounded warnings. It is attached through the existing context-level `route("**/*", ...)` hook, which covers the spec's per-page route requirement.
- **Collector.** `analyzers/js/collect_styles.js` is a self-contained function evaluated with `page.evaluate`. It samples visible elements up to 5,000, records the first opaque ancestor background as `effectiveBg`, separates button and link samples, captures the first three headings per level, reads `:root` custom properties, and lists `document.fonts` faces.
- **Color parsing.** `analyzers/color_utils.py` parses `rgb()`, `rgba()`, hex, `hsl()`, `hsla()`, `color(srgb ...)`, and a small named-color table. Semi-transparent colors are composited over `effectiveBg`; fully transparent colors are dropped. Box-shadow colors are intentionally not sampled, which is why `#FF00FF` never enters the palette.
- **Role heuristics.** Backgrounds are ranked by visible area, text by text length, and borders/SVG by count. Primary is the highest-weight non-neutral color observed on buttons/links, falling back to all non-neutral colors. Secondary excludes hues within 20 degrees of primary. All role records are marked `source="inferred"` and `roles_method` records the heuristic.
- **Typography.** Font families are ranked by summed visible area. The primary family is the top entry; fallbacks are parsed from the declared font stack; `loaded` comes from `document.fonts`. Size and weight histograms and H1/H2/H3 computed styles are returned as observed evidence.
- **Fixture.** `tests/fixtures/visual/palette.html` is served locally. It declares a `@font-face` family with a local source so tests remain offline and deterministic while still exercising the font-stack parsing and `document.fonts` path.
- **Screenshot.** `VisualIdentity.screenshot` stays `None` in Phase 4; Phase 5 fills it in the orchestrator.

## Phase 5 — Screenshot Engine

- **Result shape.** `ScreenshotResult` wraps the `FileRef` and the capture metadata (`document_height`, `viewport`, `truncated`, `scrolled_steps`, optional `base64`). The orchestrator copies `result.data.file` into `VisualIdentity.screenshot`; `screenshot.py` never mutates visual identity itself.
- **Browser reuse.** `ScreenshotEngine` uses `services/browser.py` and the same `BrowserRequestGuard` as Phase 4. It opens its own browser for now; Phase 9 will share one context between visual identity and screenshot capture.
- **Viewport.** Capture uses the existing desktop profile (`visual_desktop_width`/`visual_desktop_height`, default 1440x900).
- **Scrolling.** The engine scrolls in viewport-height steps with 120 ms pauses, up to 40 steps. It stops when the bottom is reached without further growth or when the measured document height reaches the configured cap. Lazy images are switched from `loading="lazy"` to `loading="eager"` before scrolling, then the engine waits briefly for `document.fonts.ready` and image completion.
- **Height cap.** `scan_screenshot_max_height` defaults to 16,000 px. Pages taller than the cap are captured with a clip at the cap and reported as `truncated=true`; the capture never fails solely because the page is tall.
- **PNG metadata.** Width and height are read directly from the PNG IHDR chunk, so no image decode is required. The file reference records bytes and SHA-256; the path is `{storage_dir}/{scan_id}/homepage.png`.
- **Embedding.** `base64` is populated only when `embed_images=True`; the default report keeps file references only.
- **Fixtures.** `tests/fixtures/site_lazy/` uses SVG images with `loading="lazy"` and a recording HTTP server verifies both were fetched. `tests/fixtures/site_tall/` is 20,000 px tall to exercise clipping.

## Phase 6 — PageSpeed Insights Client

- **Fixed endpoint.** Requests go to `https://www.googleapis.com/pagespeedonline/v5/runPagespeed`. The submitted target URL was already validated in Phase 2, so the client does not repeat SSRF validation for the Google call.
- **Retries.** Tenacity retries 429, 5xx, and timeouts up to three retries (four attempts total) with exponential backoff. A 400 is returned immediately and never retried.
- **Reason codes.** Persistent 429 is `quota_exceeded`; timeouts are `timeout`; Google's `FAILED_DOCUMENT_REQUEST` / cannot-fetch messages are `invalid_url_or_unreachable`; malformed JSON and unusable payloads are `bad_response`; other non-2xx responses are `http_error`; a 403 without a configured key is `missing_api_key`.
- **Missing key.** An unconfigured `PSI_API_KEY` does not fail the request. It adds a warning because PSI can answer unauthenticated requests, subject to stricter quotas.
- **Field data.** URL-level CrUX metrics are used first, with per-metric fallback to `originLoadingExperience`. The result is labeled `crux_url` only when every field came from the URL response; any origin fallback labels it `crux_origin`. CrUX CLS percentiles are divided by 100 to normalize the API's scaled value.
- **Lab data.** Numeric Lighthouse values are read from `numericValue`. `displayValue` is available for diagnostics, while the lab output contract keeps the numeric millisecond/CLS fields.
- **Diagnostics.** Following the spec, numeric/informative audits with score < 0.9 and table/list audits with items are diagnostics. Unknown insight-style audit shapes are included with whatever `id/title/score/displayValue` fields exist. Core metric audits therefore also appear as diagnostics when their score is below 0.9.
- **Extra Lighthouse metadata.** `StrategyPerformance` carries `fetch_time`, `final_url`, and `runtime_errors` in addition to the requested `lighthouse_version`, so the parsed values are not discarded.
- **Logging.** Request logs include the target URL with any `key` query parameter removed. The `httpx` logger is set to WARNING and carries `SensitiveDataFilter`, so the API key cannot appear in captured logs.
- **INP note.** `Performance.notes` always contains the explanation that INP requires CrUX field data and is not produced by a Lighthouse lab run.
- **Fixtures.** `recorded_429.json` is a real PSI quota response captured from the live endpoint. The success fixtures are synthetic responses shaped like the PSI v5 schema because the unauthenticated quota for this environment is zero. `scripts/record_psi_fixture.py` is the live-only recorder for replacing them with real success responses when a key is available. `respx` is a dev dependency used to mock the endpoint in tests.

## Phase 7 - Technical SEO Analyzer

- **Package location.** The spec's SEO package is `src/site_dna/analyzers/seo/`, separate from the older `site_dna.analysis.technical_seo` platform code. Rule IDs, thresholds, and docstrings live in `rules.py`; the analyzer is in `analyzer.py`; sitemap parsing is in `sitemap.py`.
- **Page inputs.** Page-level checks use `PageData.raw_html` and the already-extracted `title`, `headings`, `images`, `links`, and `language` fields. `raw_html` remains excluded from `report.json`.
- **X-Robots-Tag.** `PageData` now carries an internal `http_headers` mapping (also excluded from reports) so the analyzer can honor `X-Robots-Tag` when a renderer supplies response headers. The current Crawl4AI renderer does not populate it, so header-only directives are best-effort until the Phase 9 pipeline wires response headers through.
- **Severity.** Missing title, meta description, H1, alt text, language, and viewport are failures. Length, canonical, Open Graph, meta-robots, hierarchy, robots.txt, sitemap, redirect, and duplicate-content findings are warnings. Broken links and 4xx/5xx crawled pages fail the relevant site check. Findings are never raised as module errors.
- **Sitemap.** Declared robots.txt sitemaps are tried before `/sitemap.xml`. Sitemap indexes are followed up to three levels, bounded to 50,000 URLs and 10 MB per document; gzip documents are decompressed defensively even though httpx normally decodes them.
- **Broken links.** Checks are internal-first, deduplicated with `canonicalize_url`, capped at 200 targets, and run with concurrency 10. Internal targets disallowed by robots.txt are skipped. Transport errors and 4xx/5xx responses are broken links.
- **Duplicates.** Duplicate titles are grouped case-insensitively after trimming; duplicate content is grouped by the Phase 3 `html_sha256`.
- **Summary.** `SeoSummary` counts every check, including `not_available`. `SeoAnalysis.issues` is the flat list of only `failed` and `warning` checks, matching the Phase 7 contract.
