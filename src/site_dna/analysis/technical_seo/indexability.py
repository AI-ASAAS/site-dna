"""Indexability directives and search engine indexing signals analysis."""

from site_dna.schemas.technical_seo import (
    IndexabilityAssessment,
    TechnicalPageRecord,
    TechnicalSEOFinding,
)


class IndexabilityAnalyzer:
    """Evaluates search engine indexing signals without speculating on actual Google index state."""

    @staticmethod
    def analyze(
        pages: list[TechnicalPageRecord],
    ) -> tuple[IndexabilityAssessment, list[TechnicalSEOFinding]]:
        """Evaluate robots directives, X-Robots-Tag, and conflicting indexing signals."""
        if not pages:
            return IndexabilityAssessment(status="unknown"), []

        findings: list[TechnicalSEOFinding] = []
        noindex_count = 0
        x_robots_tag_count = 0
        conflicting_count = 0
        pages_with_directives: list[str] = []
        evidence_ids = pages[0].source_evidence_ids[:3]

        for p in pages:
            directives_lower = [d.lower() for d in p.robots_directives]
            has_noindex = any("noindex" in d for d in directives_lower)

            if p.robots_directives:
                pages_with_directives.append(p.requested_url)

            # Check for noindex
            if has_noindex:
                noindex_count += 1
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-IDX-NOINDEX",
                        title="رصد توجيه حظر الفهرسة noindex (Noindex Directive Observed)",
                        category="indexability",
                        description=f"الصفحة تحتوي على توجيه noindex في وسم robots meta، مما يمنع محركات البحث من فهرستها: '{p.requested_url}'",
                        page_url=p.requested_url,
                        source_excerpt=", ".join(p.robots_directives),
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="observed",
                        severity="medium",
                        confidence_category="measured",
                        potential_technical_impact="استبعاد الصفحة من نتائج البحث (ملاحظة: هذا ليس دليلاً على وجود عقوبة أو استبعاد فعلي من Google).",
                        recommended_action="إذا كانت الصفحة مخصصة للنشر العام، يجب إزالة توجيه noindex فوراً؛ وإذا كان الاستبعاد مقصوداً، يُرجى التأكد من عدم إدراجها في ملف sitemap.",
                    )
                )

            # Check for conflicting signals: noindex + sitemap membership
            if has_noindex and p.sitemap_membership:
                conflicting_count += 1
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-IDX-CONFLICT-SITEMAP",
                        title="تعارض بين توجيه noindex وتضمين الصفحة في خريطة الموقع (Noindex in Sitemap Conflict)",
                        category="indexability",
                        description=f"الصفحة تحمل توجيه noindex لمنع فهرستها ومع ذلك فهي مدرجة ضمن خريطة الموقع XML: '{p.requested_url}'",
                        page_url=p.requested_url,
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="derived",
                        severity="high",
                        confidence_category="derived",
                        potential_technical_impact="إرسال إشارات متناقضة لمحركات البحث مما يهدر ميزانية الزحف ويؤخر تحديث الفهرس.",
                        recommended_action="إزالة الصفحة من خريطة الموقع sitemap.xml إذا كان حظر الفهرسة مقصوداً، أو حذف توجيه noindex إذا كانت الصفحة مستهدفة للفهرسة.",
                    )
                )

            # Check for conflicting signals: noindex on self-declared canonical
            if has_noindex and p.canonical_url and p.canonical_url.rstrip("/") == p.requested_url.rstrip("/"):
                conflicting_count += 1
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-IDX-CONFLICT-CANONICAL",
                        title="تعارض بين توجيه noindex ورابط Canonical الذاتي (Noindex with Self Canonical)",
                        category="indexability",
                        description=f"الصفحة تشير إلى نفسها كرابط Canonical أساسي وفي الوقت ذاته تعلن توجيه noindex: '{p.requested_url}'",
                        page_url=p.requested_url,
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="derived",
                        severity="high",
                        confidence_category="derived",
                        potential_technical_impact="ارتباك خوارزميات الفهرسة واختيار النسخة المعيارية.",
                        recommended_action="إما إزالة noindex لاعتماد الصفحة كنسخة رئيسية مفهرسة، أو توجيه Canonical لصفحة مفهرسة بديلة.",
                    )
                )

        # Overall indexability classification
        if conflicting_count > 0:
            status = "conflicting_signals"
        elif noindex_count == len(pages):
            status = "noindex_observed"
        elif any(p.http_status >= 400 for p in pages):
            status = "potentially_indexable"
        else:
            status = "potentially_indexable"

        assessment = IndexabilityAssessment(
            status=status,
            noindex_count=noindex_count,
            x_robots_tag_count=x_robots_tag_count,
            conflicting_directives_count=conflicting_count,
            pages_with_directives=pages_with_directives,
            evidence_ids=evidence_ids,
            findings=[f.title for f in findings],
        )

        return assessment, findings
