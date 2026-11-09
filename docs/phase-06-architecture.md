# Site DNA — Phase 06 Architecture: Content & Marketing Intelligence Engine

**Project:** Site DNA — بصمة الموقع  
**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Phase:** 06 — Content & Marketing Intelligence  
**Official AI Model:** Gemini 3.6 Flash (`gemini-3.6-flash`, CrewAI: `gemini/gemini-3.6-flash`)  
**Backend:** Python 3.11 + FastAPI + CrewAI Flows  

---

## 1. Executive Summary & Purpose

Phase 06 introduces the **AI-Powered Content & Marketing Intelligence Engine** into Site DNA. The system systematically audits what a website communicates to visitors, evaluating value propositions, headline clarity, product/service descriptions, CTA actionability, credibility claims, brand voice consistency, and audience alignment.

The subsystem operates strictly on **grounded evidence** collected from previous crawl (Phase 02) and visual (Phase 03) phases. It never invents business facts, guarantees, testimonials, or pricing.

---

## 2. Three-Layer Architectural Separation

The Content & Marketing Intelligence engine is organized into three decoupled layers:

```
+-------------------------------------------------------------------------------+
| Layer A: Observed Content & Source Evidence                                   |
| - Crawled Page DOM, Headings (H1-H6), Paragraphs, Lists, CTAs, Metadata       |
| - Rendered Viewport Context & Visual Hierarchy References                     |
| - Raw Source Excerpts with Exact Evidence IDs (EV-xxx)                        |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Layer B: Deterministic Linguistic & Structural Measurements (Zero-Cost)       |
| - Page Classification & Content Inventory (Word counts, reading levels)       |
| - Value Proposition & Hero Headline Clarity (Generic terms detection)         |
| - CTA Density, Placement, Context, & Friction Analysis                        |
| - Trust Claims Inventory & Onsite Cross-Referencing                           |
| - Language, Dialect, RTL Alignment, & Cross-Page Tone Consistency Checks       |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Layer C: Multimodal AI Interpretation (Gemini 3.6 Flash)                      |
| - Contextual Messaging & Semantic Nuance Audit                                |
| - Communication Friction Assessment & Content Gap Identification              |
| - Grounded Recommendation Synthesis & Fact-Preserving Copy Rewrites           |
| - Strict Quota-Aware Fail-Soft Caching & Content-Addressable Hashes           |
+-------------------------------------------------------------------------------+
```

---

## 3. Core Components Breakdown

1. **`ContentContextBuilder` (`context_builder.py`):**
   - Validates existence of crawl run and visual run artifacts.
   - Prevents path traversal vulnerabilities using regex validation (`^[a-zA-Z0-9_\-]+$`).
   - Normalizes raw crawl data into `PageContentRecord` objects and indexes all evidence items into an indexed evidence registry.

2. **`PageClassifier` (`page_classifier.py`):**
   - Heuristically categorizes pages into `home`, `about`, `services`, `products`, `pricing`, `contact`, `blog`, `faq`, or `other`.

3. **`ContentInventoryBuilder` (`content_inventory.py`):**
   - Computes structural distributions: total pages, total words, reading time, missing meta tags, image alt coverage, heading hierarchy completeness.

4. **Specialized Analyzers:**
   - **`ValuePropositionAnalyzer` (`value_proposition.py`):** Extracts H1/meta descriptions, identifies core benefits, claimed differentiators, and target audience. Flags generic greetings or missing value statements.
   - **`MessagingAnalyzer` (`messaging_analyzer.py`):** Evaluates headline clarity, jargon overload, and unsubstantiated absolute claims ("الأفضل", "#1").
   - **`ServiceContentAnalyzer` (`service_content.py`):** Assesses whether services/products have adequate descriptions, feature breakdowns, and clear next steps.
   - **`CTAContentAnalyzer` (`cta_analyzer.py`):** Categorizes CTAs (primary vs. secondary), audits generic labels ("اضغط هنا"), checks action clarity, and flags missing hero CTAs.
   - **`TrustAnalyzer` (`trust_analyzer.py`):** Compiles `TrustClaimRecord` entries, labels verification state (`observed_only`, `supported_onsite`), and flags sensitive/unsupported claims.
   - **`VoiceAnalyzer` (`voice_analyzer.py`):** Detects primary language (Arabic, English, bilingual), identifies Arabic dialect (Saudi/Gulf, Egyptian, Levantine, Maghrebi), audits RTL alignment, and measures tone consistency.
   - **`ConsistencyAnalyzer` (`consistency_analyzer.py`):** Checks cross-page naming coherence, terminology harmony, and handles single-page neutral evaluations.
   - **`ContentGapAnalyzer` (`content_gaps.py`):** Identifies systemic communication gaps (unclear offerings, missing pricing context, missing contact channels).

5. **`ContentEvidenceValidator` (`evidence_validator.py`):**
   - Rigorously validates all AI-generated findings against ground-truth DOM content and excerpts. Quarantines unverified hallucinated claims.

6. **`ContentMultimodalAdapter` (`multimodal_adapter.py`):**
   - Manages communication with Google AI Studio using Gemini 3.6 Flash (`gemini-3.6-flash`).
   - Features prompt-injection defense with untrusted XML block encapsulation (`<untrusted_content>`).
   - Content-addressable SHA-256 caching (`model_name:content_v1:payload_hash`).
   - Graceful fail-soft handling for Google Free Tier daily quotas.

7. **`ContentScoringEngine` (`scoring.py`):**
   - Executes the 7-dimension weighted rubric (100% total).
   - Handles neutral dimensions gracefully without penalizing incomplete site scopes.

8. **`ContentRecommendationEngine` (`recommendations.py`):**
   - Generates prioritized (P1-P3) actionable content recommendations with effort estimates and validation criteria.

9. **`CopyProposalsEngine` (`copy_proposals.py`):**
   - Drafts grounded copy rewrite proposals that preserve verified facts and explicitly highlight inserted strategic guidance.

10. **`ContentReportBuilder` (`report_builder.py`):**
    - Persists structured JSON outputs (`analysis.json`, `content-inventory.json`, `messaging-findings.json`, `recommendations.json`, `copy-proposals.json`, `claims-inventory.json`, `evidence-index.json`, `execution-summary.json`) and renders the 14-section Arabic Markdown audit (`report.md`).

---

## 4. Framework Integration

- **CrewAI Flow:** `ContentMarketingFlow` orchestrates context building, deterministic analysis, and Gemini 3.6 Flash interpretation through `@start()` and `@listen()`.
- **CrewAI Agent:** `ContentMarketingAgent` configured with `model="gemini/gemini-3.6-flash"`.
- **CrewAI Tool:** `ContentMarketingTool` wraps `ContentMarketingAnalysisService`.
- **FastAPI Endpoint:** `POST /api/v1/analysis/content-marketing` with bearer authentication, path-traversal safety, and rate-limiting.
- **CLI Subcommand:** `site-dna analyze-content` supporting `--crawl-run-id`, `--visual-run-id`, `--offline`, `--deterministic-only`, and `--save`.
