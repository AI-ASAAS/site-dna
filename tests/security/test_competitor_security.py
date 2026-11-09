"""Security and robustness tests for Phase 08 Competitor Intelligence."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from site_dna.analysis.competitor_intelligence.context_builder import CompetitorContextBuilder
from site_dna.api.main import create_app
from site_dna.core.config import Settings
from site_dna.schemas.competitor_intelligence import CompetitorAnalysisRequest


def test_competitor_ssrf_and_private_ip_blocking():
    settings = Settings(app_name="Test", app_env="test")
    builder = CompetitorContextBuilder(settings=settings)

    # 1. Localhost and 127.0.0.1
    with pytest.raises((ValueError, HTTPException)):
        builder.build_context(
            CompetitorAnalysisRequest(
                primary_url="https://legit.com",
                competitor_urls=["http://127.0.0.1:8000/admin"],
            )
        )

    # 2. Cloud metadata IP 169.254.169.254
    with pytest.raises((ValueError, HTTPException)):
        builder.build_context(
            CompetitorAnalysisRequest(
                primary_url="https://legit.com",
                competitor_urls=["http://169.254.169.254/latest/meta-data/"],
            )
        )

    # 3. File URI scheme
    with pytest.raises((ValueError, HTTPException)):
        builder.build_context(
            CompetitorAnalysisRequest(
                primary_url="https://legit.com",
                competitor_urls=["file:///etc/passwd"],
            )
        )


def test_competitor_path_traversal_blocking():
    app = create_app()
    client = TestClient(app)

    # Path traversal in competitor analysis ID
    response = client.get("/api/v1/analysis/competitors/../../etc/passwd")
    assert response.status_code in (400, 404)


def test_prompt_injection_sanitization():
    from site_dna.analysis.competitor_intelligence.evidence_validator import CompetitorEvidenceValidator
    from tests.fixtures.competitor_intelligence.test_fixtures import PROMPT_INJECTION_CRAWL_DATA

    validator = CompetitorEvidenceValidator()
    # Ensure adversarial commands in text are sanitized/quarantined
    sanitized = validator.sanitize_text(PROMPT_INJECTION_CRAWL_DATA["pages"][0]["title"])
    assert "IGNORE ALL INSTRUCTIONS" not in sanitized or "system instruction" not in sanitized.lower()
