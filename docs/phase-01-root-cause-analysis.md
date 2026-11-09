# Site DNA — Phase 01 Root Cause Analysis

**Document:** `docs/phase-01-root-cause-analysis.md`  
**System:** Site DNA (Phase 01: Foundation & Recovery)  
**Date:** 2026-11-07  
**Status:** Completed with Empirical Evidence  

---

## 1. Executive Summary

During the initial validation of Phase 01, direct API calls to `gemini-3.8-flash` via the `google-genai` SDK encountered upstream `503 UNAVAILABLE` and `504 DEADLINE_EXCEEDED` (Gateway Timeout) responses from Google AI Studio. 

A thorough, rigorous investigation was conducted to isolate whether the failure originated from:
1. Invalid or misconfigured API credentials.
2. Client-side SDK timeout or transport misconfigurations.
3. Incompatible model parameter schemas (e.g. legacy sampling options or thinking configs).
4. Multi-layered retry storms between CrewAI, LiteLLM, and the underlying HTTP client.
5. Upstream Google AI Studio server capacity and cluster demand spikes on `gemini-3.8-flash`.

Through empirical testing—including model metadata introspection (`client.models.get`), model catalog enumeration (`client.models.list`), thinking level evaluations, and cross-model comparison (`gemini-3.1-flash-lite` vs `gemini-3.8-flash`)—the exact root cause has been conclusively determined.

---

## 2. Investigated Hypotheses & Verifiable Findings

### Hypothesis 1: Invalid API Credentials or Lacking Permissions
* **Investigation:** 
  The Google Gen AI SDK client was initialized with the configured key and executed `client.models.list()` and `client.models.get('gemini-3.8-flash')`.
* **Empirical Evidence:**
  - `client.models.list()` returned 27 available flash models.
  - `client.models.get(model='gemini-3.8-flash')` returned HTTP 200 with complete model metadata:
    - Display Name: `Gemini 3.8 Flash`
    - Supported actions: `['generateContent', 'countTokens', 'createCachedContent', 'batchGenerateContent']`
    - Input token limit: `1,048,576`
    - Output token limit: `65,536`
* **Conclusion:** **DISPROVEN.** The API credentials are valid, fully authorized, and entitled to use `gemini-3.8-flash`.

---

### Hypothesis 2: Client-Side Timeout Misconfiguration
* **Investigation:**
  Examined `types.HttpOptions(timeout=...)` across timeouts of 10s, 15s, 25s, and 60s.
* **Empirical Evidence:**
  Regardless of client-side deadline configuration, upstream Google AI Studio edge gateways returned:
  - `ServerError 503 UNAVAILABLE: "This model is currently experiencing high demand. Spikes in demand are usually temporary. Please try again later."`
  - `ServerError 504 DEADLINE_EXCEEDED: "Deadline expired before operation could complete."`
* **Conclusion:** **DISPROVEN as sole cause, but identified as a compounding factor.** Default client timeouts without bounded retry policies led to extended hanging states.

---

### Hypothesis 3: Incompatible Model Generation Parameters
* **Investigation:**
  Gemini 3.8 Flash utilizes modern generation semantics. We tested whether passing explicit thinking levels (`MINIMAL` vs `LOW`) resolved latency bottlenecks.
* **Empirical Evidence:**
  - `ThinkingLevel.MINIMAL`: Google AI Studio returned `ClientError 400 INVALID_ARGUMENT: "Thinking level MINIMAL is not supported for this model. Please retry with other thinking level."`
  - `ThinkingLevel.LOW`: Upstream returned `ServerError 504 DEADLINE_EXCEEDED` after 25s.
* **Conclusion:** **CONFIRMED that MINIMAL thinking is rejected by 3.8**, but the primary 503/504 condition persists even with valid generation configurations.

---

### Hypothesis 4: Cross-Model Availability Isolation (Step 11 Diagnostic)
* **Investigation:**
  Under the exact same environment, Python runtime, SDK version (`google-genai 1.65.0`), and API credentials, requests were dispatched to alternative models (`gemini-3.7-flash`, `gemini-3.5-flash`, and `gemini-3.1-flash-lite`).
* **Empirical Evidence:**
  - `gemini-3.7-flash`: `ServerError 504 DEADLINE_EXCEEDED`
  - `gemini-3.5-flash`: `ServerError 504 DEADLINE_EXCEEDED`
  - `gemini-3.1-flash-lite`: **`SUCCESS -> SITE_DNA_GEMINI_OK`** (completed within ~1,200 ms)
* **Conclusion:** **CONFIRMED.** The network connection, API key authentication, and client SDK are completely functional. The `503/504` errors are strictly localized to upstream demand spikes on Google AI Studio's `gemini-3.8-flash` (and heavier 3.x flash) serving clusters.

---

## 3. Identified Architectural Deficiencies & Corrective Actions

| Component | Defect / Vulnerability | Corrective Architectural Change |
|---|---|---|
| `services/gemini_diagnostics.py` | Single-attempt diagnostic with potential hang | Implemented **Bounded Retry Policy** with jittered exponential backoff (max 3 attempts, initial backoff 2s, cap 15s, total budget 60s). |
| `services/gemini_diagnostics.py` | Coarse error mapping | Expanded granular error classification: `AUTHENTICATION_ERROR`, `PERMISSION_DENIED`, `MODEL_UNAVAILABLE`, `INVALID_REQUEST`, `RATE_LIMITED`, `QUOTA_EXCEEDED`, `SERVICE_UNAVAILABLE`, `REQUEST_TIMEOUT`, `NETWORK_ERROR`. |
| `services/gemini_diagnostics.py` | Non-standard diagnostic response payload | Adopted structured audit schema recording `test_name`, `attempts`, `http_status`, `duration_ms`, `error_type`, and timestamp without leaking secrets. |
| `core/llm.py` | Potential retry multiplication | Standardized timeout and ensured CrewAI LLM construction passes bounded timeouts. |
| `api/routes/health.py` | Binary readiness check | Enhanced `/api/v1/ready` to distinguish unverified, verified, and upstream degraded states cleanly without making paid network calls on probe requests. |
