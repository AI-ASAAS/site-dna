# Site DNA — Phase 12: Technical Limitations & Disclosures

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Phase:** 12 — Limitations and Boundaries  

---

## 1. Upstream AI Rate Limits & Quotas
- Site DNA relies on **Gemini 3.6 Flash** (`gemini-3.6-flash`).
- When operating under the Google AI Studio Free Tier, daily request limits may be reached (HTTP 429). Site DNA handles this deterministically by entering fail-soft fallback mode, generating fully structured, mathematically verified reports using deterministic rule-based algorithms rather than retrying indefinitely or fabricating synthetic outputs.

## 2. Dynamic Single Page Applications (SPAs)
- Client-side websites requiring complex multi-step user authentication (e.g., CAPTCHAs, SMS 2FA, biometric authentication) cannot be crawled beyond the public barrier.
- Single-page applications with infinite scroll or delayed lazy loading require adequate timeout parameters (`--timeout-sec 45`) during visual capture.

## 3. PDF Font Inlining
- To ensure 100% offline self-containment and eliminate SSRF, all font files are embedded as base64 WOFF2 strings. This increases the raw HTML size by approximately 1.1 MB, but ensures fast (sub-second) Chromium PDF generation with zero network lookups.

## 4. Legal & Regulatory Non-Certification
- Site DNA reports are rigorous technical diagnostic audits. They do not constitute official legal certifications of compliance under GDPR, Saudi PDPL, or official W3C accessibility certification bodies.
