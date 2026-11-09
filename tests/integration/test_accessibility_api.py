"""Integration tests for Site DNA Phase 10 Accessibility FastAPI endpoints."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from site_dna.api.main import app


@pytest.fixture
def client():
    """Create a FastAPI TestClient instance."""
    return TestClient(app)


def test_accessibility_api_lifecycle(tmp_path: Path, monkeypatch, client: TestClient):
    """Verify POST, GET, GET /wcag, and task update endpoints for accessibility."""
    runs_dir = tmp_path / "runs"
    crawl_dir = runs_dir / "crawl-acc-test-01"
    crawl_dir.mkdir(parents=True)

    crawl_payload = {
        "target_url": "https://acc-test.example.com/",
        "website_info": {"canonical_origin": "https://acc-test.example.com"},
        "pages": [
            {
                "url": "https://acc-test.example.com/",
                "status_code": 200,
                "headers": {"content-type": "text/html; charset=utf-8"},
                "cookies": [],
                "raw_html": """<!doctype html>
<html lang="ar" dir="rtl">
<head><title>صفحة اختبار النفاذ</title></head>
<body>
  <header><nav aria-label="رئيسي"><a href="/">الرئيسية</a></nav></header>
  <main>
    <h1>عنوان رئيسي سليم</h1>
    <p>نص تجريبي لاختبار مسار التكامل.</p>
    <form action="/test" method="post">
      <label for="f-name">الاسم:</label>
      <input type="text" id="f-name" name="name" required>
      <button type="submit">إرسال</button>
    </form>
  </main>
</body>
</html>""",
            }
        ],
    }
    (crawl_dir / "crawl.json").write_text(json.dumps(crawl_payload), encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    # 1. Trigger accessibility analysis via POST
    trigger_resp = client.post(
        "/api/v1/analysis/accessibility",
        json={
            "crawl_run_id": "crawl-acc-test-01",
            "deterministic_only": True,
            "max_pages": 4,
        },
    )
    assert trigger_resp.status_code == 201
    report = trigger_resp.json()
    assert report["crawl_run_id"] == "crawl-acc-test-01"
    assert report["target_url"] == "https://acc-test.example.com/"
    assert "scores" in report
    assert report["scores"]["overall_score"] is not None

    # 2. Retrieve generated report via GET
    get_resp = client.get("/api/v1/analysis/accessibility/crawl-acc-test-01")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["crawl_run_id"] == "crawl-acc-test-01"
    assert len(retrieved["wcag_criteria"]) >= 10

    # 3. Retrieve WCAG criteria via GET /wcag
    wcag_resp = client.get("/api/v1/analysis/accessibility/crawl-acc-test-01/wcag")
    assert wcag_resp.status_code == 200
    criteria_list = wcag_resp.json()
    assert isinstance(criteria_list, list)
    assert len(criteria_list) >= 10

    # 4. Update manual review task via POST /tasks/{review_id}
    tasks = retrieved.get("manual_review_tasks", [])
    if tasks:
        task_id = tasks[0]["review_id"]
        update_resp = client.post(
            f"/api/v1/analysis/accessibility/crawl-acc-test-01/tasks/{task_id}",
            json={
                "status": "passed",
                "notes": "تم التحقق اليدوي بنجاح عبر قارئ الشاشة",
                "reviewer": "خبير النفاذ الرقمي",
            },
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        assert updated["status"] == "passed"
        assert updated["reviewer"] == "خبير النفاذ الرقمي"
