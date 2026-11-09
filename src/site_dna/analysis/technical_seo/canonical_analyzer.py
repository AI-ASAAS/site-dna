"""Canonical URL consistency and conflict analysis engine."""

from urllib.parse import urlparse

from site_dna.schemas.technical_seo import (
    CanonicalAssessment,
    TechnicalPageRecord,
    TechnicalSEOFinding,
)


class CanonicalAnalyzer:
    """Evaluates rel='canonical' declarations, cross-page targets, and self-referencing integrity."""

    @staticmethod
    def analyze(
        pages: list[TechnicalPageRecord],
    ) -> tuple[CanonicalAssessment, list[TechnicalSEOFinding]]:
        """Audit canonical tags, cross-domain references, and target validity."""
        if not pages:
            return CanonicalAssessment(), []

        findings: list[TechnicalSEOFinding] = []
        missing_canonical_count = 0
        self_referencing_count = 0
        cross_page_count = 0
        cross_domain_count = 0
        conflicting_count = 0
        evidence_ids = pages[0].source_evidence_ids[:3]

        # Map pages by URL to check if canonical target points to a 4xx/5xx or redirect
        pages_by_url = {p.requested_url.rstrip("/"): p for p in pages}

        for p in pages:
            canonical = (p.canonical_url or "").strip()
            page_clean = p.requested_url.rstrip("/")

            if not canonical:
                missing_canonical_count += 1
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-CAN-MISSING",
                        title="غياب رابط Canonical المعياري (Missing Canonical Declaration)",
                        category="canonical",
                        description=f"الصفحة تفتقر إلى وسم <link rel='canonical'> لتحديد النسخة المعيارية الرسمية: '{p.requested_url}'",
                        page_url=p.requested_url,
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="observed",
                        severity="low",
                        confidence_category="observed",
                        potential_technical_impact="احتمال تشتت تقييم الصفحة بين المتغيرات مع أو بدون معلمات التتبع ومسارات السلاش.",
                        recommended_action="إضافة وسم <link rel='canonical' href='...'> يشير إلى العنوان المعتمد للصفحة.",
                    )
                )
                continue

            canonical_clean = canonical.rstrip("/")

            # Check self-referencing
            if canonical_clean == page_clean:
                self_referencing_count += 1
            else:
                cross_page_count += 1

                # Check cross-domain
                p_host = urlparse(p.requested_url).netloc.lower()
                c_host = urlparse(canonical).netloc.lower()
                if c_host and c_host != p_host:
                    cross_domain_count += 1
                    findings.append(
                        TechnicalSEOFinding(
                            finding_id="TS-CAN-CROSSDOMAIN",
                            title="رابط Canonical يشير إلى نطاق خارجي مختلف (Cross-Domain Canonical)",
                            category="canonical",
                            description=f"الصفحة تشير إلى نطاق خارجي كنسخة معيارية بديلة: '{canonical}' (من '{p.requested_url}')",
                            page_url=p.requested_url,
                            source_excerpt=canonical,
                            evidence_ids=p.source_evidence_ids[:2],
                            observation_type="observed",
                            severity="medium",
                            confidence_category="observed",
                            potential_technical_impact="إسناد كامل قيمة المحتوى وحقوقه إلى النطاق الخارجي وعدم فهرسة الصفحة محلياً.",
                            recommended_action="التأكد من أن الإشارة للنطاق الخارجي متعمدة (مثل التدوين المشترك أو نقل المحتوى المرخص).",
                        )
                    )

                # Check if target is known to be broken (4xx or 5xx) in collected sample
                target_page = pages_by_url.get(canonical_clean)
                if target_page and target_page.http_status >= 400:
                    conflicting_count += 1
                    findings.append(
                        TechnicalSEOFinding(
                            finding_id="TS-CAN-BROKEN-TARGET",
                            title="رابط Canonical يشير إلى صفحة تُرجع خطأ (Canonical to Error URL)",
                            category="canonical",
                            description=f"رابط Canonical يشير إلى هدف يُرجع رمز فشل {target_page.http_status}: '{canonical}'",
                            page_url=p.requested_url,
                            source_excerpt=canonical,
                            evidence_ids=p.source_evidence_ids[:2],
                            observation_type="derived",
                            severity="high",
                            confidence_category="measured",
                            potential_technical_impact="تجاهل محركات البحث للإشارة المعيارية تماماً بسبب تعذر الوصول للهدف.",
                            recommended_action="تعديل رابط Canonical ليشير إلى صفحة صالحة وحية تُرجع رمز 200 OK.",
                        )
                    )

                if target_page and any("noindex" in rd.lower() for rd in target_page.robots_directives):
                    conflicting_count += 1
                    findings.append(
                        TechnicalSEOFinding(
                            finding_id="TS-CAN-NOINDEX-TARGET",
                            title="رابط Canonical يشير إلى صفحة تحمل noindex (Canonical Target has Noindex)",
                            category="canonical",
                            description=f"رابط Canonical يشير إلى صفحة محظورة من الفهرسة (noindex): '{canonical}'",
                            page_url=p.requested_url,
                            source_excerpt=canonical,
                            evidence_ids=p.source_evidence_ids[:2],
                            observation_type="derived",
                            severity="high",
                            confidence_category="measured",
                            potential_technical_impact="إرسال إشارات متناقضة لمحركات البحث حيث تشير النسخة المعيارية لصفحة ممنوعة من الفهرسة.",
                            recommended_action="إما إزالة noindex من الصفحة الهدف أو توجيه Canonical إلى صفحة قابلة للفهرسة.",
                        )
                    )

        assessment = CanonicalAssessment(
            missing_canonical_count=missing_canonical_count,
            self_referencing_count=self_referencing_count,
            cross_page_canonical_count=cross_page_count,
            cross_domain_canonical_count=cross_domain_count,
            conflicting_canonicals_count=conflicting_count,
            evidence_ids=evidence_ids,
            findings=[f.title for f in findings],
        )

        return assessment, findings
