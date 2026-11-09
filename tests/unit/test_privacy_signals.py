"""Unit tests for Privacy Signals Analyzer in Site DNA Phase 09."""

from site_dna.analysis.security_privacy.privacy_signals import PrivacySignalsAnalyzer
from site_dna.schemas.security_privacy import SecurityPageRecord


def test_privacy_signals_comprehensive_disclosures():
    """Verify detection of privacy policy, cookie policy, contact email, user rights, and DPO."""
    analyzer = PrivacySignalsAnalyzer()

    page = SecurityPageRecord(
        page_url="https://example.com/privacy-policy",
        scheme="https",
        status_code=200,
    )

    crawl_dataset = {
        "pages": [
            {
                "url": "https://example.com/privacy-policy",
                "raw_html": """
                <html>
                <body>
                    <a href="/privacy-policy">سياسة الخصوصية Privacy Policy</a>
                    <a href="/cookie-policy">Cookie Policy</a>
                </body>
                </html>
                """,
                "text": "Privacy Policy Cookie Policy Data Protection Officer dpo@example.com under gdpr users have right to access and data retention and third party sharing.",
            }
        ]
    }

    assessment = analyzer.analyze([page], crawl_dataset=crawl_dataset)

    assert assessment.privacy_policy_found is True
    assert assessment.privacy_policy_url is not None
    assert assessment.cookie_policy_found is True
    assert assessment.privacy_contact_found is True
    assert assessment.user_rights_mentioned is True
    assert assessment.dpo_or_officer_mentioned is True
    assert assessment.data_retention_mentioned is True
    assert assessment.third_party_sharing_mentioned is True


def test_privacy_signals_missing():
    """Verify assessment when pages contain zero privacy disclosures."""
    analyzer = PrivacySignalsAnalyzer()
    page = SecurityPageRecord(
        page_url="https://empty.example.com/",
        scheme="https",
        status_code=200,
    )
    crawl_dataset = {
        "pages": [
            {
                "url": "https://empty.example.com/",
                "raw_html": "<html><body>Hello World</body></html>",
                "text": "Hello World",
            }
        ]
    }
    assessment = analyzer.analyze([page], crawl_dataset=crawl_dataset)
    assert assessment.privacy_policy_found is False
    assert assessment.cookie_policy_found is False
    assert assessment.privacy_contact_found is False
