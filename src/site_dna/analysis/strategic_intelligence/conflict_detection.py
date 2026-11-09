"""Cross-Agent Conflict & Tradeoff Detection Engine for Site DNA Phase 11."""

from site_dna.schemas.strategic_intelligence import ConflictRecord, ConflictType, UnifiedFinding


class ConflictDetector:
    """Identifies architectural, UX, and strategic tensions between different agent recommendations."""

    def detect_conflicts(self, findings: list[UnifiedFinding]) -> list[ConflictRecord]:
        """Examine normalized findings across domains to detect conflicting guidance."""
        conflicts: list[ConflictRecord] = []

        findings_by_phase: dict[str, list[UnifiedFinding]] = {}
        for f in findings:
            findings_by_phase.setdefault(f.source_phase, []).append(f)

        # 1. Performance vs Visual Quality
        perf_findings = [
            f
            for f in findings_by_phase.get("technical_seo", [])
            if any(term in (f.title + f.description).lower() for term in ("lcp", "performance", "image", "weight"))
        ]
        visual_findings = [
            f
            for f in findings_by_phase.get("visual_identity", [])
            if any(term in (f.title + f.description).lower() for term in ("imagery", "hero", "visual", "rich"))
        ]
        if perf_findings and visual_findings:
            p_f = perf_findings[0]
            v_f = visual_findings[0]
            conflicts.append(
                ConflictRecord(
                    conflict_type="performance_vs_visual",
                    finding_ids=[p_f.unified_finding_id, v_f.unified_finding_id],
                    recommendation_ids=[],
                    description="Tension between rich, high-resolution visual storytelling and strict page weight/Core Web Vitals budgets.",
                    description_ar="تعارض بين متطلبات الهوية البصرية الجذابة عالية الدقة وميزانية سرعة تحميل الصفحة ومؤشرات Core Web Vitals.",
                    supporting_evidence_ids=list(set(p_f.evidence_ids + v_f.evidence_ids)),
                    proposed_resolution="Adopt next-gen AVIF/WebP responsive image pipelines with explicit srcset and dimensions, rather than degrading visual assets or ignoring LCP.",
                    proposed_resolution_ar="اعتماد صيغ الصور الحديثة (WebP/AVIF) والتضمين المتجاوب عبر srcset مع تحديد أبعاد العرض بدلاً من إزالة الصور أو إهمال سرعة التحميل.",
                    resolution_confidence=0.85,
                    manual_review_required=False,
                )
            )

        # 2. Conversion vs Accessibility
        cro_findings = [
            f
            for f in findings_by_phase.get("ux_ui", []) + findings_by_phase.get("content_marketing", [])
            if any(term in (f.title + f.description).lower() for term in ("form", "simplify", "shorten", "friction"))
        ]
        a11y_form_findings = [
            f
            for f in findings_by_phase.get("accessibility", [])
            if any(term in (f.title + f.description).lower() for term in ("label", "fieldset", "input", "legend"))
        ]
        if cro_findings and a11y_form_findings:
            c_f = cro_findings[0]
            a_f = a11y_form_findings[0]
            conflicts.append(
                ConflictRecord(
                    conflict_type="conversion_vs_accessibility",
                    finding_ids=[c_f.unified_finding_id, a_f.unified_finding_id],
                    recommendation_ids=[],
                    description="Conflict between minimizing visual form fields for conversion and providing mandatory accessible labels and instructions.",
                    description_ar="تعارض بين الرغبة في تبسيط مظهر النماذج لزيادة التحويل وإلزامية وجود تسميات وإرشادات وصول برمجية واضحة.",
                    proposed_resolution="Retain explicit programmatic labels via floating labels or sr-only accessible associations, ensuring zero reduction in screen-reader accessibility while preserving sleek form aesthetics.",
                    proposed_resolution_ar="الحفاظ على الارتباط البرمجي الصريح للتسميات واستخدام التسميات العائمة أو الموجهة لقارئات الشاشة (sr-only) للموازنة بين الأناقة والنفاذ.",
                    resolution_confidence=0.90,
                    manual_review_required=False,
                )
            )

        # 3. SEO vs UX (Content Density)
        seo_text_findings = [
            f
            for f in findings_by_phase.get("technical_seo", [])
            if any(term in (f.title + f.description).lower() for term in ("content", "keyword", "heading", "h1", "h2"))
        ]
        ux_density_findings = [
            f
            for f in findings_by_phase.get("ux_ui", [])
            if any(
                term in (f.title + f.description).lower() for term in ("whitespace", "clutter", "density", "scannab")
            )
        ]
        if seo_text_findings and ux_density_findings:
            s_f = seo_text_findings[0]
            u_f = ux_density_findings[0]
            conflicts.append(
                ConflictRecord(
                    conflict_type="seo_vs_ux",
                    finding_ids=[s_f.unified_finding_id, u_f.unified_finding_id],
                    recommendation_ids=[],
                    description="Tension between indexable explanatory body text for search discovery and minimalist, scannable UX layouts.",
                    description_ar="تعارض بين إضافة نصوص وصفية تفصيلية لمحركات البحث والحفاظ على بساطة وسلاسة القراءة وتجنب حشو الواجهة.",
                    proposed_resolution="Organize explanatory content using structured semantic accordions, tabbed layouts, and progressive disclosure cards.",
                    proposed_resolution_ar="هيكلة المحتوى الوصفي باستخدام حاويات الأكورديون المنظمة والتبويبات التفاعلية لتحقيق أهداف الأرشفة دون إرباك القارئ.",
                    resolution_confidence=0.80,
                    manual_review_required=False,
                )
            )

        # 4. Security vs Third-Party Marketing Functionality
        sec_csp_findings = [
            f
            for f in findings_by_phase.get("security_privacy", [])
            if any(term in (f.title + f.description).lower() for term in ("csp", "policy", "inline", "eval"))
        ]
        mktg_findings = [
            f
            for f in findings_by_phase.get("content_marketing", [])
            + findings_by_phase.get("competitor_intelligence", [])
            if any(term in (f.title + f.description).lower() for term in ("tracking", "tag", "widget", "analytics"))
        ]
        if sec_csp_findings and mktg_findings:
            sec_f = sec_csp_findings[0]
            mkt_f = mktg_findings[0]
            conflicts.append(
                ConflictRecord(
                    conflict_type="security_vs_functionality",
                    finding_ids=[sec_f.unified_finding_id, mkt_f.unified_finding_id],
                    recommendation_ids=[],
                    description="Conflict between strict Content Security Policy enforcement and third-party marketing tags or scripts.",
                    description_ar="تعارض بين تطبيق سياسة أمان محتوى صارمة (CSP) وتشغيل أدوات التحليل وسكربتات التسويق الخارجية.",
                    proposed_resolution="Deploy CSP in Content-Security-Policy-Report-Only mode first to map all required external origins and use cryptographic nonces for dynamic scripts.",
                    proposed_resolution_ar="تشغيل سياسة CSP في وضع التقرير فقط (Report-Only) لحصر النطاقات المعتمدة واستخدام Nonce مشفر للسكربتات المصرحة.",
                    resolution_confidence=0.85,
                    manual_review_required=True,
                )
            )

        return conflicts
