# Site DNA — Phase 09 Architecture: Security, Privacy & Trust Intelligence

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Phase:** 09 — Security, Privacy & Digital Trust Intelligence  
**Official AI Model:** Gemini 3.6 Flash (`gemini-3.6-flash`, CrewAI: `gemini/gemini-3.6-flash`)  
**Status:** Production-Ready & Validated  

---

## 1. Architectural Overview

Phase 09 introduces the **Security, Privacy & Digital Trust Intelligence Engine** into Site DNA.
The architecture follows a strictly **passive, evidence-based, non-intrusive** design. It audits observable security configurations and privacy posture from previously collected crawl and visual data without conducting active vulnerability scans, port scans, or exploit payloads.

```
                    ┌──────────────────────────────────────────────┐
                    │               Crawl & DOM Data               │
                    │      (crawl.json, manifest.json, DOM)        │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │     SecurityPrivacyContextBuilder            │
                    │   - Path Traversal & SSRF Defense            │
                    │   - Cookie Value Redaction                   │
                    │   - Origin Isolation & Header Sanitization   │
                    └──────────────────────┬───────────────────────┘
                                           │
         ┌─────────────────────────────────┴─────────────────────────────────┐
         │                                                                   │
         ▼                                                                   ▼
┌─────────────────────────────────┐                         ┌─────────────────────────────────┐
│     Deterministic Analyzers     │                         │   Privacy & Trust Analyzers     │
│  - HTTPSAnalyzer                │                         │  - PrivacySignalsAnalyzer       │
│  - TLSObservationsAnalyzer      │                         │  - ConsentObservationsAnalyzer  │
│  - SecurityHeadersAnalyzer      │                         │  - TrustSignalsAnalyzer         │
│  - CSPAnalyzer                  │                         └────────────────┬────────────────┘
│  - CookieSecurityAnalyzer       │                                          │
│  - MixedContentAnalyzer         │                                          │
│  - BrowserIsolationAnalyzer     │                                          │
│  - ClientSideObsAnalyzer        │                                          │
│  - ThirdPartyResourceAnalyzer   │                                          │
└────────────────┬────────────────┘                                          │
                 │                                                           │
                 └─────────────────────────┬─────────────────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │            RiskAssessmentEngine              │
                    │   - Synthesizes Domain Findings              │
                    │   - Maps Severity (Critical, High, Med, Low) │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │          SecurityEvidenceValidator           │
                    │   - Anti-Hallucination Provenance Check      │
                    │   - Strict Verification State Enforcement    │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │           SecurityScoringEngine              │
                    │   - 6 Weighted Scoring Dimensions (100%)     │
                    │   - Deterministic Deduction Rubric           │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │        SecurityPrivacyFlow (CrewAI)          │
                    │   - Official Model: gemini-3.6-flash         │
                    │   - Defensive AI Interpretation              │
                    │   - Remediation Playbook Synthesis           │
                    └──────────────────────┬───────────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────────────┐
                    │             SecurityReportBuilder            │
                    │   - Bilingual Reports (Arabic / English)     │
                    │   - Markdown & JSON Artifact Generation      │
                    └──────────────────────────────────────────────┘
```

---

## 2. Component Breakdown

| Module | Responsibility |
|---|---|
| `context_builder.py` | Extracts normalized page records, performs strict header redaction and boundary checks. |
| `https_analyzer.py` | Validates scheme enforcement, HTTP-to-HTTPS redirect chains, and mixed transport. |
| `tls_observations.py` | Evaluates observable TLS certificate chain and protocol versions passively. |
| `security_headers.py` | Evaluates 8 critical HTTP headers (HSTS, CSP, X-Frame, X-Content-Type, Referrer-Policy, Permissions-Policy, Cross-Origin-Opener-Policy, Cross-Origin-Resource-Policy). |
| `csp_analyzer.py` | Parses Content Security Policy directives, unsafe-inline/unsafe-eval keywords, and script origins. |
| `cookie_analyzer.py` | Checks Secure, HttpOnly, and SameSite attributes while strictly redacting all cookie values. |
| `mixed_content.py` | Detects passive and active mixed content HTTP resources on HTTPS pages. |
| `browser_isolation.py` | Assesses framing protection (X-Frame-Options, frame-ancestors) and cross-origin isolation. |
| `client_side_observations.py` | Scans for external script sprawl, vulnerable inline script patterns, and public source maps. |
| `third_party_resources.py` | Categorizes external CDNs, analytics, trackers, ads, and widgets by risk tier. |
| `privacy_signals.py` | Detects privacy policies, data collection notices, and contact disclosure endpoints. |
| `consent_observations.py` | Observes cookie consent banners, CMP integrations, and opt-out controls. |
| `trust_signals.py` | Identifies security.txt, vulnerability disclosure contacts, certifications, and trust badges. |
| `risk_assessment.py` | Aggregates observable evidence into standardized `SecurityFinding` objects with CVSS-like severity. |
| `evidence_validator.py` | Enforces evidence provenance, rejecting any finding without matching verifiable evidence IDs. |
| `scoring.py` | Calculates mathematically normalized scores (0-100) across 6 weighted dimensions. |
| `recommendations.py` | Generates prioritized remediation actions (P1 Immediate, P2 Planned, P3 Best Practice). |
| `report_builder.py` | Generates comprehensive bilingual Markdown and JSON audit reports. |
| `service.py` | Master orchestrator coordinating all analyzers, flow execution, and disk persistence. |

---

## 3. Official AI Model Integration

- **Model Identifier:** `gemini-3.6-flash`
- **CrewAI Binding:** `gemini/gemini-3.6-flash`
- **Provider:** Google AI Studio
- **Role:** Synthesizes qualitative risk commentary, impact explanation, and remediation advice grounded exclusively on deterministic findings.
- **Fail-Safe Mechanism:** In the event of API rate-limiting or quota exhaustion, deterministic evaluation completes 100% of scores, headers, and findings without interruption.
