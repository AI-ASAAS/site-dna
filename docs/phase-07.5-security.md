# Site DNA — Phase 07.5: Security Architecture & Safeguards

## 1. Threat Model & Overview

The introduction of an interactive web frontend and artifact streaming endpoints introduces potential threat vectors including path traversal, arbitrary file access, SSRF/protocol injection, and cross-origin abuse.

Phase 07.5 incorporates defense-in-depth safeguards at all layers.

---

## 2. Security Safeguards

### 2.1 Path Traversal Protection on Artifact Endpoints
The `/api/v1/runs/{run_id}/artifacts/screenshot` endpoint serves dynamic image files from disk. To prevent arbitrary local file disclosure (e.g. `../../etc/passwd` or `..\..\..\Windows\win.ini`), `AnalysisCoordinator.resolve_screenshot_path` enforces:
1. **Identifier Sanitization**: Strips any character outside `[a-zA-Z0-9_\-]` from `run_id`.
2. **Path Canonicalization**: Resolves target path via `.resolve()`.
3. **Boundary Verification**: Ensures that the resolved path strictly resides within the run's canonical directory:
   ```python
   run_dir = self._get_run_dir(run_id)
   target_path = (run_dir / "visual" / safe_rel).resolve()
   if not str(target_path).startswith(str(run_dir.resolve())):
       raise HTTPException(status_code=403, detail="Access denied: Invalid file path.")
   ```
4. **Extension Whitelisting**: Prohibits non-image extensions (only `.png`, `.jpg`, `.webp` allowed).

### 2.2 Protocol & URL Injection Safeguards
Run submissions accept target website URLs. To mitigate SSRF and protocol manipulation:
- URLs are strictly validated against:
  `^https?://[a-zA-Z0-9\-\.]+(\.[a-zA-Z]{2,})?(:[0-9]+)?(/.*)?$`
- Non-web protocols (`javascript:`, `file:`, `ftp:`, `data:`, `gopher:`) are blocked with `HTTP 400 Bad Request`.
- Hostnames are resolved through the Phase 02 URL Validator prior to dispatching crawler processes.

### 2.3 CORS & Origin Policy
FastAPI is configured with explicit CORS origins:
```python
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
```

### 2.4 SPA Static Asset Serving Security
Static files served by FastAPI from `frontend/dist` are scoped to the build distribution directory. Path traversal attempts against the SPA fallback route are safely handled by `StaticFiles` standard protections.

### 2.5 Future Agent Execution Lockdown
Phase 08–12 agent IDs are locked at both frontend and backend. Attempting to bypass the UI and post `{"stages": ["competitor_intelligence"]}` results in immediate `HTTP 400 Bad Request`, ensuring unverified or planned agent logic cannot be invoked.
