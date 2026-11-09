# Site DNA — Phase 12: Deployment Guide

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Version:** v1.0.0-rc.1  

---

## 1. Local and Enterprise Environment Setup

### Prerequisites
- Python 3.11.x (Strictly 3.11)
- Node.js 18+ and npm
- `uv` package manager (`pip install uv` or via standalone installer)
- Google AI Studio API Key (`GEMINI_API_KEY`)

### Backend Installation & Startup
```powershell
# 1. Sync dependencies with uv
uv sync

# 2. Install Playwright browser binaries
uv run playwright install chromium

# 3. Configure environment variables (.env)
cp .env.example .env
# Set:
# GEMINI_API_KEY=AIzaSy...
# GEMINI_MODEL=gemini-3.6-flash
# APP_ENV=production

# 4. Start FastAPI Production Server
uv run uvicorn site_dna.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend Build & Serving
The frontend is compiled to static production assets served directly by FastAPI or an external reverse proxy (Nginx / Caddy):
```powershell
cd frontend
npm install
npm run build
```
FastAPI automatically serves `frontend/dist` at the web root `/`.
