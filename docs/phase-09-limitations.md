# Site DNA — Phase 09 Limitations & Defensive Boundary Explanations

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Phase:** 09 — Security, Privacy & Trust Intelligence  

---

## 1. Passive Audit Limitations

1. **Passive vs. Active Testing:**
   - Site DNA evaluates *configuration signals*, not exploitability. A missing header (e.g. `X-Frame-Options`) indicates a defensive posture gap, but does not guarantee that the site can be successfully clickjacked without deeper context.
2. **Reverse Proxy & CDN Header Stripping:**
   - If an origin server sits behind a CDN (such as Cloudflare, CloudFront, or Fastly), the headers observed represent the edge configuration. Origin server vulnerabilities hidden behind edge rules cannot be passively assessed.
3. **Session Cookie Heuristics:**
   - Session identification uses naming conventions (e.g., `session`, `token`, `jwt`, `sid`, `auth`). Non-standard custom session names may be categorized as functional cookies rather than session cookies.
4. **JavaScript-Rendered Consent Banners:**
   - If a consent banner relies on heavy client-side JavaScript that executes after a long delay or requires specific geo-IP conditions, passive DOM analysis might miss it if not captured in the crawl dataset.

---

## 2. False-Positive Mitigation

- Findings are explicitly labeled with verifiable confidence levels:
  - `confirmed_configuration_issue`: The header or flag is definitively missing from the HTTP response.
  - `potential_risk`: An observable signal (e.g., lack of SRI on an external script) presents a potential supply chain risk depending on upstream trust.
- Every finding includes direct evidence references (`evidence_ids` and `evidence_snippets`) allowing security engineers to verify the observation immediately.
