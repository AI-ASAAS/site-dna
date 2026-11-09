# Site DNA — Phase 07.5: API Integration & Event Streaming Specification

## 1. REST Endpoints Overview

All Phase 07.5 operations are hosted under `/api/v1` and fully documented via FastAPI's interactive Swagger UI (`/docs`) and OpenAPI spec (`/openapi.json`).

---

## 2. API Endpoints Catalog

### 2.1 Agents Registry

#### `GET /api/v1/agents`
Returns full list of 12 registered agents with capability metadata.
- **Response**: `200 OK` → `list[AgentRegistryItem]`

#### `GET /api/v1/agents/{agent_id}`
Returns metadata for a specific agent.
- **Parameters**: `agent_id` (e.g. `visual_identity`)
- **Response**: `200 OK` → `AgentRegistryItem` | `404 Not Found`

---

### 2.2 Dashboard Telemetry

#### `GET /api/v1/dashboard/summary`
Returns global metrics and agent readiness states for the main operations dashboard.
- **Response**: `200 OK`
```json
{
  "total_runs": 14,
  "completed_runs": 12,
  "running_runs": 1,
  "failed_runs": 1,
  "total_findings": 142,
  "total_recommendations": 86,
  "recent_runs": [...],
  "agent_readiness": {...}
}
```

---

### 2.3 Run Management & Execution

#### `GET /api/v1/runs`
Lists historical runs with search and status filtering.
- **Query Params**:
  - `query` (optional string): Search by URL or Run ID
  - `status` (optional string): Filter (`all`, `completed`, `running`, `failed`)
  - `page` (default: 1): Page number
  - `page_size` (default: 20, max: 100): Page size
- **Response**: `200 OK` → `{ items: [...], total: 14, page: 1, page_size: 20, pages_count: 1 }`

#### `POST /api/v1/runs`
Submits a new analysis run with user-selected agent stages.
- **Payload**:
```json
{
  "url": "https://example.com",
  "stages": ["visual_capture", "visual_identity", "technical_seo"],
  "max_pages": 5,
  "offline_mode": false,
  "deterministic_only": false
}
```
- **Response**:
  - `201 Created` → `RunRecord`
  - `400 Bad Request` → Invalid URL format or attempted execution of planned Phase 08–12 agent.

#### `GET /api/v1/runs/{run_id}`
Returns execution state, stage breakdown, duration, and scores for a specific run.
- **Response**: `200 OK` → `RunRecord` | `404 Not Found`

---

### 2.4 Real-Time Event Streaming (SSE)

#### `GET /api/v1/runs/{run_id}/events`
Opens a Server-Sent Events (SSE) connection pushing real-time progress and stage state changes.
- **Headers**: `Content-Type: text/event-stream`, `Cache-Control: no-cache`
- **Event Contract**:
  - `event: init`: Current run snapshot immediately on connection.
  - `event: stage.started`: Emitted when an agent stage begins execution.
  - `event: stage.progress`: Emitted during long operations (e.g. crawling or rendering).
  - `event: stage.completed`: Emitted when a stage successfully concludes.
  - `event: run.completed`: Emitted when the entire pipeline finishes.
  - `event: done`: Terminal signal instructing client to close the EventSource.
  - `: heartbeat`: Sent every 15 seconds of inactivity to prevent proxy timeouts.

---

### 2.5 Screenshots & Visual Evidence

#### `GET /api/v1/runs/{run_id}/screenshots`
Returns desktop and mobile screenshot metadata, viewports, and page paths.
- **Response**: `200 OK` → `list[ScreenshotItem]`

#### `GET /api/v1/runs/{run_id}/artifacts/screenshot?file=<relative_path>`
Safely streams PNG image bytes with path traversal security checks.
- **Response**: `200 OK` (`image/png`) | `403/404` for invalid or forbidden paths.

---

### 2.6 Findings, Recommendations & Reports

#### `GET /api/v1/runs/{run_id}/findings?agent=<optional_agent_id>`
Returns structured findings across analyzed stages with severity badges.

#### `GET /api/v1/runs/{run_id}/recommendations?priority=<p1|p2|p3>`
Returns prioritized remediation items with effort estimation and code/CSS suggestions.

#### `GET /api/v1/runs/{run_id}/reports/{stage_id}?format=markdown|json`
Returns complete markdown audit text or raw analysis JSON for a specific stage.
