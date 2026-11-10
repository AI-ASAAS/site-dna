"""Unit tests for AI & Automation Readiness and Optimization Analyzer."""

import json
from pathlib import Path
import pytest

from site_dna.analysis.ai_automation.analyzer import AIAutomationAnalyzer
from site_dna.schemas.ai_automation import AIAutomationReport


def test_ai_automation_analyzer_detects_chatbot(tmp_path: Path):
    """Verify that multi-layer inspection identifies chatbot from buttons, images, and visual DOM elements."""
    run_dir = tmp_path / "run-test-present"
    run_dir.mkdir()

    # Mock crawl.json with chatbot buttons and images
    crawl_data = {
        "website_info": {"initial_url": "https://ecogreen.com.my/"},
        "pages": [
            {
                "url": "https://ecogreen.com.my/",
                "title": "Eco Green Sustainable Landscaping",
                "meta_description": "Vertical gardens and green walls",
                "raw_text_preview": "Welcome to Eco Green. Talk to our specialist.",
                "headings": ["Innovative Green Systems"],
                "buttons": ["Start designing", "AI"],
                "images": [{"src": "https://ecogreen.com.my/images/chatbot.webp", "alt": "Chatbot"}],
                "forms": ["chat-form"],
            }
        ],
    }
    (run_dir / "crawl.json").write_text(json.dumps(crawl_data), encoding="utf-8")

    # Mock visual.json with DOM elements
    vis_dir = run_dir / "visual" / "vis-001"
    vis_dir.mkdir(parents=True)
    visual_data = {
        "pages": [
            {
                "dom_elements": [
                    {
                        "accessible_name": "Open AI assistant",
                        "classes": ["chat-fab", "has-avatar"],
                        "attributes": {"aria-label": "Open AI assistant"},
                    }
                ]
            }
        ]
    }
    (vis_dir / "visual.json").write_text(json.dumps(visual_data), encoding="utf-8")

    analyzer = AIAutomationAnalyzer(base_dir=tmp_path)
    report = analyzer.analyze_run("run-test-present")

    assert isinstance(report, AIAutomationReport)
    assert report.status == "present"
    assert report.has_chatbot is True
    assert report.maturity_score >= 80.0
    assert "Eco Assistant" in report.headline_ar or "روبوت محادثة" in report.headline_ar
    assert len(report.detected_evidences) >= 2
    assert len(report.proposals) >= 4
    # Proposals should include Vision AI and Function calling
    proposal_ids = [p.id for p in report.proposals]
    assert "AIP-01" in proposal_ids
    assert any(p.type == "multimodal_upgrade" for p in report.proposals)


def test_ai_automation_analyzer_detects_absent(tmp_path: Path):
    """Verify that a site with no AI/chatbot indicators produces an absent report with adoption blueprint."""
    run_dir = tmp_path / "run-test-absent"
    run_dir.mkdir()

    crawl_data = {
        "website_info": {"initial_url": "https://traditional-sports.example.com/"},
        "pages": [
            {
                "url": "https://traditional-sports.example.com/",
                "title": "Sports News and Highlights",
                "meta_description": "Watch football highlights and matches",
                "raw_text_preview": "Scores, tables, and fixtures for football leagues.",
                "headings": ["Premier League Table", "Latest Fixtures"],
                "buttons": ["Subscribe", "Read More"],
                "images": [{"src": "https://example.com/logo.png", "alt": "Logo"}],
                "forms": [],
            }
        ],
    }
    (run_dir / "crawl.json").write_text(json.dumps(crawl_data), encoding="utf-8")

    analyzer = AIAutomationAnalyzer(base_dir=tmp_path)
    report = analyzer.analyze_run("run-test-absent")

    assert isinstance(report, AIAutomationReport)
    assert report.status == "absent"
    assert report.has_chatbot is False
    assert report.maturity_score <= 30.0
    assert "يفتقر" in report.headline_ar
    assert len(report.proposals) >= 4
    # Absent site should receive P1 adoption proposals
    p1_proposals = [p for p in report.proposals if p.priority == "P1"]
    assert len(p1_proposals) >= 2
    assert any(p.type == "chatbot" for p in p1_proposals)
