"""Value proposition and business offering analysis engine."""

import re

from site_dna.schemas.content_marketing import (
    ContentFinding,
    PageContentRecord,
    ValuePropositionAssessment,
)


class ValuePropositionAnalyzer:
    """Evaluates how clearly a website communicates what it offers, benefits, and differentiators."""

    @staticmethod
    def analyze(
        pages: list[PageContentRecord],
    ) -> tuple[ValuePropositionAssessment, list[ContentFinding]]:
        """Evaluate value proposition and return assessment plus grounded findings."""
        if not pages:
            return ValuePropositionAssessment(clarity_rating="unclear"), []

        home_page = next((p for p in pages if p.page_type == "home"), pages[0])
        findings: list[ContentFinding] = []
        evidence_ids = list(home_page.source_evidence_ids)

        # 1. Offering candidate: prefer H1 text, else meta description, else first paragraph
        h1_headings = [h.get("text", "").strip() for h in home_page.headings if h.get("level") == 1]
        hero_h1 = h1_headings[0] if h1_headings else None
        meta_desc = home_page.meta_description.strip() if home_page.meta_description else None

        offering_summary = None
        if hero_h1 and len(hero_h1.split()) >= 3:
            offering_summary = hero_h1
        elif meta_desc and len(meta_desc.split()) >= 4:
            offering_summary = meta_desc
        elif home_page.paragraphs:
            first_p = home_page.paragraphs[0].get("text", "").strip()
            if first_p:
                offering_summary = first_p[:150]

        # 2. Extract benefits
        benefits: list[str] = []
        benefit_patterns = [
            r"([^\.\n]*(?:زيادة|توفير|تسريع|تحسين|تسهيل|تمكين)[^\.\n]*)",
            r"([^\.\n]*(?:increase|save|accelerate|improve|boost|streamline|empower)[^\.\n]*)",
        ]
        for pattern in benefit_patterns:
            matches = re.findall(pattern, home_page.main_content, re.IGNORECASE)
            for m in matches[:5]:
                clean_m = m.strip()
                if len(clean_m) > 10 and clean_m not in benefits:
                    benefits.append(clean_m[:120])

        # 3. Extract claimed differentiators
        differentiators: list[str] = []
        diff_patterns = [
            r"([^\.\n]*(?:الوحيد|أول|الأفضل|حصري|الرائد|رقم واحد)[^\.\n]*)",
            r"([^\.\n]*(?:only|first|#1|leading|exclusive|unique|best)[^\.\n]*)",
        ]
        for pattern in diff_patterns:
            matches = re.findall(pattern, home_page.main_content, re.IGNORECASE)
            for m in matches[:5]:
                clean_m = m.strip()
                if len(clean_m) > 8 and clean_m not in differentiators:
                    differentiators.append(clean_m[:120])

        # 4. Target audience
        target_audience = None
        aud_matches = re.findall(
            r"([^\.\n]*(?:للشركات|للأفراد|للمطورين|للمصممين|لأصحاب العمل|for business|for teams|for developers|for creators)[^\.\n]*)",
            home_page.main_content,
            re.IGNORECASE,
        )
        if aud_matches:
            target_audience = aud_matches[0].strip()[:100]

        # 5. Clarity evaluation
        generic_terms = ["مرحباً", "welcome", "أهلاً", "الصفحة الرئيسية", "الرئيسية", "home"]
        is_generic_h1 = bool(hero_h1 and any(g in hero_h1.lower() for g in generic_terms))

        clarity_rating = "moderate"
        if (not hero_h1 and not meta_desc and home_page.word_count < 40) or (
            is_generic_h1 and home_page.word_count < 40
        ):
            clarity_rating = "unclear"
            findings.append(
                ContentFinding(
                    finding_id="CF-VP01",
                    title="غياب بيان واضح عن القيمة المقترحة وطبيعة النشاط (Unclear Value Proposition)",
                    category="value_proposition",
                    description="الصفحة الرئيسية تفتقر إلى عنوان رئيسي أو وصف يشرح طبيعة ما تقدمه المؤسسة بشكل مباشر للزائر، أو تكتفي بترحيب عام مبهم.",
                    page_url=home_page.page_url,
                    source_excerpt=hero_h1 or (home_page.main_content[:150] if home_page.main_content else None),
                    evidence_ids=evidence_ids[:3],
                    observation_type="derived",
                    severity="high",
                    confidence_category="measured",
                    potential_communication_impact="صعوبة فهم الزائر لطبيعة عمل الموقع فور وصوله، مما يزيد من معدلات الارتداد.",
                )
            )
        elif hero_h1 and not is_generic_h1 and len(hero_h1.split()) >= 3 and len(benefits) >= 1:
            clarity_rating = "clear"
        elif not hero_h1:
            clarity_rating = "moderate"
            findings.append(
                ContentFinding(
                    finding_id="CF-VP02",
                    title="غياب عنوان رئيسي بارز (Missing H1 Headline)",
                    category="value_proposition",
                    description="لم يتم رصد وسم H1 رئيسي في الصفحة للتعريف بالقيمة المقترحة للموقع.",
                    page_url=home_page.page_url,
                    evidence_ids=evidence_ids[:2],
                    observation_type="derived",
                    severity="medium",
                    confidence_category="observed",
                )
            )

        # Flag unsubstantiated differentiator claims
        for idx, diff in enumerate(differentiators[:2], 1):
            findings.append(
                ContentFinding(
                    finding_id=f"CF-VP-DIFF{idx}",
                    title="ادعاء تفوق مطلق بحاجة إلى إثبات مرجعي (Unsupported Differentiator Claim)",
                    category="trust_claims",
                    description=f"استخدام صياغات تفضيل مطلق دون إسناد بأدلة مقارنة موثقة: '{diff}'",
                    page_url=home_page.page_url,
                    source_excerpt=diff,
                    evidence_ids=evidence_ids[:2],
                    observation_type="observed",
                    severity="medium",
                    confidence_category="observed",
                    potential_communication_impact="إضعاف المصداقية لدى الزوار في حال عدم وجود مقارنات أو بيانات تثبت الادعاء.",
                )
            )

        assessment = ValuePropositionAssessment(
            offering_summary=offering_summary,
            target_audience=target_audience,
            problem_addressed=None,
            core_benefits=benefits[:5],
            claimed_differentiators=differentiators[:5],
            clarity_rating=clarity_rating,
            is_understandable_without_context=bool(offering_summary and clarity_rating != "unclear"),
            evidence_ids=evidence_ids[:10],
            findings=[f.title for f in findings],
        )

        return assessment, findings
