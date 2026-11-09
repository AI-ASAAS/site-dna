"""Robots policy and robots.txt analysis engine."""

from site_dna.schemas.discovery import CrawlResult
from site_dna.schemas.technical_seo import (
    RobotsAssessment,
    TechnicalPageRecord,
    TechnicalSEOFinding,
)


class RobotsAnalyzer:
    """Evaluates robots.txt availability, crawler rules, and sitemap references."""

    @staticmethod
    def analyze(
        pages: list[TechnicalPageRecord],
        crawl_result: CrawlResult,
    ) -> tuple[RobotsAssessment, list[TechnicalSEOFinding]]:
        """Audit robots.txt existence, compliance, and directives."""
        findings: list[TechnicalSEOFinding] = []
        info = crawl_result.website_info

        # Extract robots evidence if available
        robots_ev = next(
            (ev for ev in crawl_result.evidence if ev.field_reference == "site.robots_txt"),
            None,
        )
        evidence_ids = [robots_ev.id] if robots_ev else (pages[0].source_evidence_ids[:2] if pages else [])

        is_present = bool(info.robots_txt_found)
        crawler_allowed = bool(info.robots_txt_allowed)
        disallowed_paths: list[str] = []
        sitemap_refs = list(info.sitemap_urls) if info.sitemap_urls else []
        http_status = None

        if robots_ev and isinstance(robots_ev.exact_value, dict):
            http_status = robots_ev.exact_value.get("status_code")
            sitemap_refs = robots_ev.exact_value.get("sitemaps", sitemap_refs)

        if not is_present:
            findings.append(
                TechnicalSEOFinding(
                    finding_id="TS-ROB-MISSING",
                    title="غياب ملف robots.txt (Robots.txt Missing)",
                    category="crawlability",
                    description="لم يتم العثور على ملف robots.txt في الجذر التوجيهي للموقع (استجابة 404 أو تعذر التحميل).",
                    page_url=f"{info.canonical_origin}/robots.txt",
                    evidence_ids=evidence_ids,
                    observation_type="observed",
                    severity="low",
                    confidence_category="measured",
                    potential_technical_impact="يسمح لجميع البوتات بالزحف دون توجيه مسبق لملفات الخريطة أو حماية المسارات الإدارية الخاصة.",
                    recommended_action="إنشاء ملف robots.txt معياري في جذر الموقع يحدد مسار sitemap.xml ويقيد زحف المسارات غير العامة.",
                )
            )

        if is_present and not sitemap_refs:
            findings.append(
                TechnicalSEOFinding(
                    finding_id="TS-ROB-NOSITEMAP",
                    title="غياب توجيه Sitemap داخل ملف robots.txt (Missing Sitemap Directive in Robots.txt)",
                    category="crawlability",
                    description="ملف robots.txt متوفر ولكنه لا يحتوي على سطر Sitemap: التوجيهي لتعريف محركات البحث بمكان خريطة الموقع.",
                    page_url=f"{info.canonical_origin}/robots.txt",
                    evidence_ids=evidence_ids,
                    observation_type="observed",
                    severity="low",
                    confidence_category="observed",
                    potential_technical_impact="تأخر اكتشاف الصفحات الجديدة وخريطة الموقع عبر بروتوكولات الزحف القياسية.",
                    recommended_action="إضافة سطر 'Sitemap: https://yourdomain.com/sitemap.xml' في نهاية ملف robots.txt.",
                )
            )

        assessment = RobotsAssessment(
            is_present=is_present,
            http_status=http_status,
            crawler_allowed=crawler_allowed,
            disallowed_paths=disallowed_paths,
            sitemap_references=sitemap_refs,
            evidence_ids=evidence_ids,
            findings=[f.title for f in findings],
        )

        return assessment, findings
