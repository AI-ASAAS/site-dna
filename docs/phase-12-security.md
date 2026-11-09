# Site DNA — Phase 12: Security Hardening & Isolation Controls

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Phase:** 12 — Application Security & Boundary Controls  

---

## 1. Threat Model & Mitigations

### 1. Server-Side Request Forgery (SSRF) in Headless Chromium
* **Threat:** A maliciously crafted HTML report could attempt to fetch local network resources (`http://169.254.169.254`, `http://localhost:8000`, etc.) when Chromium renders the page to PDF.
* **Mitigation:** The `PlaywrightPdfRenderer` launches Chromium with `--disable-network`, `--disable-background-networking`, and `--disable-extensions`. Chromium is completely forbidden from opening any network socket during print rendering. All assets (fonts, logos, screenshots) are required to be pre-inlined as base64 data URIs.

### 2. Path Traversal & Arbitrary File Overwrite
* **Threat:** Malicious `crawl_run_id` or `report_id` containing path traversal patterns (e.g. `../../etc/passwd` or `..\\windows\\system32`) could read or overwrite files outside the `runs/` workspace.
* **Mitigation:**
  - Strict regex validation (`^[a-zA-Z0-9_\-]+$`) rejects any non-alphanumeric character or period/slash immediately with HTTP 400.
  - Path resolution strictly checks `.resolve().is_relative_to(base_runs_dir.resolve())`.

### 3. Cross-Site Scripting (XSS) & Content Confusion in Report Downloads
* **Threat:** Serving HTML reports or PDFs with ambiguous MIME types could lead to stored XSS or content-type sniffing vulnerabilities.
* **Mitigation:**
  - All download endpoints explicitly return `X-Content-Type-Options: nosniff`.
  - Content-Disposition is set to `attachment; filename="site-dna-report-<id>.<ext>"`.
  - Content-Security-Policy headers in HTML previews disallow external scripts.

### 4. API Authentication & Token Protection
* **Threat:** Unauthorized access to report generation and sensitive technical findings.
* **Mitigation:** Endpoints under `/api/v1/reports/final` support bearer token authentication via `REPORT_EXPORT_TOKEN` or `STRATEGIC_ANALYSIS_TOKEN` in settings. Missing or invalid tokens return HTTP 401 or 403.
