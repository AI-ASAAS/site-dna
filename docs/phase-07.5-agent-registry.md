# Site DNA — Phase 07.5: 12-Agent Registry Specification

## 1. Overview

Site DNA features a 12-agent architecture covering the entire lifecycle of digital website intelligence. In Phase 07.5, all 12 agents are cataloged in a unified registry (`src/site_dna/orchestration/coordinator.py:AGENT_REGISTRY`) and exposed via `/api/v1/agents`.

Phases 01–07 are fully implemented and executable. Phases 08–12 are systematically registered as planned future capabilities, visible in the dashboard and registry for roadmap clarity but strictly locked against execution.

---

## 2. Complete Agent Registry Matrix

| Phase | Agent ID | Name (English / Arabic) | Status | Can Run | Requires Visual | Dependencies | Model |
|---|---|---|---|---|---|---|---|
| **01** | `infrastructure` | Core Diagnostics & Harness / البنية التحتية والفحص التشخيصي | Implemented | ❌ (Internal) | ❌ | None | `gemini-3.6-flash` |
| **02** | `discovery` | Website Crawling & Discovery / الاستكشاف والزحف الذكي للروابط | Implemented | ✅ | ❌ | None | `gemini-3.6-flash` |
| **03** | `visual_capture` | Browser Rendering & Visual Evidence / التصيير المتصفحي والأدلة البصرية | Implemented | ✅ | ❌ | `discovery` | Headless Playwright |
| **04** | `visual_identity` | AI Visual Identity Analyst / محلل الهوية البصرية الذكي | Implemented | ✅ | ✅ | `discovery`, `visual_capture` | `gemini-3.6-flash` |
| **05** | `ux_ui` | AI UX/UI & Usability Analyst / محلل تجربة وواجهة المستخدم | Implemented | ✅ | ✅ | `discovery`, `visual_capture` | `gemini-3.6-flash` |
| **06** | `content_marketing` | Content & Marketing Intelligence / ذكاء المحتوى والتسويق الرقمي | Implemented | ✅ | ❌ | `discovery` | `gemini-3.6-flash` |
| **07** | `technical_seo` | Technical SEO & Performance Analyst / محلل SEO التقني ومؤشرات الأداء | Implemented | ✅ | ❌ | `discovery` | `gemini-3.6-flash` |
| **08** | `competitor_intelligence` | Competitor Landscape & Differentiation / ذكاء المنافسين والتموضع التنافسي | **Planned** | ❌ (Locked) | ❌ | `discovery`, `content_marketing` | Future |
| **09** | `market_positioning` | ICP & Market Resonance Engine / هندسة التموضع والجمهور المستهدف | **Planned** | ❌ (Locked) | ❌ | `content_marketing` | Future |
| **10** | `conversion_optimization` | Conversion Rate & Funnel Optimization / هندسة معدلات التحويل ومسارات الشراء | **Planned** | ❌ (Locked) | ✅ | `ux_ui`, `content_marketing` | Future |
| **11** | `security_compliance` | Security, Privacy & Web Compliance / الأمان والخصوصية والامتثال الرقمي | **Planned** | ❌ (Locked) | ❌ | `discovery` | Future |
| **12** | `executive_synthesis` | Executive AI Synthesis & Strategic Roadmap / التوليف الاستراتيجي التنفيذي وخارطة الطريق | **Planned** | ❌ (Locked) | ✅ | `visual_identity`, `ux_ui`, `content_marketing`, `technical_seo` | Future |

---

## 3. Agent Execution Contracts

### 3.1 Implemented & Selectable Agents (Phases 02–07)
Users can select any combination of Phases 02–07 when starting an audit.
- **Topological Ingestion**: If an agent requires dependencies (such as `visual_identity` requiring `discovery` and `visual_capture`), the `AnalysisCoordinator` automatically resolves and includes prerequisite stages in the execution pipeline.
- **Selective Execution**: Unselected stages are completely bypassed, saving quota, compute, and execution time.

### 3.2 Planned Future Agents (Phases 08–12)
- **Frontend Safeguard**: The checkbox control is permanently disabled (`disabled={true}`), styled with slate opacity, and badged with `قريبًا / Planned`. Tooltips clearly state: *"وكيل تحليلي مخطط ضمن المراحل القادمة (8-12)"*.
- **Backend Safeguard**: `POST /api/v1/runs` inspects `request.stages`. If any stage is present in `PLANNED_STAGE_IDS`, the request is immediately aborted with `HTTP 400 Bad Request` and message:
  ```json
  {
    "detail": "Agent '<Agent Name>' (Phase 08-12) is planned and cannot be executed."
  }
  ```
- **Integrity**: Phase 08–12 backend logic is not implemented, preventing mock or fake results.
