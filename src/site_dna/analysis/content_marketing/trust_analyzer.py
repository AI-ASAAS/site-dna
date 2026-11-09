"""Trust signals, credibility indicators, and marketing claims analyzer."""

import re

from site_dna.schemas.content_marketing import (
    ContentFinding,
    PageContentRecord,
    TrustClaimRecord,
)


class TrustAnalyzer:
    """Inventories visible credibility indicators, builds claim provenance, and evaluates transparency."""

    STATISTICAL_PATTERN = re.compile(
        r"(\b\d{1,3}(?:,\d{3})*\+?\s*(?:عميل|مستخدم|شركة|مشروع|ريال|دولار|clients|users|projects|customers|satisfaction|%)\b[^\.\n]*)",
        re.IGNORECASE,
    )

    SENSITIVE_DOMAINS = [
        "طب",
        "صحة",
        "استثمار",
        "أرباح",
        "قانون",
        "health",
        "cure",
        "invest",
        "guaranteed profit",
        "legal",
    ]

    @classmethod
    def analyze(
        cls,
        pages: list[PageContentRecord],
    ) -> tuple[list[TrustClaimRecord], list[ContentFinding]]:
        """Extract credibility claims and audit trust transparency."""
        claims: list[TrustClaimRecord] = []
        findings: list[ContentFinding] = []

        has_about = any(
            p.page_type == "about" or "من نحن" in p.main_content or "about" in p.page_url.lower() for p in pages
        )
        has_contact = any(
            p.page_type == "contact" or "اتصل" in p.main_content or "contact" in p.page_url.lower() for p in pages
        )

        home_page = next((p for p in pages if p.page_type == "home"), pages[0] if pages else None)
        evidence_ids = home_page.source_evidence_ids[:3] if home_page else []

        # 1. Missing About or Contact
        if not has_about:
            findings.append(
                ContentFinding(
                    finding_id="CF-TRST-NOABT",
                    title="غياب صفحة أو قسم تعريفي بالمؤسسة (Missing About Information)",
                    category="trust_claims",
                    description="لم يتم العثور على صفحة 'من نحن' أو قسم يعرف بفريق العمل والجهة المسؤولة عن الموقع.",
                    page_url=home_page.page_url if home_page else "https://unknown",
                    evidence_ids=evidence_ids[:2],
                    observation_type="derived",
                    severity="medium",
                    confidence_category="measured",
                )
            )

        if not has_contact:
            findings.append(
                ContentFinding(
                    finding_id="CF-TRST-NOCON",
                    title="غياب بيانات أو قنوات تواصل واضحة (Missing Direct Contact Info)",
                    category="trust_claims",
                    description="لم يتم رصد وسائل تواصل مباشرة (بريد، هاتف، أو صفحة اتصل بنا) ضمن الصفحات المستكشفة.",
                    page_url=home_page.page_url if home_page else "https://unknown",
                    evidence_ids=evidence_ids[:2],
                    observation_type="derived",
                    severity="high",
                    confidence_category="measured",
                )
            )

        # 2. Extract Numerical and Performance Claims
        claim_counter = 0
        for p in pages:
            matches = cls.STATISTICAL_PATTERN.findall(p.main_content)
            for m in matches[:3]:
                claim_counter += 1
                c_text = m.strip()[:140]
                claim_id = f"CLM-{claim_counter:02d}"

                # Check if sensitive
                is_sensitive = any(s in c_text.lower() for s in cls.SENSITIVE_DOMAINS)

                claims.append(
                    TrustClaimRecord(
                        claim_id=claim_id,
                        claim_text=c_text,
                        claim_type="performance_claim" if "%" in c_text or "نجاح" in c_text else "credential_claim",
                        page_url=p.page_url,
                        source_evidence_ids=p.source_evidence_ids[:2],
                        supporting_onsite_references=[],
                        verification_status="observed_only",
                        review_required=is_sensitive,
                    )
                )

                findings.append(
                    ContentFinding(
                        finding_id=f"CF-TRST-CLM{claim_counter}",
                        title=f"ادعاء إحصائي أو رقمي بحاجة لإثبات مرجعي ({claim_id})",
                        category="trust_claims",
                        description=f"ذكر إحصائية أو إنجاز رقمي '{c_text}' دون تقديم رابط أو وثيقة إثباتية تسند الرقم.",
                        page_url=p.page_url,
                        source_excerpt=c_text,
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="observed",
                        severity="medium" if not is_sensitive else "high",
                        confidence_category="observed",
                        potential_communication_impact="قد يتشكك الزائر في دقة الأرقام التسويقية في حال عدم توثيق مصدرها.",
                    )
                )

        return claims, findings
