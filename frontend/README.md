# Site DNA — Frontend Platform (Phase 07.5)

Professional operations dashboard and analysis suite for **Site DNA (بصمة الموقع)**, developed for **ASAAS AI (أساس للذكاء الاصطناعي)**.

Built with **React 19**, **TypeScript**, **Vite**, and the official **ASAAS UI Kit**.

---

## Features

- **ASAAS Visual Identity**: Authentic liquid-glass aesthetics, Thmanyah Arabic typography (`ThmanyahSans`, `ThmanyahSerifDisplay`), brand ink, gold, and sand tokens.
- **Bilingual & Bidirectional**: Primary Arabic RTL (`dir="rtl"`) with seamless toggle to English LTR (`dir="ltr"`).
- **Interactive Selective Agent Picker**: Users pick which analysis agents to run (Phases 02–07) or select all with 1 click.
- **Future-Agent Readiness**: Visibly catalogs planned agents for Phases 08–12 (*Competitor Intelligence*, *Market Positioning*, *CRO*, *Security & Compliance*, *Executive AI Synthesis*) with disabled controls and backend rejection safeguards.
- **Real-Time Live Monitor**: Server-Sent Events (SSE) streaming live stage transitions, progress bars, and events log with automated fallback polling.
- **11 Integrated Views**:
  - `Dashboard`: Aggregated metrics, recent runs, agent readiness matrix.
  - `New Analysis`: URL submission with selective agent chooser.
  - `Live Monitor`: Real-time execution timeline and live streaming log.
  - `Overview`: Multi-agent score gauges, executive summary, and scientific limitations.
  - `Screenshot Explorer`: Desktop and mobile visual evidence with full-screen lightbox preview.
  - `Findings Explorer`: Filterable severity badges with slide-out Evidence Drawer.
  - `Recommendations Viewer`: Prioritized P1/P2/P3 actionable remediation cards.
  - `Report Viewer`: Markdown and JSON formatted audit report viewer with copy & download.
  - `Agents Directory`: 12-agent capability catalog and dependencies.
  - `History`: Searchable, filterable audit history table.
  - `Settings`: Target model (`gemini-3.6-flash`), system health, and theme preferences.

---

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python backend running at `http://127.0.0.1:8000`

### Development Mode
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser. API requests to `/api` are automatically proxied to `http://127.0.0.1:8000`.

### Production Build
```bash
npm run build
```
Builds optimized production assets to `frontend/dist`. These files are automatically served by the FastAPI application at root (`http://127.0.0.1:8000/`) with SPA client-side routing fallback.
