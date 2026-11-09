# Site DNA — Phase 08: Pre-flight Audit & Prior-Phase Verification

## 1. Executive Summary

Prior to beginning implementation of **Phase 08 (Competitor Intelligence)**, an exhaustive pre-flight verification of the existing Site DNA system was conducted in accordance with Section 5 of the Phase 08 specification. This audit reconciles test inventories, evaluates frontend-backend integration, verifies security boundaries, reviews Agent Registry readiness, and checks AI model operational boundaries.

---

## 2. Pre-flight A — Test Inventory Reconciliation

A collection audit using `pytest --collect-only -q` was executed on the current repository:

```
tests/api:          23 tests
tests/browser:      10 tests
tests/integration:  14 tests
tests/security:     31 tests
tests/unit:        197 tests
-----------------------------
Total Pytest Tests: 275 tests
```

### Explanation of Discrepancy in Previous Summary:
- The previous summary recorded an estimated sum of 257 tests when grouping tests by phase names.
- The actual pytest runner strictly collects **275 distinct test functions** across all five test suites.
- Furthermore, the 8 visual QA scenarios are automated browser verifications executed via Playwright in `scripts/verify_frontend_qa.py` (generating visual artifacts in `docs/screenshots/`), and are not collected by pytest.
- **Audit Conclusion**: Zero tests were deleted or altered. All 275 tests pass 100% under Python 3.11 with zero regressions.

---

## 3. Pre-flight B — Frontend Integration

Inspection of the Phase 07.5 frontend and FastAPI backend confirmed:
1. **Unified Application Serving**: FastAPI (`src/site_dna/api/main.py`) serves the REST API under `/api/v1` and compiles/mounts the production React/Vite SPA from `frontend/dist` with SPA fallback.
2. **Selective Execution Workflow**: `frontend/src/pages/NewAnalysis.tsx` allows users to select specific agent stages before launching an analysis.
3. **Real-time Event Streaming**: Server-Sent Events (SSE) via `/api/v1/runs/{run_id}/events` stream real-time events (`stage.started`, `stage.progress`, `stage.completed`, `run.completed`) with automated fallback polling via `useRunEvents.ts`.
4. **Historical Persistence**: Runs are stored on disk under `runs/<run_id>/` with `execution.json` and `events.jsonl`, reconstructed on restart without data loss.

---

## 4. Pre-flight C — Security Boundaries

The existing security architecture enforces:
1. **Path Traversal Defense**: Dynamic image serving in `/api/v1/runs/{run_id}/artifacts/screenshot` sanitizes identifiers (`[a-zA-Z0-9_\-]`) and verifies that resolved paths reside strictly within the canonical run directory. Non-image extensions are rejected.
2. **SSRF & Scheme Defense**: Target URLs are validated to strictly allow `http://` and `https://`. Disallowed protocols (`javascript:`, `file:`, `ftp:`) are blocked with HTTP 400/422. Hostnames are checked against private IP spaces, cloud metadata IP (`169.254.169.254`), and loopback addresses.
3. **Robots & Crawler Boundaries**: Bounded crawls enforce RFC 9309 rules, rate limits, and egress restrictions.
4. **Planned Agent Lockdown**: Submissions requesting planned agents (Phases 08–12) are blocked with `HTTP 400 Bad Request`.

---

## 5. Pre-flight D — Agent Registry Readiness

Inspection of `src/site_dna/orchestration/coordinator.py:AGENT_REGISTRY`:
- Phases 01–07 are currently registered as `implementation_status="implemented"` with `can_execute=True` (except Phase 01 internal infrastructure).
- Phase 08 (`competitor_intelligence`) is currently marked as:
  ```python
  implementation_status = "planned"
  runtime_availability = "not_implemented"
  can_execute = False
  ```
- **Activation Gate for Phase 08**: Phase 08 will only be flipped to `implemented` / `ready` / `can_execute=True` once all backend services, schemas, CrewAI agent & flow, fixtures, automated tests, and UI views are implemented and verified.
- **Phases 09–12**: Will remain strictly `planned`, `not_implemented`, and non-executable.

---

## 6. Pre-flight E — Model Validation

The official AI model for the entire project is **Gemini 3.6 Flash**:
- Google AI Studio Model ID: `gemini-3.6-flash`
- CrewAI Model Identifier: `gemini/gemini-3.6-flash`
- If the external Gemini API quota is exhausted, the system gracefully falls back to deterministic analysis, flags AI interpretation as unavailable, and reports the genuine provider status without fabricating results or silently switching to another model.
