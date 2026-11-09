"""Unit tests for VoiceAnalyzer."""

from pathlib import Path

from site_dna.analysis.content_marketing.context_builder import ContentContextBuilder
from site_dna.analysis.content_marketing.voice_analyzer import VoiceAnalyzer

FIXTURES_DIR = Path("tests/fixtures/content_marketing")


def test_voice_analysis_fixture_e_dialect_and_bilingual():
    """Verify that Fixture E detects dialect and bilingual content without error."""
    base_dir = FIXTURES_DIR / "fixture_e_bilingual_dialect" / "runs"
    builder = ContentContextBuilder(base_dir=str(base_dir))
    pages, _, _, _ = builder.build_context(crawl_run_id="crawl-e")

    assessment, findings = VoiceAnalyzer.analyze(pages)

    assert assessment.dialect_detected == "saudi_gulf"
    assert assessment.is_bilingual is True
    assert assessment.observed_tone == "conversational"
