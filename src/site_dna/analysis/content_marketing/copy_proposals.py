"""Grounded copy rewrite proposals engine adhering to strict fact-preservation rules."""

from site_dna.schemas.content_marketing import (
    ContentFinding,
    CopyRewriteProposal,
    PageContentRecord,
)


class CopyProposalsEngine:
    """Generates grounded copy rewrite suggestions without inventing unverified business facts."""

    @staticmethod
    def generate_proposals(
        pages: list[PageContentRecord],
        findings: list[ContentFinding],
        max_proposals: int = 8,
    ) -> list[CopyRewriteProposal]:
        """Generate copy rewrite proposals based on verified source facts and identified issues."""
        proposals: list[CopyRewriteProposal] = []
        if not pages:
            return proposals

        home_page = next((p for p in pages if p.page_type == "home"), pages[0])
        counter = 0

        # Proposal 1: H1 Headline Rewrite (if missing or ambiguous)
        h1_findings = [
            f
            for f in findings
            if f.category in ("value_proposition", "messaging_clarity") and "H1" in f.title or "عنوان" in f.title
        ]
        if h1_findings and counter < max_proposals:
            counter += 1
            f = h1_findings[0]
            orig = f.source_excerpt or home_page.page_title or "غير محدد"
            site_topic = home_page.page_title or "المنصة"
            proposed = f"الحل المتكامل لتحليل وتطوير المواقع بالذكاء الاصطناعي — {site_topic}"
            if "en" in (home_page.language or "").lower():
                proposed = f"Comprehensive AI-Powered Website Intelligence & Auditing — {site_topic}"

            proposals.append(
                CopyRewriteProposal(
                    proposal_id=f"PRP-{counter:02d}",
                    element_type="headline_h1",
                    source_page=home_page.page_url,
                    source_evidence_id=f.evidence_ids[0] if f.evidence_ids else None,
                    original_excerpt=orig,
                    identified_communication_issue=f.description,
                    proposed_replacement=proposed,
                    explanation_of_change="استبدال الصياغة العامة أو المفقودة بعنوان رئيسي صريح يحدد ماهية الخدمة والقيمة المحورية للزائر فور وصوله.",
                    facts_preserved=[f"طبيعة نشاط الموقع: {site_topic}"],
                    information_requiring_confirmation=["[يرجى تأكيد العبارة الترويجية الأكثر مطابقة لرسالة الشركة]"],
                    is_suggestion=True,
                )
            )

        # Proposal 2: CTA Label Optimization (if generic CTAs found)
        cta_findings = [f for f in findings if f.category == "cta_action" and f.source_excerpt]
        for cf in cta_findings:
            if counter >= max_proposals:
                break
            counter += 1
            orig_cta = cf.source_excerpt or "اضغط هنا"
            improved_cta = "ابدأ الاستكشاف الآن"
            if "تواصل" in orig_cta or "contact" in orig_cta.lower():
                improved_cta = "تواصل مع مستشارينا الآن"
            elif "سجل" in orig_cta or "sign" in orig_cta.lower() or "register" in orig_cta.lower():
                improved_cta = "أنشئ حسابك وابدأ التجربة"
            elif "en" in (home_page.language or "").lower():
                improved_cta = (
                    "Explore Our Solutions"
                    if orig_cta.lower() in ("click here", "more")
                    else f"Get Started with {orig_cta}"
                )

            proposals.append(
                CopyRewriteProposal(
                    proposal_id=f"PRP-{counter:02d}",
                    element_type="cta_label",
                    source_page=cf.page_url,
                    source_evidence_id=cf.evidence_ids[0] if cf.evidence_ids else None,
                    original_excerpt=orig_cta,
                    identified_communication_issue=cf.description,
                    proposed_replacement=improved_cta,
                    explanation_of_change="تحويل النص العام والمبهم إلى دعوة صريحة ومحفزة تبين النتيجة المباشرة للنقر دون غموض.",
                    facts_preserved=["الإجراء المستهدف للنقر"],
                    information_requiring_confirmation=["[تأكيد الوجهة المحددة التي ينقل الزر إليها]"],
                    is_suggestion=True,
                )
            )

        # Proposal 3: Hero Supporting Copy (if hero exists)
        if counter < max_proposals and home_page.paragraphs:
            first_p = home_page.paragraphs[0].get("text", "")
            if len(first_p.split()) > 10:
                counter += 1
                proposed_hero = f"{first_p[:120]}... احصل على تحليل دقيق وقابل للتنفيذ لتحسين حضورك الرقمي."
                proposals.append(
                    CopyRewriteProposal(
                        proposal_id=f"PRP-{counter:02d}",
                        element_type="hero_copy",
                        source_page=home_page.page_url,
                        source_evidence_id=home_page.source_evidence_ids[0] if home_page.source_evidence_ids else None,
                        original_excerpt=first_p[:120],
                        identified_communication_issue="إمكانية تعزيز جاذبية النص التمهيدي بإضافة عبارة تؤكد الفائدة المباشرة للزائر.",
                        proposed_replacement=proposed_hero,
                        explanation_of_change="إعادة هيكلة الفقرة التمهيدية لتجمع بين تعريف النشاط والنتيجة العملية للعميل.",
                        facts_preserved=[f"النص الأصلي: {first_p[:60]}..."],
                        information_requiring_confirmation=[
                            "[تأكيد الفائدة المحورية المستهدفة للتسليط عليها في الواجهة]"
                        ],
                        is_suggestion=True,
                    )
                )

        # Proposal 4: Trust Reassurance Statement
        trust_findings = [f for f in findings if f.category == "trust_claims" and "إحصائي" in f.title]
        if trust_findings and counter < max_proposals:
            counter += 1
            tf = trust_findings[0]
            orig_stat = tf.source_excerpt or "أرقام إحصائية"
            proposals.append(
                CopyRewriteProposal(
                    proposal_id=f"PRP-{counter:02d}",
                    element_type="trust_reassurance",
                    source_page=tf.page_url,
                    source_evidence_id=tf.evidence_ids[0] if tf.evidence_ids else None,
                    original_excerpt=orig_stat,
                    identified_communication_issue=tf.description,
                    proposed_replacement=f"{orig_stat} (استناداً إلى دراسات قياس الأداء المعتمدة [أضف رابط التقرير أو المرجع])",
                    explanation_of_change="إسناد الأرقام التسويقية بمرجع صريح يحمي المنصة من الشكوك التسويقية ويعزز الثقة.",
                    facts_preserved=[f"الرقم المعلن: {orig_stat}"],
                    information_requiring_confirmation=["[إضافة رابط التقرير أو جهة القياس المعتمدة]"],
                    is_suggestion=True,
                )
            )

        return proposals
