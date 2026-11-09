# Site DNA — Phase 09 Methodology: Passive Security & Privacy Auditing

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Phase:** 09 — Security, Privacy & Trust Intelligence  
**Standard:** Passive, Evidence-Based, Non-Intrusive Verification  

---

## 1. Core Principles

Site DNA's Security & Privacy Intelligence module operates under four inviolable principles:
1. **Zero Active Scanning:** No port scans, SQLi/XSS injection probes, directory fuzzing, or brute force attempts.
2. **Deterministic Evidence Base:** Every finding must be linked to observable HTTP response headers, TLS metadata, or DOM elements collected during normal browsing.
3. **Strict Credential & Cookie Redaction:** Cookie values and Authorization tokens are redacted before analysis and schema persistence.
4. **Proportional Defensive Guidance:** Recommendations focus on modern web platform security standards (HSTS, CSP, Subresource Integrity, Cross-Origin Isolation).

---

## 2. Evaluation Domains

### A. Transport & Encryption
- Scheme verification across all visited pages (HTTP vs. HTTPS).
- Redirect enforcement (301/302 from HTTP to HTTPS).
- TLS certificate chain validity and protocol version observation (TLS 1.2 / TLS 1.3 preferred).

### B. Security Headers (8 Standard Headers)
1. **Strict-Transport-Security (HSTS):** Minimum `max-age=31536000`, presence of `includeSubDomains` and `preload`.
2. **Content-Security-Policy (CSP):** Directives evaluation (`default-src`, `script-src`, `object-src`), detection of `'unsafe-inline'` and `'unsafe-eval'`.
3. **X-Frame-Options:** Mitigation of clickjacking (`DENY` or `SAMEORIGIN`), complemented by `frame-ancestors` in CSP.
4. **X-Content-Type-Options:** Enforcing `nosniff` to avoid MIME sniffing attacks.
5. **Referrer-Policy:** Preventing token leakage in referrers (`strict-origin-when-cross-origin` or `no-referrer`).
6. **Permissions-Policy:** Restricting sensitive browser hardware APIs (camera, microphone, geolocation).
7. **Cross-Origin-Opener-Policy (COOP):** Process isolation for browsing contexts (`same-origin`).
8. **Cross-Origin-Resource-Policy (CORP):** Protecting assets from cross-origin reads (`same-origin` or `same-site`).

### C. Cookie Security
- **Secure Flag:** Required on all cookies delivered over HTTPS.
- **HttpOnly Flag:** Required on authentication, session, and token cookies to prevent DOM XSS theft.
- **SameSite Flag:** `Lax` or `Strict` to mitigate cross-site request forgery (CSRF).

### D. Client-Side Observations & Subresource Integrity
- Identification of external CDN scripts lacking Subresource Integrity (`integrity="sha384-..."`).
- Publicly accessible production JavaScript source maps (`.map`).
- Obsolete or deprecated third-party libraries.

### E. Privacy Signals & User Consent
- Availability of a clear Privacy Policy (`/privacy`, `/privacy-policy`).
- Clear disclosure of data controller identity and contact channels.
- Presence of a functional Cookie Consent management mechanism (CMP).

### F. Digital Trust & Security Transparency
- Presence of `/.well-known/security.txt` or dedicated security disclosure page.
- Clear vulnerability reporting channels or bug bounty programs.
- Recognizable third-party certifications (e.g. ISO 27001, SOC 2, PCI-DSS) where claimed.
