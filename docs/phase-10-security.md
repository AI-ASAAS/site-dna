# Site DNA — Phase 10: Security, Privacy & Defensive Boundaries

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Engine:** Site DNA Accessibility Engine  
**Post-Condition:** 100% Non-destructive, passive audit mode  

---

## 1. Zero Form Submission Guarantee

To protect third-party website integrity, data confidentiality, and prevent accidental data alteration:
- The Accessibility Engine **never** submits forms, never clicks `<button type="submit">`, and never sends synthetic `POST` or `PUT` payloads to audited targets.
- Form controls and inputs are audited purely through passive DOM tree inspection (verifying attributes such as `for`, `id`, `aria-label`, `aria-labelledby`, `type`, `autocomplete`, and `required`).
- Interactive modal and focus trap verifications are conducted in isolated DOM memory representations without triggering background network requests.

---

## 2. Path Traversal & File System Hardening

- All requests referencing `crawl_run_id` pass through strict regular expression validation (`^[a-zA-Z0-9_\-]+$`).
- Any attempt to introduce relative paths (e.g., `../../etc/passwd` or `..\\windows\\win.ini`) is blocked immediately with a `SecurityValidationError` before any filesystem call is attempted.
- All artifact generation paths are strictly resolved against the designated `runs/` workspace directory.

---

## 3. Strict Model Governance & Credential Isolation

- The engine strictly binds to **Gemini 3.6 Flash** (`gemini/gemini-3.6-flash`).
- No secondary or unauthorized fallback models are invoked.
- API keys and tokens are loaded strictly via environment variables (`GEMINI_API_KEY`) and are never written to analysis output JSON, logs, or reports.
- Optional bearer token verification protects the `/api/v1/analysis/accessibility/*` endpoints in production deployments.
