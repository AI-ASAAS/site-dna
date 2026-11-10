"""Strategic Opportunity Synthesis Engine for Site DNA Phase 11.

Synthesizes cross-agent strategic opportunities dynamically from actual observable
defects, specific evidence findings, and real technical observations, avoiding
generic static boilerplate across analyzed sites.
"""

from site_dna.schemas.strategic_intelligence import OpportunityCategory, StrategicOpportunity, UnifiedFinding


def _extract_specific_topics(findings: list[UnifiedFinding], max_items: int = 3) -> tuple[str, str]:
    """Extract succinct English and Arabic topic summaries from actual specific findings."""
    titles_ar = []
    titles_en = []
    for f in findings:
        t_ar = f.title_ar or f.title
        t_en = f.title
        # Clean common prefixes
        clean_ar = t_ar.replace("معالجة:", "").replace("خلل:", "").strip()
        clean_en = t_en.replace("Resolve:", "").replace("Fix:", "").strip()
        if clean_ar and clean_ar not in titles_ar:
            titles_ar.append(clean_ar)
        if clean_en and clean_en not in titles_en:
            titles_en.append(clean_en)

    ar_summary = "، ".join(titles_ar[:max_items]) if titles_ar else "ملاحظات تقنية مرصودة"
    en_summary = ", ".join(titles_en[:max_items]) if titles_en else "observed technical issues"
    return ar_summary, en_summary


class OpportunitySynthesizer:
    """Synthesizes cross-agent strategic opportunities without fabricating financial ROI or ungrounded uplift percentages."""

    def synthesize_opportunities(self, findings: list[UnifiedFinding]) -> list[StrategicOpportunity]:
        """Group domain findings into comprehensive strategic improvement opportunities."""
        opportunities: list[StrategicOpportunity] = []

        by_cat: dict[str, list[UnifiedFinding]] = {}
        for f in findings:
            by_cat.setdefault(f.source_phase, []).append(f)

        # 1. Security & Digital Trust
        sec_findings = by_cat.get("security_privacy", [])
        if sec_findings:
            pages = sorted(list({f.page_url for f in sec_findings if f.page_url}))
            ev_ids = sorted(list({ev for f in sec_findings for ev in f.evidence_ids}))
            ar_topics, en_topics = _extract_specific_topics(sec_findings, max_items=2)
            opportunities.append(
                StrategicOpportunity(
                    title=f"Infrastructure Hardening & Defensive Trust Signals ({en_topics})",
                    title_ar=f"تحصين أمان الخادم وترسيخ الثقة الرقمية ({ar_topics})",
                    category="security_privacy",
                    related_finding_ids=[f.unified_finding_id for f in sec_findings],
                    affected_pages=pages,
                    observed_problem=f"Gaps identified in server edge headers and defensive security: {en_topics}.",
                    strategic_interpretation=f"معالجة ثغرات وترويسات الأمان المرصودة ({ar_topics}) تغلق منافذ الامتثال المفتوحة وتعزز ثقة العملاء والجهات الرقابية في المنصة.",
                    evidence_ids=ev_ids,
                    expected_type_of_benefit="Enhanced regulatory compliance, mitigation of clickjacking/MIME-sniffing, and higher enterprise trustworthiness.",
                    estimated_effort="small",
                    impact_confidence=0.90,
                    limitations="Evaluates external observable responses only; internal backend security remains uninspected.",
                )
            )

        # 2. Inclusive Accessibility & WCAG Conformance
        a11y_findings = by_cat.get("accessibility", [])
        if a11y_findings:
            pages = sorted(list({f.page_url for f in a11y_findings if f.page_url}))
            ev_ids = sorted(list({ev for f in a11y_findings for ev in f.evidence_ids}))
            ar_topics, en_topics = _extract_specific_topics(a11y_findings, max_items=2)
            opportunities.append(
                StrategicOpportunity(
                    title=f"Universal Accessibility Uplift ({en_topics})",
                    title_ar=f"الارتقاء بالنفاذ الرقمي ومعايير WCAG 2.2 ({ar_topics})",
                    category="accessibility",
                    related_finding_ids=[f.unified_finding_id for f in a11y_findings],
                    affected_pages=pages,
                    observed_problem=f"Accessibility barriers identified across evaluated components: {en_topics}.",
                    strategic_interpretation=f"إصلاح عوائق النفاذ المكتشفة ({ar_topics}) يتيح استخدام الموقع للأشخاص ذوي الإعاقة ومستخدمي قارئات الشاشة ويمنع المخاطر القانونية.",
                    evidence_ids=ev_ids,
                    expected_type_of_benefit="Expanded reachable audience, legal risk reduction, improved usability across devices and assistive tools.",
                    estimated_effort="medium",
                    impact_confidence=0.92,
                    limitations="Automated heuristics must be supplemented with manual screen-reader and keyboard testing.",
                )
            )

        # 3. Technical Discoverability & Search Architecture
        seo_findings = by_cat.get("technical_seo", [])
        if seo_findings:
            pages = sorted(list({f.page_url for f in seo_findings if f.page_url}))
            ev_ids = sorted(list({ev for f in seo_findings for ev in f.evidence_ids}))
            ar_topics, en_topics = _extract_specific_topics(seo_findings, max_items=2)
            opportunities.append(
                StrategicOpportunity(
                    title=f"Search Engine Indexability & Crawl Optimization ({en_topics})",
                    title_ar=f"تعزيز قابلية الفهرسة والظهور في محركات البحث ({ar_topics})",
                    category="seo_discoverability",
                    related_finding_ids=[f.unified_finding_id for f in seo_findings],
                    affected_pages=pages,
                    observed_problem=f"Technical search indexing impediments observed: {en_topics}.",
                    strategic_interpretation=f"معالجة مشكلات الأرشفة المرصودة ({ar_topics}) تضمن لعناكب البحث فهرسة صفحات الخدمات والمنتجات الرئيسية بأعلى كفاءة وبدون إهدار ميزانية الزحف.",
                    evidence_ids=ev_ids,
                    expected_type_of_benefit="Improved organic visibility, correct rich snippet display, and efficient search crawler indexation.",
                    estimated_effort="medium",
                    impact_confidence=0.88,
                    limitations="Search ranking algorithms involve external off-page signals beyond technical on-page health.",
                )
            )

        # 4. Conversion Experience & Form Friction Reduction
        ux_findings = by_cat.get("ux_ui", [])
        if ux_findings:
            pages = sorted(list({f.page_url for f in ux_findings if f.page_url}))
            ev_ids = sorted(list({ev for f in ux_findings for ev in f.evidence_ids}))
            ar_topics, en_topics = _extract_specific_topics(ux_findings, max_items=2)
            opportunities.append(
                StrategicOpportunity(
                    title=f"User Journey & Touchpoint Optimization ({en_topics})",
                    title_ar=f"تبسيط تجربة التصفح وتجاوب الواجهة ({ar_topics})",
                    category="ux_friction_reduction",
                    related_finding_ids=[f.unified_finding_id for f in ux_findings],
                    affected_pages=pages,
                    observed_problem=f"User interaction and layout friction observed: {en_topics}.",
                    strategic_interpretation=f"إصلاح عيوب التجاوب والتفاعل المكتشفة ({ar_topics}) يمنع تسرب الزوار ويضمن تجربة مريحة وسريعة عبر كافة الشاشات.",
                    evidence_ids=ev_ids,
                    expected_type_of_benefit="Reduced visitor abandonment, smoother task completion, and improved satisfaction.",
                    estimated_effort="medium",
                    impact_confidence=0.85,
                    limitations="Qualitative heuristic observations require post-launch A/B analytics validation to confirm exact uplift.",
                )
            )

        # 5. Content Clarity & Value Proposition
        content_findings = by_cat.get("content_marketing", [])
        if content_findings:
            pages = sorted(list({f.page_url for f in content_findings if f.page_url}))
            ev_ids = sorted(list({ev for f in content_findings for ev in f.evidence_ids}))
            ar_topics, en_topics = _extract_specific_topics(content_findings, max_items=2)
            opportunities.append(
                StrategicOpportunity(
                    title=f"Value Proposition & Messaging Sharpening ({en_topics})",
                    title_ar=f"صقل الرسائل التسويقية والدعوة للإجراء ({ar_topics})",
                    category="content_clarity",
                    related_finding_ids=[f.unified_finding_id for f in content_findings],
                    affected_pages=pages,
                    observed_problem=f"Content communication gaps identified: {en_topics}.",
                    strategic_interpretation=f"تطوير صياغات المحتوى والدعوات للإجراء ({ar_topics}) يرفع جاذبية العرض ويوضح القيمة الفعلية للعميل في الثواني الأولى للزيارة.",
                    evidence_ids=ev_ids,
                    expected_type_of_benefit="Clearer communication of product strengths, reduced cognitive load, and more decisive visitor engagement.",
                    estimated_effort="small",
                    impact_confidence=0.80,
                    limitations="Copy changes should be tested against customer personas to ensure tone alignment.",
                )
            )

        return opportunities
