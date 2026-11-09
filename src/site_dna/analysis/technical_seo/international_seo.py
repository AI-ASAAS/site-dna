"""International SEO, language tags, and hreflang annotations analysis engine."""

from site_dna.schemas.technical_seo import (
    InternationalSEOAssessment,
    TechnicalPageRecord,
    TechnicalSEOFinding,
)


class InternationalSEOAnalyzer:
    """Evaluates html lang, hreflang annotations, x-default, and reciprocal alternate references."""

    @staticmethod
    def analyze(
        pages: list[TechnicalPageRecord],
    ) -> tuple[InternationalSEOAssessment, list[TechnicalSEOFinding]]:
        """Audit language declarations and hreflang reciprocal links."""
        if not pages:
            return InternationalSEOAssessment(), []

        findings: list[TechnicalSEOFinding] = []
        evidence_ids = pages[0].source_evidence_ids[:3]

        primary_lang = pages[0].html_lang or "ar"
        total_hreflang = sum(len(p.hreflang_links) for p in pages)
        reciprocal_valid = True
        x_default_present = False

        # If hreflang is present on any page, evaluate reciprocal links
        if total_hreflang > 0:
            pages_by_url = {p.requested_url.rstrip("/"): p for p in pages}
            for p in pages:
                for h in p.hreflang_links:
                    lang_code = h.get("lang", "").lower()
                    alt_url = h.get("href", "").rstrip("/")
                    if lang_code == "x-default":
                        x_default_present = True

                    # Reciprocal check within collected sample
                    target = pages_by_url.get(alt_url)
                    if target:
                        has_return = any(
                            rh.get("href", "").rstrip("/") == p.requested_url.rstrip("/")
                            for rh in target.hreflang_links
                        )
                        if not has_return:
                            reciprocal_valid = False
                            findings.append(
                                TechnicalSEOFinding(
                                    finding_id="TS-INT-NO-RETURN",
                                    title="غياب الرابط التبادلي في وسم hreflang (Missing Reciprocal hreflang)",
                                    category="international_seo",
                                    description=f"الصفحة تشير إلى بديل لغوي '{alt_url}' دون وجود إشارة تبادلية عكسية في الصفحة البديلة.",
                                    page_url=p.requested_url,
                                    source_excerpt=f"{lang_code} -> {alt_url}",
                                    evidence_ids=p.source_evidence_ids[:2],
                                    observation_type="derived",
                                    severity="medium",
                                    confidence_category="derived",
                                    potential_technical_impact="تجاهل محركات البحث لوسوم hreflang بالكامل وفق اشتراطات Google الصارمة للتبادلية.",
                                    recommended_action="التأكد من أن كل صفحة بديلة تحتوي على نفس مجموعة وسوم hreflang كاملة بما فيها الإشارة لنفسها وللصفحة المصدر.",
                                )
                            )

        assessment = InternationalSEOAssessment(
            html_lang_declared=primary_lang,
            hreflang_count=total_hreflang,
            reciprocal_annotations_valid=reciprocal_valid,
            x_default_present=x_default_present,
            bilingual_parity="single_language" if total_hreflang == 0 else "multilingual",
            evidence_ids=evidence_ids,
            findings=[f.title for f in findings],
        )

        return assessment, findings
