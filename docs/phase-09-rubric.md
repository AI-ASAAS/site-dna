# Site DNA — Phase 09 Scoring Rubric & Weighting Architecture

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Phase:** 09 — Security, Privacy & Digital Trust Intelligence  
**Rubric Version:** `1.0.0`  

---

## 1. Weighting Architecture (Sum = 100%)

The overall Security Posture Score ($S \in [0, 100]$) is computed as the weighted sum of six orthogonal security dimensions:

$$S = \sum_{i=1}^{6} w_i \times D_i$$

| Dimension | Key | Weight ($w_i$) | Core Objective |
|---|---|---|---|
| **Security Headers** | `security_headers_score` | **25%** | Verifies protective HTTP response headers preventing common web attacks. |
| **Transport & Encryption** | `https_transport_score` | **20%** | Measures HTTPS ubiquitous adoption, valid certificates, and HSTS enforcement. |
| **Cookie Security** | `cookie_security_score` | **15%** | Evaluates flags (`Secure`, `HttpOnly`, `SameSite`) on all observed cookies. |
| **Browser Isolation & Sandbox** | `client_side_resources_score` | **15%** | Checks clickjacking mitigation, CSP, SRI hashes, and cross-origin boundaries. |
| **Privacy & Consent Governance**| `privacy_consent_score` | **15%** | Analyzes privacy disclosure availability, contact info, and cookie banners. |
| **Digital Trust & Transparency** | `digital_trust_score` | **10%** | Evaluates `security.txt`, vulnerability disclosure, and trust credentials. |

---

## 2. Deduction Rubric by Dimension

### A. Security Headers (25 pts max)
- Baseline: 100 points
- Missing HSTS: -20 pts
- Missing Content-Security-Policy: -25 pts
- Missing X-Frame-Options (without CSP frame-ancestors): -15 pts
- Missing X-Content-Type-Options: -15 pts
- Missing Referrer-Policy: -10 pts
- Missing Permissions-Policy: -10 pts
- Missing COOP / CORP: -5 pts

### B. Transport & HTTPS (20 pts max)
- Baseline: 100 points
- Any unencrypted HTTP page accessed without 301 redirect: -40 pts
- Mixed active content (scripts/iframes over HTTP on HTTPS page): -30 pts
- Mixed passive content (images/styles over HTTP): -15 pts
- Untrusted or expired TLS certificate: -50 pts

### C. Cookie Security (15 pts max)
- Baseline: 100 points
- Session cookie missing `Secure` flag over HTTPS: -30 pts
- Session cookie missing `HttpOnly` flag: -25 pts
- Session cookie missing `SameSite` attribute: -20 pts
- Non-session tracking cookie missing `SameSite`: -10 pts

### D. Client-Side & Isolation (15 pts max)
- Baseline: 100 points
- External CDN script without Subresource Integrity (SRI): -15 pts
- Exposing production source maps (`.map` files publicly accessible): -15 pts
- Obsolete or vulnerable library version detected: -20 pts

### E. Privacy & Consent (15 pts max)
- Baseline: 100 points
- No discoverable Privacy Policy: -40 pts
- Third-party tracking scripts loaded prior to user consent: -25 pts
- Missing clear contact details or data controller identity: -15 pts

### F. Digital Trust & Transparency (10 pts max)
- Baseline: 100 points
- Missing `/.well-known/security.txt`: -30 pts
- No vulnerability disclosure program or security contact: -30 pts

---

## 3. Score Thresholds & Qualitative Classifications

| Score Range | English Label | Arabic Label | Security Status |
|---|---|---|---|
| **90 – 100** | Exceptional / Robust | وضع دفاعي استثنائي ومتين | Fully aligned with modern browser security baselines. |
| **75 – 89** | Strong / Compliant | وضع أمني قوي ومتوافق | Minor defense-in-depth headers recommended. |
| **55 – 74** | Moderate / Needs Hardening | متوسط / يتطلب تعزيزاً دفاعياً | Multiple standard security headers or flags absent. |
| **35 – 54** | Vulnerable / Weak | ضعيف / معرض للمخاطر | Critical configurations missing (e.g. no HSTS, no CSP). |
| **0 – 34** | Critical / Compromised Baseline | حرج / غير آمن أساسياً | Severe transport or cookie exposure detected. |
