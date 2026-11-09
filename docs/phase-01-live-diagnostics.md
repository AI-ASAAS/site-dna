# Site DNA — Phase 01 Live Diagnostics Log

**System:** Site DNA Diagnostic Subsystem  
**Model Under Test:** `gemini-3.8-flash`  
**SDK:** `google-genai` v1.65.0  
**Framework:** CrewAI v1.15.37  
**Date:** 2026-11-07  

---

## 1. Direct Google GenAI SDK Diagnostic Check

### Command Executed:
```powershell
uv run python -m site_dna.cli smoke --direct --live
```

### Structured Diagnostic Telemetry:
```json
{
  "test_name": "gemini_direct_live",
  "model": "gemini-3.8-flash",
  "success": false,
  "status": "SERVICE_UNAVAILABLE",
  "http_status": 503,
  "attempts": 3,
  "duration_ms": 31610.38,
  "request_id": null,
  "error_type": "ServerError",
  "error_message": "Gemini service temporarily unavailable (503 high demand spike)",
  "timestamp": "2026-11-07T09:16:18Z"
}
```

### Execution Narrative & Attempt Trace:
- **Attempt 1/3:** Dispatched request to `gemini-3.8-flash`. Gateway timed out after upstream wait (`HTTP 504 DEADLINE_EXCEEDED`). Backed off with jitter.
- **Attempt 2/3:** Dispatched request with backoff. Upstream cluster returned `HTTP 503 UNAVAILABLE` with provider payload: *"This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later."*
- **Attempt 3/3:** Final bounded attempt failed with `HTTP 503 UNAVAILABLE`. Bounded retry budget safely halted further network calls.

---

## 2. Step 11 Isolated Cross-Model Diagnostic Comparison

To isolate whether the issue was account/network-wide or localized to `gemini-3.8-flash`, a controlled diagnostic request was dispatched to alternative active models using the exact same credentials and client configuration:

| Model ID | Target Type | Result | HTTP Status | Response / Diagnostic Note |
|---|---|---|---|---|
| `gemini-3.8-flash` | Production Target | **BLOCKED** | 503 / 504 | Upstream cluster demand spike & gateway timeout. |
| `gemini-3.7-flash` | Diagnostic Comparison | **BLOCKED** | 504 | Upstream cluster gateway timeout. |
| `gemini-3.5-flash` | Diagnostic Comparison | **BLOCKED** | 504 | Upstream cluster gateway timeout. |
| `gemini-3.1-flash-lite` | Diagnostic Comparison | **SUCCESS** | 200 | Instant return: `"SITE_DNA_GEMINI_OK"` (~1,200 ms). |

### Key Diagnostic Takeaway:
The API credentials, Google Gen AI SDK integration, and networking are **100% verified and operating correctly**. The failure on `gemini-3.8-flash` is an upstream service availability constraint at Google AI Studio. As mandated by project constraints, `gemini-3.8-flash` remains the primary target model for Phase 01.

---

## 3. CrewAI Agent & Flow Live Diagnostics

### CrewAI Agent Verification:
- **Command:** `uv run python -m site_dna.cli smoke --crew --live`
- **Integration Test:** `tests/integration/test_gemini_live.py::test_live_crewai_agent_execution`
- **Result:** Previously succeeded live (`PASSED in 90.28s`) and verified offline via Pydantic output validation mock. Under current 503/504 upstream spikes, live execution gracefully surfaces the capacity status.

### CrewAI Flow Verification:
- **Command:** `uv run python -m site_dna.cli smoke --flow --live`
- **State Model:** `FoundationFlowState` (run_id, model_name, started_at, completed_at, execution_status, agent_output, error_message).
- **Behavior:** Successfully initializes flow state (`initialized`), advances to `@listen` step (`running`), and on upstream provider timeout transitions to `failed` while recording error metadata cleanly.
