"""Strategic Opportunity Synthesis Engine for Site DNA Phase 11."""

from site_dna.schemas.strategic_intelligence import StrategicOpportunity, UnifiedFinding


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
            opportunities.append(
                StrategicOpportunity(
                    title="Comprehensive Web Infrastructure Hardening & Defensive Trust Signals",
                    title_ar="تحصين البنية التحتية لشبكة الويب وترسيخ مؤشرات الثقة الرقمية",
                    category="security_privacy",
                    related_finding_ids=[f.unified_finding_id for f in sec_findings],
                    affected_pages=pages,
                    observed_problem="Gaps in transport security, missing defense-in-depth HTTP headers, and cookie configurations.",
                    strategic_interpretation="Hardening server edge headers and cookie flags eliminates low-hanging compliance vulnerabilities and boosts enterprise customer confidence.",
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
            opportunities.append(
                StrategicOpportunity(
                    title="Universal Accessibility & Inclusive Experience Uplift (WCAG 2.2 Level AA)",
                    title_ar="الارتقاء بمعايير النفاذ الرقمي الشامل وتوافق إرشادات WCAG 2.2 AA",
                    category="accessibility",
                    related_finding_ids=[f.unified_finding_id for f in a11y_findings],
                    affected_pages=pages,
                    observed_problem="Barriers in keyboard navigation, form labeling, or visual contrast identified across key user flows.",
                    strategic_interpretation="Remediating accessibility barriers unlocks access for assistive technology users, prevents legal liability, and improves overall usability for all audiences.",
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
            opportunities.append(
                StrategicOpportunity(
                    title="Search Engine Indexability & Discoverability Optimization",
                    title_ar="تعزيز قابلية الفهرسة والظهور في محركات البحث",
                    category="seo_discoverability",
                    related_finding_ids=[f.unified_finding_id for f in seo_findings],
                    affected_pages=pages,
                    observed_problem="Signals such as canonical tagging, structured data, or crawl budget efficiency need alignment.",
                    strategic_interpretation="Eliminating technical crawl impediments ensures search engine spiders correctly parse and index core product and landing pages.",
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
            opportunities.append(
                StrategicOpportunity(
                    title="Frictionless User Journey & Form Interaction Streamlining",
                    title_ar="تبسيط رحلة المستخدم وتقليل الاحتكاك في نماذج التفاعل",
                    category="ux_friction_reduction",
                    related_finding_ids=[f.unified_finding_id for f in ux_findings],
                    affected_pages=pages,
                    observed_problem="Navigation obstacles, unclear interactive affordances, or multi-step form cognitive friction.",
                    strategic_interpretation="Smoothing interactive touchpoints and providing explicit feedback lowers drop-off rates during critical conversion steps.",
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
            opportunities.append(
                StrategicOpportunity(
                    title="Value Proposition Sharpening & Coherent Marketing Messaging",
                    title_ar="صقل القيمة المقترحة وتوحيد الرسائل التسويقية الإقناعية",
                    category="content_clarity",
                    related_finding_ids=[f.unified_finding_id for f in content_findings],
                    affected_pages=pages,
                    observed_problem="Generic headlines, ambiguous product differentiation, or weak calls-to-action.",
                    strategic_interpretation="Refining header copy and clarifying business value propositions immediately communicates relevance to incoming visitors.",
                    evidence_ids=ev_ids,
                    expected_type_of_benefit="Clearer communication of product strengths, reduced cognitive load, and more decisive visitor engagement.",
                    estimated_effort="small",
                    impact_confidence=0.80,
                    limitations="Copy changes should be tested against customer personas to ensure tone alignment.",
                )
            )

        return opportunities
