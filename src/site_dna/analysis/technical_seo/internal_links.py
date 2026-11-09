"""Internal link graph and anchor tag technical integrity analyzer."""

from site_dna.schemas.technical_seo import (
    TechnicalPageRecord,
    TechnicalSEOFinding,
)


class InternalLinksAnalyzer:
    """Audits crawlable anchor tags, malformed link schemes, and broken internal destinations."""

    @staticmethod
    def analyze(
        pages: list[TechnicalPageRecord],
    ) -> list[TechnicalSEOFinding]:
        """Audit anchor links across pages for crawlability and integrity."""
        findings: list[TechnicalSEOFinding] = []
        if not pages:
            return findings

        pages_by_url = {p.requested_url.rstrip("/"): p for p in pages}

        for p in pages:
            js_links = 0
            empty_links = 0
            for lnk in p.internal_links:
                clean = lnk.strip()
                if clean.lower().startswith("javascript:") or clean == "#":
                    js_links += 1
                elif not clean:
                    empty_links += 1
                else:
                    # Check if destination exists in crawled sample and returned an error
                    dest_norm = clean.rstrip("/")
                    target_page = pages_by_url.get(dest_norm)
                    if target_page and target_page.http_status >= 400:
                        findings.append(
                            TechnicalSEOFinding(
                                finding_id="TS-LNK-BROKEN-INTERNAL",
                                title=f"رابط داخلي يشير إلى صفحة عطلانة HTTP {target_page.http_status} (Broken Internal Link)",
                                category="internal_links",
                                description=f"الصفحة تحتوي على رابط داخلي يشير إلى صفحة تُرجع رمز فشل {target_page.http_status}: '{clean}'",
                                page_url=p.requested_url,
                                source_excerpt=clean,
                                evidence_ids=p.source_evidence_ids[:2],
                                observation_type="derived",
                                severity="high",
                                confidence_category="measured",
                                potential_technical_impact="تجربة مستخدم سلبية وتوقف تدفق روبوتات الزحف وفقدان قوة الروابط الداخلية.",
                                recommended_action="تحديث الرابط ليشير إلى الصفحة الصحيحة البديلة أو حذفه إذا كان المحتوى ملغى.",
                            )
                        )

            if js_links > 0:
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-LNK-JS-NAV",
                        title="روابط تعتمد على جافاسكربت وتفتقر لوسم href قياسي (JavaScript Navigation Link)",
                        category="internal_links",
                        description=f"الصفحة تحتوي على {js_links} رابط يعتمد على 'javascript:' أو '#' مما يعيق تتبع العناكب التلقائي.",
                        page_url=p.requested_url,
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="observed",
                        severity="medium",
                        confidence_category="observed",
                        potential_technical_impact="صعوبة استكشاف المسارات الداخلية للصفحات بواسطة روبوتات محركات البحث غير المتطورة في التصيير.",
                        recommended_action="استبدال روابط جافاسكربت بروابط معيارية <a href='/actual-path'> مع استخدام معالجات الأحداث تدريجياً.",
                    )
                )

        return findings
