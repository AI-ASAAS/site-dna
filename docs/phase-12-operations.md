# Site DNA — Phase 12: Operations & Maintenance Manual

**Organization:** ASAAS AI — أساس للذكاء الاصطناعي  
**Product:** Site DNA — بصمة الموقع  
**Version:** v1.0.0-rc.1  

---

## 1. Routine Run Management & Retention

Reports and analysis runs are stored in the structured directory `runs/<run_id>/`.

To manage disk usage in production environments:
```powershell
# List existing runs and their disk sizes
Get-ChildItem -Directory runs | Select-Object Name, @{Name="SizeMB";Expression={(Get-ChildItem $_.FullName -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB}}

# Archive old runs older than 30 days
$cutoff = (Get-Date).AddDays(-30)
Get-ChildItem -Directory runs | Where-Object { $_.LastWriteTime -lt $cutoff } | Move-Item -Destination "archives/"
```

## 2. CLI Export Operations

To export a report on demand from the terminal:
```powershell
# Export A4 PDF in Arabic
uv run python -m site_dna.cli export-report --analysis-run-id "crawl-a" --format pdf --language ar --output "exports/report.pdf"

# Export Markdown executive report
uv run python -m site_dna.cli export-report --analysis-run-id "crawl-a" --format md --language ar --report-mode executive

# Export structured JSON data
uv run python -m site_dna.cli export-report --analysis-run-id "crawl-a" --format json
```

## 3. Monitoring Health & AI Quotas

- **Health check endpoint:** `GET /api/v1/health`
- **Agent readiness:** `GET /api/v1/agents`
- **Daily quota monitoring:** When the free tier limit is reached, Site DNA gracefully falls soft to deterministic analysis, recording `status: ai_blocked` without crashing or throwing unhandled errors.
