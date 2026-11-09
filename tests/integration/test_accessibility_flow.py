"""Integration tests for AccessibilityFlow and service execution."""

import json
from pathlib import Path

from site_dna.flows.accessibility_flow import AccessibilityFlow


def test_accessibility_flow_execution(tmp_path: Path, monkeypatch):
    """Verify that AccessibilityFlow runs end-to-end in deterministic mode."""
    runs_dir = tmp_path / "runs"
    crawl_dir = runs_dir / "crawl-flow-acc-01"
    crawl_dir.mkdir(parents=True)

    crawl_payload = {
        "target_url": "https://flow-acc.example.com/",
        "website_info": {"canonical_origin": "https://flow-acc.example.com"},
        "pages": [
            {
                "url": "https://flow-acc.example.com/",
                "status_code": 200,
                "headers": {"content-type": "text/html"},
                "cookies": [],
                "raw_html": """<!doctype html>
<html lang="ar" dir="rtl">
<head><title>منصة التدفق</title></head>
<body>
  <header><nav aria-label="رئيسي"><a href="/">الرئيسية</a></nav></header>
  <main>
    <h1>تدفق اختبار النفاذ</h1>
    <p>محتوى متوافق مع لوحة المفاتيح والتباين.</p>
  </main>
</body>
</html>""",
            }
        ],
    }
    (crawl_dir / "crawl.json").write_text(json.dumps(crawl_payload), encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    flow = AccessibilityFlow(
        crawl_run_id="crawl-flow-acc-01",
        deterministic_only=True,
        offline_mode=True,
    )

    result_state = flow.kickoff()

    assert result_state.execution_status == "completed"
    assert result_state.report is not None
    assert result_state.report.crawl_run_id == "crawl-flow-acc-01"
    assert result_state.report.scores.overall_score is not None
    assert (crawl_dir / "analysis" / "accessibility").exists()
