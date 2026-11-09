# Site DNA — Phase 06: Operational Scope, Limitations & Truth Boundaries

**Project:** Site DNA — بصمة الموقع  
**Subsystem:** Content & Marketing Intelligence Engine  
**Version:** 1.0.0  

---

## 1. Automated Analysis vs. Human Strategy

Site DNA's Content & Marketing Intelligence engine is an **automated diagnostic system**, not an autonomous marketing agency. It is designed to rapidly audit visible, published website communication against industry copywriting standards, conversion clarity heuristics, and structural linguistics.

Strategic decisions regarding corporate branding, legal compliance, or pricing strategy require human validation and market context.

---

## 2. Core Operational Limitations

1. **Absence of Web Analytics & Conversion Telemetry:**
   - The engine does not have access to Google Analytics, Mixpanel, heatmaps, or user session recordings.
   - It cannot measure actual bounce rates, click-through rates, or conversion figures.
   - Predictions regarding user behavior are based strictly on observed friction and proven UX/copywriting heuristics.

2. **Published Claims vs. Independent Truth:**
   - Any statement found on a website (e.g. "Trusted by 10,000 companies", "#1 in Saudi Arabia") is inventoried strictly as a **source claim**, never as an independently verified truth.
   - The engine marks these claims as `observed_only` or `supported_onsite` (if case studies or testimonials exist within the crawled pages).

3. **Strict Fact-Preservation in Copy Rewrite Proposals:**
   - When suggesting improved headlines or CTA copy, the system is strictly prohibited from inventing new business facts, imaginary features, false guarantees, or speculative pricing.
   - Rewrites focus on clarity, action-orientation, and readability using only verified facts extracted from the page.

4. **Multi-Page Scope Boundaries:**
   - The engine analyzes only the pages discovered and captured during Phase 02 and Phase 03. Uncrawled pages, gated portals behind logins, or hidden dynamic content (SPA pages without server-side rendering or deep links) fall outside the analysis scope.

5. **AI Provider Availability & Fail-Soft Behavior:**
   - In environments where Google AI Studio daily quotas are exceeded or network connectivity to Gemini is severed, the engine gracefully transitions to **fail-soft deterministic mode**.
   - Deterministic structural findings, inventory statistics, and rubric scoring are fully preserved, ensuring system resilience.
