# Site DNA — AI Website Intelligence Platform

**Site DNA** is an AI-powered website intelligence and strategic auditing platform developed for **ASAAS AI (أساس للذكاء الاصطناعي)**.

The platform coordinates specialized AI agents using **CrewAI Flows** to analyze web properties across design, user experience, content, technical performance, and competitive positioning.

> **Release Candidate (Phase 12 Complete):** This repository implements the complete enterprise intelligence suite across all **12 Phases**:
> 1. **Phase 01:** Foundation, Gemini 3.6 Flash LLM Factory & Diagnostics
> 2. **Phase 02:** Secure Website Discovery, Crawling & Structured Data
> 3. **Phase 03:** Headless Browser Rendering, Visual DNA & Evidence Capture
> 4. **Phase 04:** Multimodal Visual Identity & Design Intelligence
> 5. **Phase 05:** UX/UI Usability, Navigation & Conversion Patterns
> 6. **Phase 06:** Content & Marketing Intelligence & Brand Tone
> 7. **Phase 07:** Technical SEO, Core Web Vitals & Structured Data
> 8. **Phase 08:** Autonomous Competitor Intelligence & Benchmarking (Top 3)
> 9. **Phase 09:** Defensive Security, Privacy Disclosures & 8 Security Headers
> 10. **Phase 10:** Web Accessibility & W3C WCAG 2.2 (Level A & AA)
> 11. **Phase 11:** Strategic Intelligence, Conflict Resolution & 4-Wave Roadmap
> 12. **Phase 12:** Executive Synthesis, Enterprise PDF Export & Asaas UI Dashboard

---

## 1. System Requirements

- **Operating System:** Windows 10/11 (or Linux/macOS)
- **Python Version:** 3.11.x
- **Package Manager:** [uv](https://astral.sh/uv) (version 0.13+)
- **LLM Provider:** Google Gemini API (`gemini-3.6-flash`) via Google AI Studio

---

## 2. Windows Installation & Environment Setup

### Step 1: Install uv Package Manager
If `uv` is not already installed on your system, install it via PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
$env:Path = "C:\Users\" + $env:USERNAME + "\.local\bin;" + $env:Path
```

### Step 2: Install Python 3.11 Runtime
`uv` automatically downloads and manages isolated Python runtimes:

```powershell
uv python install 3.11
```

### Step 3: Clone Repository and Install Dependencies
Navigate to the project root and install dependencies into the managed virtual environment:

```powershell
# Windows PowerShell
cd site-dna
uv sync
```

Equivalent command for Command Prompt (CMD):
```cmd
cd site-dna
uv sync
```

---

## 3. Configuration & API Key Setup

1. Copy the example configuration to `.env`:
   ```powershell
   # PowerShell
   Copy-Item .env.example .env

   # CMD
   copy .env.example .env
   ```

2. Open `.env` and insert your Google AI Studio API key:
   ```env
   APP_NAME="Site DNA"
   APP_ENV=development
   APP_HOST=127.0.0.1
   APP_PORT=8000
   GEMINI_API_KEY=your_google_ai_studio_api_key_here
   GEMINI_MODEL=gemini-3.6-flash
   VISUAL_ANALYSIS_MODEL=gemini-3.6-flash
   LOG_LEVEL=INFO
   ENABLE_LIVE_LLM_TESTS=false
   ```

> **Security Guarantee:** Credentials are never printed in console output, returned in API payloads, or committed to version control. The application boots in offline mode if the key is omitted.

---

## 4. Running the Local Backend Server

Start the FastAPI application with Uvicorn:

```powershell
uv run uvicorn site_dna.api.main:app --reload --host 127.0.0.1 --port 8000
```

Once running:
- **Interactive OpenAPI Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check Endpoint:** `GET http://127.0.0.1:8000/api/v1/health`
- **Readiness Check Endpoint:** `GET http://127.0.0.1:8000/api/v1/ready`

---

## 5. Local CLI Usage

Site DNA includes a built-in CLI for environment verification and diagnostic testing.

### System Verification (Doctor)
Check Python, dependencies, configuration, and skills without consuming API tokens:

```powershell
uv run python -m site_dna.cli doctor
```

### Direct Gemini Connection Test
Verify raw Google GenAI SDK connectivity to `gemini-3.6-flash`:

```powershell
uv run python -m site_dna.cli smoke --direct --live
```

### CrewAI Foundation Smoke Agent Test
Verify end-to-end CrewAI agent and task execution:

```powershell
uv run python -m site_dna.cli smoke --crew --live
```

### Website Discovery & Crawling (Phase 02)
Execute secure, deterministic website crawling and structured data extraction:

```powershell
# Basic crawl
uv run python -m site_dna.cli discover --url "https://example.com"

# Crawl with custom constraints and save JSON artifact to runs/<run_id>/crawl.json
uv run python -m site_dna.cli discover --url "https://example.com" --max-pages 5 --max-depth 2 --save
```

### Visual Evidence Collection & Browser Rendering (Phase 03)
Execute headless Chromium browser rendering, dual-viewport screenshot collection, and computed CSS/DOM extraction on a crawled website:

```powershell
# Execute visual capture using an existing crawl run ID
uv run python -m site_dna.cli visual-capture --crawl-run-id "98b5cd6a-3225-4c00-9b75-0d13061d85f1"

# Execute visual capture directly from a crawl artifact file
uv run python -m site_dna.cli visual-capture --crawl-file "runs/98b5cd6a-3225-4c00-9b75-0d13061d85f1/crawl.json"
```

### Visual Identity AI Analysis (Phase 04)
Execute multimodal AI visual identity audit combining screenshots, computed CSS, DOM structure, and responsive observations:

```powershell
# Analyze visual run by ID
uv run python -m site_dna.cli analyze-visual --visual-run-id "vis-e6b6128de9b5" --save

# Or analyze directly via manifest file
uv run python -m site_dna.cli analyze-visual --manifest-file "runs/.../manifest.json" --save

# Force offline deterministic analysis
uv run python -m site_dna.cli analyze-visual --visual-run-id "vis-e6b6128de9b5" --offline
```

---

## 6. Automated Testing & Code Quality

### Run Offline Unit & Security Tests
Runs all unit, security, and API tests without requiring external Gemini LLM calls:

```powershell
uv run pytest -m "not integration"
```

### Run Live Integration Tests
Runs tests against live Google Gemini endpoints (requires `ENABLE_LIVE_LLM_TESTS=true` and `GEMINI_API_KEY`):

```powershell
$env:ENABLE_LIVE_LLM_TESTS="true"; uv run pytest -m "integration"
```

### Code Formatting & Linting
Run Ruff static analysis and formatting check:

```powershell
uv run ruff check .
uv run ruff format --check .
```

---

## 7. Project Structure

```
site-dna/
├── pyproject.toml              # Build & dependency configuration
├── uv.lock                     # Locked dependencies
├── .env.example                # Safe environment template
├── runs/                       # Crawl and visual JSON artifacts and screenshots
├── docs/                       # Architecture, security, and validation docs
│   ├── phase-01-validation.md
│   ├── phase-02-architecture.md
│   ├── phase-02-security.md
│   ├── phase-02-validation.md
│   ├── phase-03-preflight.md
│   ├── phase-03-architecture.md
│   ├── phase-03-security.md
│   ├── phase-03-validation.md
│   ├── phase-04-preflight.md
│   ├── phase-04-architecture.md
│   ├── phase-04-rubric.md
│   ├── phase-04-limitations.md
│   └── phase-04-validation.md
├── src/site_dna/
│   ├── cli.py                  # Local CLI (doctor, smoke, discover, visual-capture, analyze-visual)
│   ├── api/
│   │   ├── main.py             # FastAPI app initialization & route registration
│   │   └── routes/             # Health, readiness, discovery, and visual routes
│   ├── core/
│   │   ├── config.py           # Pydantic Settings & system configuration
│   │   ├── logging.py          # Structured logging & secret filter
│   │   ├── security.py         # SSRF prevention, IP validation, host checks
│   │   └── llm.py              # CrewAI LLM factory for Gemini 3.8 Flash
│   ├── discovery/              # Phase 02 Discovery Engine
│   │   ├── url_validator.py    # URL normalization and scope verification
│   │   ├── http_client.py      # Secure HTTP client (connection-time IP pinning)
│   │   ├── robots_policy.py    # RFC 9309 compliant robots.txt engine
│   │   ├── sitemap.py          # defusedxml sitemap discovery
│   │   ├── frontier.py         # Bilingual priority frontier queue
│   │   ├── extractor.py        # HTML content, heading, and element extractor
│   │   ├── classifier.py       # Heuristic page categorization
│   │   ├── evidence.py         # Traceable evidence collector
│   │   ├── crawler.py          # Deterministic crawler orchestrator
│   │   └── service.py          # WebsiteDiscoveryService facade
│   ├── visual/                 # Phase 03 Visual Evidence Engine
│   │   ├── browser_manager.py  # Playwright Chromium manager & viewport profiles
│   │   ├── browser_security.py # Browser network egress & SSRF guard
│   │   ├── renderer.py         # Page renderer & font readiness synchronization
│   │   ├── screenshots.py      # Real PNG capture, PIL sizing, SHA-256 hashes
│   │   ├── dom_extractor.py    # Semantic visible DOM extraction
│   │   ├── css_extractor.py    # Computed CSS properties extraction
│   │   ├── color_extractor.py  # Normalized palette & usage clustering
│   │   ├── typography_extractor.py # Font scale, weights, and RTL direction
│   │   ├── layout_extractor.py # Structural landmarks bounding boxes
│   │   ├── responsive.py       # Cross-viewport metrics & overflow detection
│   │   ├── evidence.py         # Auditable visual evidence recorder
│   │   ├── storage.py          # Run directories, visual.json, manifest.json
│   │   └── service.py          # VisualCollectionService orchestrator
│   ├── tools/
│   │   ├── website_discovery_tool.py # CrewAI discovery tool wrapper
│   │   └── visual_evidence_tool.py   # CrewAI visual evidence tool wrapper
│   ├── flows/
│   │   ├── foundation_flow.py  # Phase 01 Foundation Flow
│   │   ├── discovery_flow.py   # Phase 02 Discovery Flow
│   │   └── visual_evidence_flow.py # Phase 03 Visual Evidence Flow
│   ├── schemas/                # Pydantic data schemas
│   │   ├── discovery.py        # CrawlRequest, CrawlResult, WebsiteInfo
│   │   ├── visual.py           # VisualCaptureResult, Screenshots, Evidence
│   │   ├── evidence.py         # EvidenceRecord
│   │   ├── page.py             # PageData, Headings, Forms, Links
│   │   └── health.py           # Health and readiness schemas
│   └── agents/
│       └── smoke_agent.py      # Foundation smoke agent
└── tests/
    ├── conftest.py             # Fixtures and test setup
    ├── fixtures/               # HTML, XML, robots.txt, and visual showcase fixtures
    ├── security/               # SSRF, XXE, boundary, and browser egress security tests
    ├── browser/                # Playwright headless rendering & visual tests
    ├── unit/                   # Offline unit tests
    └── api/                    # FastAPI route tests
```

---

## 8. Troubleshooting & Reliability Architecture

- **Reliability Policy & Bounded Retries:**
  Direct diagnostics use a bounded retry policy to prevent cascading storms:
  - Max total attempts: 3 (1 initial + 2 retries).
  - Jittered exponential backoff: 2.0s initial, capped at 15.0s.
  - Hard overall deadline: 60.0s total budget.
  - Non-retryable errors (HTTP 400, 401, 403, 404, exhausted quota) immediately halt without wasting retries.
- **`503 UNAVAILABLE` / `504 DEADLINE_EXCEEDED` from Gemini:**
  Google AI Studio occasionally experiences transient cluster demand spikes on `gemini-3.6-flash`. The diagnostic service automatically classifies these outcomes as `SERVICE_UNAVAILABLE` or `REQUEST_TIMEOUT` and surfaces timing metrics without leaking credentials.
- **Charmap Encoding Warning in Windows Console:**
  If PowerShell displays encoding warnings during CrewAI emoji logging, set the encoding environment variable:
  ```powershell
  $env:PYTHONIOENCODING="utf-8"
  ```
- **Live Tests Skipped:**
  Ensure `ENABLE_LIVE_LLM_TESTS=true` is set and `GEMINI_API_KEY` is populated in your `.env`.

---

## 9. Implemented Scope (Phases 01–12 Complete)

- **Phase 01:** Foundation, environment validation, Gemini LLM factory (`gemini-3.6-flash`), CrewAI integration, FastAPI endpoints, CLI diagnostics, automated tests.
- **Phase 02:** Secure Website Discovery — deterministic crawler, sitemap parsing, robots.txt compliance, URL canonicalization, and discovery agents.
- **Phase 03:** Browser Rendering & Visual Evidence — headless Chromium execution, dual-viewport screenshots (desktop & mobile), PIL verification, SHA-256 hashes, computed CSS, color palettes, typography scale, spatial layout.
- **Phase 04:** AI Visual Identity Analyst — multimodal AI design evaluation, WCAG 2.1 contrast calculations, typography hierarchy with RTL support, cross-page & mobile consistency, explainable scoring rubric (0-100), evidence validator.
- **Phase 05:** UX/UI Usability & Navigation — interactive usability, CTA prominence, form ergonomics, and mobile layout.
- **Phase 06:** Content & Marketing Intelligence — value proposition audit, brand tone consistency, and conversion copywriting.
- **Phase 07:** Technical SEO & Performance — crawlability, canonical consistency, Core Web Vitals (LCP/CLS/INP), and JSON-LD schema.
- **Phase 08:** Autonomous Competitor Intelligence & Benchmarking — automated discovery of top 3 industry competitors, feature parity matrix, pricing strategy analysis, and gap detection.
- **Phase 09:** Defensive Security & Privacy — passive SSL/TLS verification, 8 HTTP security headers (CSP, HSTS, etc.), cookie security flags, and privacy policy auditing.
- **Phase 10:** Web Accessibility & WCAG 2.2 — W3C WCAG 2.2 Level A/AA conformance, semantics, keyboard navigation, contrast, and manual review tasks.
- **Phase 11:** Strategic Intelligence & Unified Roadmap — cross-agent synthesis, deduplication, architectural conflict resolution, and 4-wave prioritized action backlog.
- **Phase 12:** Executive Synthesis & Enterprise PDF Export — production-ready Arabic RTL PDF reports with Thmanyah typography, 10-axis executive scorecard, and responsive React frontend (Asaas UI kit).
