# Site DNA — Phase 09 Security & Defensive Boundary Architecture

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Phase:** 09 — Security, Privacy & Trust Intelligence  
**Classification:** Defensive Application Security Protocol  

---

## 1. Non-Intrusive Operating Boundaries

Phase 09 strictly implements **passive observability**. The following active scanning behaviors are prohibited by architectural invariant:

| Prohibited Action | Enforcement Mechanism |
|---|---|
| Port scanning / TCP SYN flooding | No raw socket manipulation; only standard HTTP/HTTPS crawl artifacts are read. |
| SQL Injection / XSS exploit attempts | No active request parameters or fuzzing inputs are transmitted to target hosts. |
| Authentication brute-forcing | No credential submission or dictionary attacks against target login forms. |
| Directory / Path discovery fuzzing | Only links discovered naturally in target sitemaps and DOM crawl are evaluated. |
| Vulnerability exploitation claims | Findings are classified as configuration observations (`potential_risk`, `confirmed_configuration_issue`), never exploit confirmations. |

---

## 2. Data Protection & Sensitive Data Sanitization

### A. Strict Cookie Value Redaction
- In accordance with privacy and security mandates, cookie values are completely redacted before reaching analyzers, logs, or stored schemas.
- The `CookieAttributeRecord` schema enforces this at the type level:
```python
class CookieAttributeRecord(BaseModel):
    name: str
    domain: Optional[str] = None
    path: Optional[str] = None
    secure: bool = False
    httponly: bool = False
    samesite: Optional[Literal["Strict", "Lax", "None"]] = None
    is_session_cookie: bool = False
    # Notice: 'value' attribute is omitted by design!
```

### B. Header Sanitization
- `sanitize_headers()` filters out sensitive headers such as `Authorization`, `Proxy-Authorization`, and `Cookie`.

### C. Path Traversal & SSRF Defense
- Any input referencing `crawl_run_id` or `visual_run_id` is validated against strict alphanumeric/hyphen regex.
- All file access paths are resolved and verified to reside strictly within `runs_dir`. Attempts to escape the directory root raise `SecurityValidationError`.
