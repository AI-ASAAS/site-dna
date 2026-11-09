# Site DNA — Phase 11 Frontend Implementation Specification
## Interactive Strategic Intelligence Console, Unified Tabs & RTL Layout Architecture

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Frontend Stack:** React + Vite + TypeScript  
**Design Kit:** ASAAS UI Kit (`asaas-ui`) with liquid glass tokens & Thmanyah typeface  
**Primary Language:** Arabic (RTL)  
**Secondary Language:** English (LTR)  

---

## 1. UI Architecture & View Hierarchy

The Strategic Intelligence Interface is embedded directly into the Site DNA Analysis Monitor (`/analyses/:runId`) and accessible via the top-level tab bar as well as report viewers.

```
Layout (v0.1.0 Phase 11 Top Banner)
   └── AnalysisMonitor
          ├── Tab Bar: [Monitor, Overview, Screenshots, Findings, Recs, Competitors, Security, A11y, Strategic (60), Reports]
          └── StrategicIntelligenceView
                 ├── Header: Strategic Health Score (60/100) & Index Pill
                 ├── Multi-Agent KPI Row (Sources, Raw, Unified, Duplicates, Conflicts, Actions)
                 └── 7 Interactive Sub-Tabs:
                        1. Overview & Synthesis
                        2. Unified Findings (with Domain & Severity Filters)
                        3. Deduplication & Cross-Agent Relationship Graph
                        4. Conflicts & Balanced Architectural Trade-offs
                        5. Sequenced 4-Wave Action Roadmap Cards
                        6. Action Backlog (P0–P3 with Interactive Status PATCH Dropdown)
                        7. Verification Procedures & Metric Impact Measurement Plan
```

---

## 2. RTL Centering & Container Constraints

In previous early iterations (Phase 07.5/08), browsers with cached or default body styling in RTL flex containers occasionally caused column squishing to the far right. This was rigorously addressed in `src/styles/app.css` and `Layout.tsx`:
- Explicit full dimensions enforced:
  ```css
  html, body, #root {
    width: 100%;
    min-height: 100%;
    margin: 0;
    padding: 0;
  }
  ```
- Layout root wrapping uses `w-full min-h-screen flex flex-col relative`.
- Max content boundary uses `max-w-7xl w-full mx-auto p-4 sm:p-6 lg:p-8`.
- Live browser rendering verified via Chromium headless screenshots across 1440x900 and 1920x1080 viewports.

---

## 3. Interactive State Management

- **Action Status Updates:** Backlog items feature an interactive `<select>` dropdown. Selecting a new status triggers an asynchronous `PATCH /api/v1/analysis/strategy/{crawl_run_id}/actions/{action_id}` request, updating local React state optimistically with zero screen flicker.
