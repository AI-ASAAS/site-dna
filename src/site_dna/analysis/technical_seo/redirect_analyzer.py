"""HTTP redirects and status codes evaluation engine."""

from site_dna.schemas.technical_seo import (
    RedirectAssessment,
    TechnicalPageRecord,
    TechnicalSEOFinding,
)


class RedirectAnalyzer:
    """Evaluates HTTP status codes, permanent vs temporary redirects, and protocol transitions."""

    @staticmethod
    def analyze(
        pages: list[TechnicalPageRecord],
    ) -> tuple[RedirectAssessment, list[TechnicalSEOFinding]]:
        """Audit redirects, HTTP-to-HTTPS transitions, and status codes."""
        if not pages:
            return RedirectAssessment(), []

        findings: list[TechnicalSEOFinding] = []
        redirect_count = 0
        permanent_301 = 0
        temporary_302 = 0
        redirect_chains = 0
        redirect_loops = 0
        http_to_https = True
        evidence_ids = pages[0].source_evidence_ids[:3]

        for p in pages:
            # Check protocol
            if p.requested_url.startswith("http://"):
                if p.final_url.startswith("https://"):
                    http_to_https = True
                else:
                    http_to_https = False
                    findings.append(
                        TechnicalSEOFinding(
                            finding_id="TS-RED-INSECURE-HTTP",
                            title="عدم التحويل الإلزامي إلى بروتوكول HTTPS المشفر (Insecure HTTP Protocol)",
                            category="redirects",
                            description=f"الصفحة تُخدم عبر بروتوكول HTTP غير المشفر دون تحويل آلي إلى HTTPS: '{p.requested_url}'",
                            page_url=p.requested_url,
                            evidence_ids=p.source_evidence_ids[:2],
                            observation_type="observed",
                            severity="high",
                            confidence_category="measured",
                            potential_technical_impact="تحذيرات أمنية للزوار في المتصفحات وتأثير سلبي على ثقة المستخدم وإشارات الترتيب.",
                            recommended_action="تفعيل إعادة التوجيه الإلزامي الدائم 301 من HTTP إلى HTTPS على مستوى خادم الويب أو شبكة الـ CDN.",
                        )
                    )

            # Check status code redirects
            if 300 <= p.http_status < 400:
                redirect_count += 1
                if p.http_status == 301:
                    permanent_301 += 1
                elif p.http_status in (302, 307):
                    temporary_302 += 1
                    findings.append(
                        TechnicalSEOFinding(
                            finding_id="TS-RED-TEMP-302",
                            title=f"استخدام إعادة توجيه مؤقتة HTTP {p.http_status} (Temporary Redirect Observed)",
                            category="redirects",
                            description=f"الصفحة تُرجع إعادة توجيه مؤقتة {p.http_status} بدلاً من 301 الدائمة: '{p.requested_url}' -> '{p.final_url}'",
                            page_url=p.requested_url,
                            source_excerpt=f"{p.http_status} -> {p.final_url}",
                            evidence_ids=p.source_evidence_ids[:2],
                            observation_type="observed",
                            severity="low",
                            confidence_category="measured",
                            potential_technical_impact="عدم تمرير قيمة الصفحة وسلطة الرابط (Link Equity) بشكل كامل وسريع.",
                            recommended_action="تغيير رمز الحالة إلى 301 Permanent Redirect إذا كان نقل الصفحة أو المحتوى دائماً.",
                        )
                    )

            # Detect redirect loop indication (url == final_url but status is 3xx)
            if 300 <= p.http_status < 400 and p.requested_url.rstrip("/") == p.final_url.rstrip("/"):
                redirect_loops += 1
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-RED-LOOP",
                        title="رصد حلقة إعادة توجيه دائرية (Redirect Loop Detected)",
                        category="redirects",
                        description=f"إعادة التوجيه تشير لنفس عنوان الصفحة الأصلي مما قد يسبب حلقة دائرية مفرغة: '{p.requested_url}'",
                        page_url=p.requested_url,
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="derived",
                        severity="critical",
                        confidence_category="measured",
                        potential_technical_impact="تعذر وصول المستخدمين ومحركات البحث وانهيار الصفحة برسالة ERR_TOO_MANY_REDIRECTS.",
                        recommended_action="مراجعة قواعد إعادة التوجيه وتصحيح العنوان النهائي لتفادي الإشارة للعنوان ذاته.",
                    )
                )

        assessment = RedirectAssessment(
            redirect_count=redirect_count,
            permanent_redirects_301=permanent_301,
            temporary_redirects_302=temporary_302,
            redirect_chains_count=redirect_chains,
            redirect_loops_count=redirect_loops,
            http_to_https_transition=http_to_https,
            evidence_ids=evidence_ids,
            findings=[f.title for f in findings],
        )

        return assessment, findings
