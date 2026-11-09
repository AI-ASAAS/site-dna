# ASAAS AI Skills Audit & Integration Analysis — Site DNA (Phase 01)

## 1. Executive Summary

This document records the systematic discovery, audit, selection, and architectural integration of skills from the ASAAS AI skills library into the **Site DNA** project (Phase 01: Project Foundation, Skills Integration & Gemini/CrewAI Setup).

The audit inspected the local skill repository at:
`C:\Users\mahmoodSaeed\Desktop\asaas_skills\skills`

Reference repository: `https://github.com/AI-ASAAS/skills`

---

## 2. Discovered Skills Inventory

The recursive scan of `C:\Users\mahmoodSaeed\Desktop\asaas_skills\skills` discovered the following skills and their structural assets:

| Skill Path | Category | Skill Name | Version / Metadata | Description |
|---|---|---|---|---|
| `skills/ai/SKILL.md` | AI | `ai` (AI Foundation) | ASAAS AI Team | Foundation standards for LLM calls, structured output, assistants, RAG, agents, and evaluations. |
| `skills/ai/build-ai-agents/SKILL.md` | AI | `build-ai-agents` | Task Skill | Design, build, and orchestrate agent workflows using ASAAS agent architecture and CrewAI defaults. |
| `skills/backend/SKILL.md` | Backend | `backend` (Backend Foundation) | ASAAS Backend Team | Modular FastAPI architecture, thin routers, Pydantic contracts, service layers, logging, and environment settings. |
| `skills/cyber/security-review/SKILL.md` | Cybersecurity | `security-review` | v3.0.0 (2026-09-27) | Comprehensive system and AI security audits, trust boundaries, credential protection, and defense against untrusted inputs. |
| `skills/frontend/SKILL.md` | Frontend | `frontend` (Frontend Foundation) | ASAAS Frontend Team | Component architecture, state management, styling, and Arabic RTL interfaces with React/Vite. |
| `skills/frontend/asaas-ui/SKILL.md` | Frontend | `asaas-ui` | Task Skill | ASAAS liquid-glass design kit, Thmanyah typography, brand tokens, and AssistantWidget. |
| `skills/Mobile/Flutter_SKILL.md` | Mobile | `mobile-flutter` | ASAAS Mobile Team | Flutter architecture, Riverpod/Bloc, RTL localization, and secure mobile storage. |
| `skills/Mobile/Native_SKILL.md` | Mobile | `mobile-native` | ASAAS Mobile Team | iOS/Android native development conventions. |

### Evaluation of Specifically Requested Skills
- **ASAAS Agent Platform**: Not present as an isolated standalone repository/skill; its specifications and core practices are embodied in `skills/ai/SKILL.md` and `skills/ai/build-ai-agents/SKILL.md`.
- **Frontend / Asaas UI**: Present in `skills/frontend/` and `skills/frontend/asaas-ui/`. Evaluated and deferred to later phases since Phase 01 is strictly headless/backend/CLI.
- **CRDO Skills**: Evaluated; not present in the local ASAAS skills directory.

---

## 3. Selected Skills & Architectural Rationale

The following skills were selected for direct architectural guidance and implementation in Phase 01:

### 1. `ai` (AI Foundation — `skills/ai/SKILL.md`)
- **Status:** **Selected**
- **Rationale:** Establishes the standard ASAAS boundaries for AI:
  - Single provider boundary (`modules/llm/` or `core/llm.py`).
  - Validation of model output like user input using Pydantic schemas.
  - Strict protection of credentials: no secrets in prompts, logs, or evaluation sets.
  - Clear separation between deterministic application logic and probabilistic model generation.
  - Standardized error handling: fail visibly rather than hallucinating success.

### 2. `build-ai-agents` (`skills/ai/build-ai-agents/SKILL.md`)
- **Status:** **Selected**
- **Rationale:** Directly governs the implementation of the CrewAI Foundation Agent and Flow:
  - Agent responsibility definition (role, goal, backstory tied to verifiable tasks).
  - Explicit LLM factory usage rather than embedding configuration inside agent logic.
  - Single sequential agent for Phase 01 smoke validation to minimize token overhead and latency.
  - Strict bounding of tool permissions and delegation (`allow_delegation=False` for Phase 01).
  - Structured output validation using Pydantic contracts.

### 3. `backend` (Backend Foundation — `skills/backend/SKILL.md`)
- **Status:** **Selected**
- **Rationale:** Defines the architectural layout and FastAPI structure:
  - Modular organization under `src/site_dna/`.
  - Separation of concerns: API routers (`api/routes/`), business schemas (`schemas/`), service layer (`services/`), and core utilities (`core/`).
  - Thin routers with dependency injection and Pydantic response models.
  - Standardized environment-based settings using `pydantic-settings`.
  - Proper logging using `logging.getLogger(__name__)`.

### 4. `security-review` (`skills/cyber/security-review/SKILL.md`)
- **Status:** **Selected**
- **Rationale:** Informs the security baseline for Site DNA:
  - Trust boundary identification: treat future website inputs and external responses as untrusted.
  - Secret protection: GEMINI_API_KEY never logged, exposed via API endpoints, or committed to git.
  - Safe defaults: server bound to `127.0.0.1` by default; live LLM testing restricted to CLI and opt-in flags.
  - Input validation: strict schema enforcement at the boundary.

---

## 4. Non-Applicable Skills in Phase 01

| Skill | Status | Reason for Deferral |
|---|---|---|
| `frontend` / `asaas-ui` | Deferred | Phase 01 covers project setup, backend API, CLI, and model integration. User interface components will be incorporated in future frontend phases. |
| `mobile-flutter` / `mobile-native` | Not Applicable | Site DNA is a server-side web intelligence platform, not a mobile client application. |

---

## 5. Key Instructions Influencing Implementation

1. **One Provider Boundary:** All LLM configuration is isolated in `src/site_dna/core/llm.py`. Agents and flows obtain model instances through the unified factory `get_llm()`.
2. **Never Mask Failures:** If a live provider fails (e.g. HTTP 503 high demand or 401 unauthorized), the system surfaces the exact diagnostic failure code and status rather than returning a mocked pass.
3. **Pydantic Structured Output:** The smoke test agent output is defined in `src/site_dna/schemas/health.py` and validated through Pydantic contracts.
4. **Deterministic Tool Separation:** Direct diagnostics (`src/site_dna/services/gemini_diagnostics.py`) use the official `google-genai` SDK directly to isolate SDK connectivity from CrewAI orchestration errors.
5. **No Secrets in Logs or Responses:** `pydantic.SecretStr` is utilized for credentials, masking them in string representations, JSON dumps, and logs.

---

## 6. Access and Compatibility Limitations

- **Local Repository:** The local skills folder at `C:\Users\mahmoodSaeed\Desktop\asaas_skills\skills` is fully accessible and up to date.
- **Provider Status:** Google Gemini 3.8 Flash endpoint availability may be subject to transient upstream capacity spikes (HTTP 503); our architecture handles this with explicit retry policies and diagnostic classifications.
