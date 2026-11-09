# Site DNA — Phase 11 Security & Boundary Architecture
## Defensive Non-Destructive Principles, ID Sanitization & Quota Protection

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Phase:** 11 — Strategic Intelligence & Unified Action Roadmap  

---

## 1. Security Architecture & Boundary Verification

1. **Passive Read-Only Analysis:**
   - Phase 11 executes entirely on previously collected artifacts stored in `runs/<crawl_run_id>/analysis/*`.
   - It performs zero outbound network probing, port scanning, or intrusive payloads.
2. **Strict Identifier Sanitization (Path Traversal Defense):**
   - All input IDs (`crawl_run_id`, `action_id`, `strategy_run_id`) are validated against regex `^[a-zA-Z0-9_\-]+$`.
   - Any path traversal sequences (`../`, `..\`, `%2e%2e`) trigger immediate `HTTP 400 Bad Request`.
3. **Optional API Bearer Authentication:**
   - Supports `STRATEGIC_ANALYSIS_TOKEN` configuration.
   - When set, requests must provide `Authorization: Bearer <token>`, failing with `HTTP 401` or `HTTP 403` on mismatch.
4. **Deterministic Fallback & Quota Protection:**
   - If AI quota is exhausted or Google AI Studio returns HTTP 429, the system triggers graceful fail-soft fallback.
   - Deterministic prioritization algorithms, topological DAG resolution, and Arabic template generators guarantee that valid artifacts and action plans are generated even when AI models are unavailable.
5. **No Speculative or Financial Claims:**
   - `EvidenceValidator` inspects generated action titles and descriptions to ensure no fabricated financial percentages or ungrounded uplift assertions are emitted.
