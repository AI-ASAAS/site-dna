"""Cross-page messaging, terminology, and offering consistency analyzer."""

from site_dna.schemas.content_marketing import ContentFinding, PageContentRecord


class ConsistencyAnalyzer:
    """Evaluates cross-page messaging alignment and detects conflicting statements."""

    @staticmethod
    def analyze(pages: list[PageContentRecord]) -> list[ContentFinding]:
        """Detect cross-page contradictions and naming inconsistencies."""
        if len(pages) <= 1:
            return []

        findings: list[ContentFinding] = []

        # Check for conflicting pricing statements (e.g. one page says "مجاني" and another says "مدفوع")
        all_texts = [(p.page_url, p.main_content.lower()) for p in pages]
        free_pages = [url for url, txt in all_texts if "مجاني" in txt or "free trial" in txt or "100% free" in txt]
        paid_pages = [
            url
            for url, txt in all_texts
            if "اشتراك شهري" in txt or "paid subscription" in txt or "pricing starts" in txt
        ]

        if free_pages and paid_pages and len(free_pages) != len(pages):
            findings.append(
                ContentFinding(
                    finding_id="CF-CNS01",
                    title="غموض في نموذج التسعير بين الصفحات (Pricing Model Ambiguity)",
                    category="messaging_clarity",
                    description="صفحات تروج للخدمة على أنها مجانية بالكامل بينما تشير صفحات أخرى لاشتراكات مدفوعة دون توضيح الفارق.",
                    page_url=free_pages[0],
                    evidence_ids=pages[0].source_evidence_ids[:2],
                    observation_type="derived",
                    severity="medium",
                    confidence_category="measured",
                )
            )

        return findings
