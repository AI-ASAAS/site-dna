"""Call-to-Action (CTA) copywriting, clarity, and consistency analyzer."""

from site_dna.schemas.content_marketing import (
    ContentFinding,
    CTAContentAssessment,
    PageContentRecord,
)


class CTAContentAnalyzer:
    """Audits CTA wording, actionability, generic phrasing, and destination alignment."""

    GENERIC_CTAS = {
        "اضغط هنا",
        "انقر هنا",
        "المزيد",
        "اقرأ المزيد",
        "هنا",
        "تفاصيل",
        "رابط",
        "click here",
        "click",
        "read more",
        "more",
        "here",
        "details",
        "link",
        "learn more",
    }

    ACTIONABLE_VERBS = [
        "ابدأ",
        "احجز",
        "سجل",
        "انضم",
        "تواصل",
        "اطلب",
        "حمّل",
        "جرّب",
        "اشترك",
        "start",
        "book",
        "register",
        "join",
        "contact",
        "order",
        "download",
        "try",
        "subscribe",
    ]

    @classmethod
    def analyze(
        cls,
        pages: list[PageContentRecord],
    ) -> tuple[CTAContentAssessment, list[ContentFinding]]:
        """Audit Call-to-Action buttons and links across all pages."""
        findings: list[ContentFinding] = []
        all_ctas: list[dict] = []
        evidence_ids: list[str] = []

        for p in pages:
            for cta in p.cta_candidates:
                all_ctas.append({**cta, "page_url": p.page_url})
            evidence_ids.extend(p.source_evidence_ids[:2])

        total_ctas = len(all_ctas)
        unique_labels = sorted(list({c.get("text", "").strip() for c in all_ctas if c.get("text")}))

        # 1. Count generic CTAs
        generic_count = 0
        for label in unique_labels:
            if label.lower() in cls.GENERIC_CTAS:
                generic_count += 1
                sample_cta = next((c for c in all_ctas if c.get("text", "").strip() == label), None)
                p_url = sample_cta.get("page_url") if sample_cta else pages[0].page_url
                findings.append(
                    ContentFinding(
                        finding_id=f"CF-CTA-GEN-{generic_count}",
                        title=f"استخدام صياغة CTA عامة وغير محددة ('{label}')",
                        category="cta_action",
                        description=f"العبارة '{label}' عبارة مبهمة تفتقر إلى تحديد القيمة أو النتيجة المتوقعة من النقر.",
                        page_url=p_url,
                        source_excerpt=label,
                        evidence_ids=evidence_ids[:2],
                        observation_type="observed",
                        severity="medium",
                        confidence_category="observed",
                        potential_communication_impact="انخفاض الدافعية للنقر بسبب عدم وضوح الخطوة اللاحقة للزائر.",
                    )
                )

        # 2. Check for Primary CTA on Homepage
        home_page = next((p for p in pages if p.page_type == "home"), pages[0] if pages else None)
        primary_cta_found = False
        if home_page:
            for cta in home_page.cta_candidates:
                txt = cta.get("text", "").lower()
                if any(verb in txt for verb in cls.ACTIONABLE_VERBS):
                    primary_cta_found = True
                    break

        if not primary_cta_found and home_page:
            findings.append(
                ContentFinding(
                    finding_id="CF-CTA-NOPRIM",
                    title="غياب دعوة واضحة لاتخاذ إجراء رئيسي في الصفحة الرئيسية (Missing Primary CTA)",
                    category="cta_action",
                    description="الصفحة الرئيسية لا تحتوي على زر أو رابط حث رئيسي يوجه الزائر نحو الإجراء المستهدف التالي بوضوح.",
                    page_url=home_page.page_url,
                    evidence_ids=home_page.source_evidence_ids[:2],
                    observation_type="derived",
                    severity="high",
                    confidence_category="measured",
                )
            )

        # 3. Inconsistent destinations (same label pointing to multiple URLs)
        label_to_urls: dict[str, set[str]] = {}
        for c in all_ctas:
            txt = c.get("text", "").strip()
            dest = c.get("url")
            if txt and dest and txt not in cls.GENERIC_CTAS:
                label_to_urls.setdefault(txt, set()).add(dest)

        inconsistent_count = sum(1 for urls in label_to_urls.values() if len(urls) > 1)

        assessment = CTAContentAssessment(
            total_ctas_observed=total_ctas,
            unique_cta_labels=unique_labels[:20],
            generic_ctas_count=generic_count,
            primary_cta_identified=primary_cta_found,
            inconsistent_destinations_count=inconsistent_count,
            evidence_ids=evidence_ids[:10],
        )

        return assessment, findings
