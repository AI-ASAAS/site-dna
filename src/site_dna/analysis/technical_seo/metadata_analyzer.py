"""Technical HTML metadata analysis engine."""

from site_dna.schemas.technical_seo import (
    MetadataAssessment,
    TechnicalPageRecord,
    TechnicalSEOFinding,
)


class MetadataAnalyzer:
    """Evaluates structural validity, presence, duplication, and conflicts in HTML head tags."""

    @staticmethod
    def analyze(
        pages: list[TechnicalPageRecord],
    ) -> tuple[MetadataAssessment, list[TechnicalSEOFinding]]:
        """Audit title, meta description, viewport, and language tags."""
        if not pages:
            return MetadataAssessment(), []

        findings: list[TechnicalSEOFinding] = []
        missing_title_count = 0
        missing_desc_count = 0
        missing_viewport_count = 0
        missing_lang_count = 0
        conflicting_count = 0
        evidence_ids = pages[0].source_evidence_ids[:3]

        titles_seen: dict[str, list[str]] = {}

        for p in pages:
            # 1. HTML Title
            title = (p.title or "").strip()
            if not title:
                missing_title_count += 1
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-MET-NOTITLE",
                        title="غياب وسم العنوان الرئيسي <title> (Missing HTML Title)",
                        category="metadata",
                        description=f"الصفحة تفتقر تماماً إلى وسم <title> في رأس المستند HTML: '{p.requested_url}'",
                        page_url=p.requested_url,
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="observed",
                        severity="high",
                        confidence_category="observed",
                        potential_technical_impact="ظهور نتائج البحث بدون عنوان محدد واعتماد عناوين عشوائية مولدة تلقائياً من محركات البحث.",
                        recommended_action="إضافة وسم <title> موجز ومميز يعبر عن موضوع الصفحة بدقة.",
                    )
                )
            else:
                titles_seen.setdefault(title, []).append(p.requested_url)
                if len(title) > 70:
                    findings.append(
                        TechnicalSEOFinding(
                            finding_id="TS-MET-TITLE-LONG",
                            title="عنوان الصفحة يتجاوز الطول الموصى به للعرض (Excessive Title Length)",
                            category="metadata",
                            description=f"طول عنوان الصفحة ({len(title)} حرفاً) يتجاوز الحد الموصى به (60-70 حرفاً): '{title[:50]}...'",
                            page_url=p.requested_url,
                            source_excerpt=title,
                            evidence_ids=p.source_evidence_ids[:2],
                            observation_type="observed",
                            severity="low",
                            confidence_category="measured",
                            potential_technical_impact="اقتطاع العنوان في نتائج البحث ووضع علامات الحذف (...).",
                            recommended_action="تقليص صياغة العنوان ليبقى في حدود 50 إلى 65 حرفاً لضمان ظهوره كاملاً على مختلف الشاشات.",
                        )
                    )

            # 2. Meta Description
            desc = (p.meta_description or "").strip()
            if not desc:
                missing_desc_count += 1
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-MET-NODESC",
                        title="غياب الوصف التعريفي meta description (Missing Meta Description)",
                        category="metadata",
                        description=f"الصفحة لا تحتوي على وسم <meta name='description'>: '{p.requested_url}'",
                        page_url=p.requested_url,
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="observed",
                        severity="low",
                        confidence_category="observed",
                        potential_technical_impact="قيام محركات البحث باقتطاع نصوص عشوائية من الصفحة لعرضها في المقتطف التوضيحي (Snippet).",
                        recommended_action="كتابة وصف تعريفي فريد وجذاب بطول 120 إلى 155 حرفاً يلخص فائدة الصفحة للباحث.",
                    )
                )

            # 3. Viewport Meta
            viewport = (p.viewport_meta or "").strip()
            if not viewport:
                missing_viewport_count += 1
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-MET-NOVIEWPORT",
                        title="غياب وسم تهيئة العرض للأجهزة الذكية (Missing Viewport Meta Tag)",
                        category="metadata",
                        description=f"الصفحة تفتقر إلى وسم <meta name='viewport'>: '{p.requested_url}'",
                        page_url=p.requested_url,
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="observed",
                        severity="high",
                        confidence_category="observed",
                        potential_technical_impact="ظهور الصفحة بأبعاد سطح المكتب على شاشات الهواتف ورسوب اختبارات التوافق مع الأجهزة المحمولة.",
                        recommended_action="إضافة <meta name='viewport' content='width=device-width, initial-scale=1.0'>.",
                    )
                )

            # 4. HTML Language
            lang = (p.html_lang or "").strip()
            if not lang:
                missing_lang_count += 1
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-MET-NOLANG",
                        title="غياب سمة اللغة في وسم HTML (Missing html lang Attribute)",
                        category="metadata",
                        description=f"وسم <html> لا يحتوي على سمة lang المحددة للغة المحتوى: '{p.requested_url}'",
                        page_url=p.requested_url,
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="observed",
                        severity="low",
                        confidence_category="observed",
                        potential_technical_impact="صعوبة التعرف الآلي السريع على لغة المستند من برامج قارئات الشاشة ومحركات البحث.",
                        recommended_action="تضمين سمة اللغة المناسبة، مثل: <html lang='ar' dir='rtl'> أو <html lang='en'>.",
                    )
                )

        # Duplicate Titles Check
        duplicate_titles_count = 0
        for title_str, urls in titles_seen.items():
            if len(urls) > 1:
                duplicate_titles_count += len(urls)
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-MET-DUPTITLE",
                        title="تكرار عنوان الصفحة عبر صفحات متعددة (Duplicate Page Titles)",
                        category="metadata",
                        description=f"العنوان '{title_str[:40]}' مكرر عبر {len(urls)} صفحات مختلفة في الموقع.",
                        page_url=urls[0],
                        source_excerpt=title_str,
                        evidence_ids=evidence_ids,
                        observation_type="derived",
                        severity="medium",
                        confidence_category="derived",
                        potential_technical_impact="تنافس صفحات الموقع ذاتياً في نتائج البحث (Keyword Cannibalization) وتشويش نية الباحث.",
                        recommended_action="صياغة عنوان فريد لكل صفحة يعكس محتواها وغايتها الخاصة دون تكرار عام.",
                    )
                )

        assessment = MetadataAssessment(
            missing_title_count=missing_title_count,
            missing_description_count=missing_desc_count,
            duplicate_titles_count=duplicate_titles_count,
            missing_viewport_count=missing_viewport_count,
            missing_lang_count=missing_lang_count,
            conflicting_metadata_count=conflicting_count,
            evidence_ids=evidence_ids,
            findings=[f.title for f in findings],
        )

        return assessment, findings
