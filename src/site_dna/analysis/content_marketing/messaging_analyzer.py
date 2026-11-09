"""Marketing messaging and headline clarity analyzer."""

from site_dna.schemas.content_marketing import (
    ContentFinding,
    MessagingAssessment,
    PageContentRecord,
)


class MessagingAnalyzer:
    """Evaluates the clarity, specificity, and quality of marketing copy and headlines."""

    GENERIC_HEADLINES = {
        "welcome",
        "home",
        "homepage",
        "untitled",
        "main",
        "مرحباً",
        "اهلا بكم",
        "أهلاً وسهلاً",
        "الصفحة الرئيسية",
        "الرئيسية",
    }

    BUZZWORDS = [
        "حلول ثورية",
        "الجيل القادم",
        "ريادة لا مثيل لها",
        "منظومة متكاملة ذكية لا نهائية",
        "paradigm shift",
        "synergy",
        "next-gen revolutionary",
        "disruptive cutting-edge",
        "game-changing",
    ]

    ABSOLUTE_TERMS = [
        "100%",
        "الأفضل دائماً",
        "الأول عالمياً",
        "بدون منازع",
        "مضمون تماماً",
        "guaranteed 100%",
        "unbeatable",
        "flawless",
        "zero risk",
        "absolute best",
    ]

    @classmethod
    def analyze(
        cls,
        pages: list[PageContentRecord],
    ) -> tuple[MessagingAssessment, list[ContentFinding]]:
        """Audit marketing headlines and copy messaging."""
        if not pages:
            return MessagingAssessment(headline_clarity="absent"), []

        home_page = next((p for p in pages if p.page_type == "home"), pages[0])
        findings: list[ContentFinding] = []
        evidence_ids = list(home_page.source_evidence_ids)

        # 1. Headline & Subheadline extraction
        h1s = [h.get("text", "").strip() for h in home_page.headings if h.get("level") == 1]
        h2s = [h.get("text", "").strip() for h in home_page.headings if h.get("level") == 2]

        hero_headline = h1s[0] if h1s else (home_page.page_title or None)
        hero_subheadline = h2s[0] if h2s else (home_page.meta_description or None)

        # 2. Headline clarity evaluation
        headline_clarity = "clear"
        if not hero_headline:
            headline_clarity = "absent"
            findings.append(
                ContentFinding(
                    finding_id="CF-MSG01",
                    title="غياب عنوان ترويجي رئيسي (Missing Hero Headline)",
                    category="messaging_clarity",
                    description="الصفحة الرئيسية لا تحتوي على عنوان رئيسي بارز يحدد رسالة الموقع الأساسية.",
                    page_url=home_page.page_url,
                    evidence_ids=evidence_ids[:2],
                    observation_type="observed",
                    severity="high",
                    confidence_category="observed",
                )
            )
        elif (
            hero_headline.lower().strip() in cls.GENERIC_HEADLINES
            or len(hero_headline.split()) < 2
            or any(gen in hero_headline.lower() for gen in ["مرحباً", "welcome", "أهلاً", "الصفحة الرئيسية"])
        ):
            headline_clarity = "ambiguous"
            findings.append(
                ContentFinding(
                    finding_id="CF-MSG02",
                    title="عنوان رئيسي مبهم أو عام يفتقر للتحديد (Ambiguous Generic Headline)",
                    category="messaging_clarity",
                    description=f"العنوان الرئيسي '{hero_headline}' عام ولا يوضح طبيعة المنتج أو الخدمة أو الميزة التنافسية.",
                    page_url=home_page.page_url,
                    source_excerpt=hero_headline,
                    evidence_ids=evidence_ids[:2],
                    observation_type="observed",
                    severity="high",
                    confidence_category="observed",
                    potential_communication_impact="عدم تكوين انطباع أولي واضح لدى الزائر عند أول 5 ثوانٍ من التصفح.",
                )
            )

        # 3. Buzzwords & Jargon Check
        all_text = " ".join(p.main_content for p in pages).lower()
        jargon_matches = [b for b in cls.BUZZWORDS if b in all_text]
        jargon_level = "low"
        if len(jargon_matches) >= 3:
            jargon_level = "excessive"
            findings.append(
                ContentFinding(
                    finding_id="CF-MSG03",
                    title="إفراط في استخدام المصطلحات الرنانة المبهمة (Excessive Marketing Jargon)",
                    category="messaging_clarity",
                    description=f"رصد تكرار عبارات رنانة عامة دون شرح عملي: {', '.join(jargon_matches[:3])}",
                    page_url=home_page.page_url,
                    evidence_ids=evidence_ids[:2],
                    observation_type="derived",
                    severity="medium",
                    confidence_category="measured",
                )
            )
        elif len(jargon_matches) >= 1:
            jargon_level = "moderate"

        # 4. Absolute / Exaggerated Claims
        absolute_count = 0
        for abs_term in cls.ABSOLUTE_TERMS:
            if abs_term in all_text:
                absolute_count += 1
                findings.append(
                    ContentFinding(
                        finding_id=f"CF-MSG-ABS-{absolute_count}",
                        title=f"استخدام وعود قطعية غير مدعومة ({abs_term})",
                        category="trust_claims",
                        description=f"استخدام صياغات جازمة ومطلقة '{abs_term}' قد تصنف كوعود مبالغ فيها قانونياً أو تسويقياً دون إثبات.",
                        page_url=home_page.page_url,
                        evidence_ids=evidence_ids[:2],
                        observation_type="observed",
                        severity="medium",
                        confidence_category="observed",
                    )
                )

        # 5. Repeated phrases across pages
        repeated_phrases: list[str] = []
        if len(pages) > 1:
            all_h2s = [
                h.get("text", "").strip()
                for p in pages
                for h in p.headings
                if h.get("level") == 2 and len(h.get("text", "").split()) >= 3
            ]
            seen = set()
            for h in all_h2s:
                if h in seen and h not in repeated_phrases:
                    repeated_phrases.append(h)
                seen.add(h)

        assessment = MessagingAssessment(
            hero_headline=hero_headline,
            hero_subheadline=hero_subheadline,
            headline_clarity=headline_clarity,
            jargon_level=jargon_level,
            absolute_claims_count=absolute_count,
            repeated_phrases=repeated_phrases[:5],
            evidence_ids=evidence_ids[:10],
        )

        return assessment, findings
