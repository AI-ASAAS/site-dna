# Site DNA — Phase 07 Pre-flight Audit & Evidence Readiness

**Project:** Site DNA — بصمة الموقع  
**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Phase:** 07 — Technical SEO & Website Performance Intelligence  
**Target Model:** Gemini 3.6 Flash (`gemini-3.6-flash`, CrewAI: `gemini/gemini-3.6-flash`)  
**Audit Date:** 2026-11-07  

---

## 1. Pre-flight A — Phase 06 Gemini Execution Proof

Audit of Run `98b5cd6a-3225-4c00-9b75-0d13061d85f1` (Analysis Run `cnt-601bc72f7aa0`):

| Check Item | Verified Value | Evidence Reference |
|---|---|---|
| **Model Configured & Used** | `gemini-3.6-flash` | `analysis.json:489` |
| **Provider Request Count** | `1` call | `analysis.json:488` |
| **Response & Analysis Status** | `completed` | `analysis.json:8`, `analysis.json:491` |
| **Execution Duration** | `6,451.5 ms` | `analysis.json:490` |
| **AI Generated Findings** | `CF-AI01` ("Explicit Non-Service Disclaimer")<br>`CF-AI02` ("Absence of Structural Headings") | `analysis.json:424`, `analysis.json:444` |
| **Grounding & Evidence Matching** | Validated against DOM excerpts (`d9653d56...`, `987d82b4...`) | `analysis.json:448-450` |
| **Fail-Soft Mechanism** | Tested and verified on transient quota limits with fallback | `multimodal_adapter.py:195-202` |

**Conclusion:** Real Gemini 3.6 Flash reasoning was successfully executed, verified, and ground-truth validated in Phase 06.

---

## 2. Pre-flight B — Scoring Calibration & Limitations

Review of Phase 06 scoring calculations:
- `example.com`: 90.7 / 100
- `crawl-a` (3 pages): 98.0 / 100

### Findings & Caveats for Phase 07:
1. In Phase 06, dimensions without negative findings (or where content was absent, e.g. `service_content` for non-commercial sites) defaulted to a base score of 100.
2. In single-page websites, cross-page consistency was neutrally unassessed.
3. **Application to Phase 07 Technical SEO:**
   - Technical SEO cannot assume that missing data implies perfection.
   - If a website does not provide performance data or sitemaps, the dimension must be marked `not_assessed` or evaluated only on available signals.
   - An overall score must **only** be calculated when minimum evidence coverage is met (e.g. at least crawlability, indexability, and metadata are evaluated). Otherwise, `overall_score: null`.

---

## 3. Pre-flight C — Grounded Copy Integrity

Artifact Review (`copy-proposals.json` and `analysis.json:461-479`):
- `PRP-01`: Proposed rewrite for `example.com` hero section explicitly cited the exact observed text (`"This domain is for use in documentation examples without needing permission..."`).
- Flagged with `is_suggestion: true` and listed missing facts under `information_requiring_confirmation`.
- Zero unverified facts, prices, or client testimonials were invented.

---

## 4. Pre-flight D — Technical Evidence Availability Audit

Audit of existing data collected in Phase 02 (`crawl.json`) and Phase 03 (`visual.json`):

| Technical Field | Status in Existing Subsystems | Notes & Recommendations for Phase 07 |
|---|:---:|---|
| **HTTP Status Code** | `AVAILABLE` | Captured in `pages[].status_code`. |
| **Response Headers** | `PARTIALLY_AVAILABLE` | Content-Type, charset, and server metadata captured in evidence records; raw full headers dictionary should be safely parsed when present. |
| **Canonical Link** | `AVAILABLE` | Captured in `pages[].metadata.canonical_url` and `site.canonical_origin`. |
| **Robots Meta Tag** | `AVAILABLE` | Captured in `pages[].metadata.robots_meta`. |
| **Robots.txt Policy** | `AVAILABLE` | Captured in `website_info.robots_txt_found`, `robots_txt_allowed`, and `site.robots_txt` evidence. |
| **Sitemap URLs** | `AVAILABLE` | Captured in `website_info.sitemap_urls` and `website_info.sitemap_found`. |
| **HTML Language (`lang`)** | `AVAILABLE` | Captured in `pages[].metadata.language` and `website_info.declared_language`. |
| **Structured Data (JSON-LD)** | `AVAILABLE` | Captured in `pages[].json_ld` (list of raw dictionaries). |
| **Viewport Meta** | `AVAILABLE` | Captured in `pages[].metadata.viewport`. |
| **Redirect Information** | `PARTIALLY_AVAILABLE` | Captured via `url` vs `final_url` and status code; intermediate multi-hop redirect chains need dedicated evaluation in Phase 07. |
| **Rendered Head & DOM** | `AVAILABLE` | Captured in Phase 03 Playwright DOM elements, attributes, and CSS computed records. |
| **Network Timing Information** | `PARTIALLY_AVAILABLE` | Total crawl duration and Playwright capture durations are captured; page-level laboratory performance timing will be gathered via bounded Phase 07 collector. |
| **Core Web Vitals** | `PARTIALLY_AVAILABLE` | CLS and layout shifts are observable locally; LCP and INP require strict separation of lab, local, and field sources. |

---

## 5. Security Pre-flight Gate

- RFC 9309-compliant robots parsing: Reused from Phase 02.
- DefusedXML and safe JSON-LD parsing: Required to prevent XML entity expansion (XXE) and code execution.
- Bounded performance measurements: Strict timeout (max 15s per page), max concurrency (1), and restricted network destinations.
- Untrusted website content defense: Encapsulation in `<untrusted_content>` tags.
- Read-only storage policy: Output written solely to `runs/<crawl_run_id>/analysis/technical-seo/<seo_run_id>/`.
