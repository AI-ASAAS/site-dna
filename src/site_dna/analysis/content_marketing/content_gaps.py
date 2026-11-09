"""Content gap detection engine for identifying missing or unclear website copy."""

from site_dna.schemas.content_marketing import ContentGap, PageContentRecord


class ContentGapAnalyzer:
    """Identifies supported information gaps and missing customer context."""

    @staticmethod
    def analyze(pages: list[PageContentRecord]) -> list[ContentGap]:
        """Detect actionable content gaps from page records."""
        gaps: list[ContentGap] = []
        if not pages:
            return gaps

        home_page = next((p for p in pages if p.page_type == "home"), pages[0])

        # 1. Unclear core offering on homepage
        h1s = [h for h in home_page.headings if h.get("level") == 1]
        is_generic = any(
            g in home_page.main_content.lower() or any(g in h.get("text", "").lower() for h in h1s)
            for g in ["مرحباً", "welcome", "الأفضل لعملائنا"]
        )
        if home_page.word_count < 30 and (not h1s or is_generic):
            gaps.append(
                ContentGap(
                    gap_id="GAP-01",
                    gap_type="unclear_offering",
                    description="الصفحة الرئيسية تفتقر إلى شرح تفصيلي لطبيعة النشاط أو الخدمة المقدمة للزائر الجديد.",
                    page_url=home_page.page_url,
                    severity="high",
                    evidence_ids=home_page.source_evidence_ids[:2],
                )
            )

        # 2. Check for missing next-step guidance
        for p in pages:
            if not p.cta_candidates and p.page_type in ("services", "pricing"):
                gaps.append(
                    ContentGap(
                        gap_id=f"GAP-NXT-{p.page_id}",
                        gap_type="missing_next_step",
                        description=f"صفحة {p.page_type} ('{p.page_url}') تنتهي دون دعوة واضحة أو رابط للخطوة التالية.",
                        page_url=p.page_url,
                        severity="medium",
                        evidence_ids=p.source_evidence_ids[:2],
                    )
                )

        # 3. Check for pricing without figures or explanation
        pricing_pages = [p for p in pages if p.page_type == "pricing"]
        for pp in pricing_pages:
            if not any(char.isdigit() for char in pp.main_content) and "تواصل" not in pp.main_content:
                gaps.append(
                    ContentGap(
                        gap_id=f"GAP-PRC-{pp.page_id}",
                        gap_type="unanswered_question",
                        description=f"صفحة باقات الأسعار '{pp.page_url}' لا توضح أسعار الباقات أو آلية احتساب التكلفة للعميل.",
                        page_url=pp.page_url,
                        severity="medium",
                        evidence_ids=pp.source_evidence_ids[:2],
                    )
                )

        return gaps
