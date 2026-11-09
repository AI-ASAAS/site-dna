"""Brand voice, language consistency, and tone analyzer."""

from site_dna.schemas.content_marketing import (
    BrandVoiceAssessment,
    ContentFinding,
    PageContentRecord,
)


class VoiceAnalyzer:
    """Analyzes writing tone, dialectal presence, language harmony, and cross-page voice consistency."""

    DIALECT_KEYWORDS = {
        "saudi_gulf": ["حياك", "ودك", "أبشر", "عشان", "الحين", "وش", "سالفة"],
        "egyptian": ["عايز", "ازيك", "علشان", "دلوقتي", "كده"],
        "levantine": ["بدك", "شو", "هيك", "كتير", "منيح"],
    }

    FORMAL_KEYWORDS = ["السادة", "نحيطكم علماً", "يسرنا أن نعلن", "بموجب", "وفقاً لأحكام"]
    CONVERSATIONAL_KEYWORDS = ["معك", "أنت", "نساعدك", "رحلتك", "you", "we help", "your journey"]

    @classmethod
    def analyze(
        cls,
        pages: list[PageContentRecord],
    ) -> tuple[BrandVoiceAssessment, list[ContentFinding]]:
        """Audit tone, language harmony, and voice consistency."""
        if not pages:
            return BrandVoiceAssessment(cross_page_tone_consistency="not_assessed"), []

        findings: list[ContentFinding] = []
        all_text = " ".join(p.main_content for p in pages)
        evidence_ids = pages[0].source_evidence_ids[:3]

        # 1. Primary language & bilingual check
        has_arabic = any(ord(char) >= 0x0600 and ord(char) <= 0x06FF for char in all_text)
        has_english = any(char.isascii() and char.isalpha() for char in all_text)
        is_bilingual = has_arabic and has_english
        primary_lang = "ar" if has_arabic else "en"

        # 2. Dialect detection
        detected_dialect = None
        for dialect, kws in cls.DIALECT_KEYWORDS.items():
            if any(kw in all_text for kw in kws):
                detected_dialect = dialect
                break

        # 3. Tone classification
        observed_tone = "professional"
        has_formal = any(k in all_text for k in cls.FORMAL_KEYWORDS)
        has_conversational = any(k in all_text for k in cls.CONVERSATIONAL_KEYWORDS)

        if detected_dialect:
            observed_tone = "conversational"
        elif has_formal and not has_conversational:
            observed_tone = "formal"
        elif has_conversational:
            observed_tone = "conversational"

        # 4. Cross-page tone consistency
        cross_consistency = "consistent"
        if len(pages) == 1:
            cross_consistency = "not_assessed"
        else:
            page_tones = []
            for p in pages:
                txt = p.main_content
                if any(k in txt for k in cls.FORMAL_KEYWORDS):
                    page_tones.append("formal")
                elif any(k in txt for k in cls.CONVERSATIONAL_KEYWORDS):
                    page_tones.append("conversational")
                else:
                    page_tones.append("professional")

            if len(set(page_tones)) > 1 and "formal" in page_tones and "conversational" in page_tones:
                cross_consistency = "inconsistent"
                findings.append(
                    ContentFinding(
                        finding_id="CF-VOC01",
                        title="تباين ملحوظ في نبرة الخطاب بين صفحات الموقع (Tone Inconsistency)",
                        category="brand_voice",
                        description="لوحظ تفاوت في نبرة الصوت بين أسلوب رسمي جداً في بعض الصفحات وأسلوب ودي غير رسمي في صفحات أخرى.",
                        page_url=pages[0].page_url,
                        evidence_ids=evidence_ids[:2],
                        observation_type="derived",
                        severity="low",
                        confidence_category="measured",
                    )
                )

        assessment = BrandVoiceAssessment(
            observed_tone=observed_tone,
            primary_language=primary_lang,
            dialect_detected=detected_dialect,
            is_bilingual=is_bilingual,
            cross_page_tone_consistency=cross_consistency,
            evidence_ids=evidence_ids[:10],
        )

        return assessment, findings
