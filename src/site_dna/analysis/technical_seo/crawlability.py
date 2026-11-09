"""Crawlability and internal discovery analysis engine."""

from site_dna.schemas.discovery import CrawlResult
from site_dna.schemas.technical_seo import (
    CrawlabilityAssessment,
    TechnicalPageRecord,
    TechnicalSEOFinding,
)


class CrawlabilityAnalyzer:
    """Evaluates crawler accessibility, internal discovery paths, and link connectivity."""

    @staticmethod
    def analyze(
        pages: list[TechnicalPageRecord],
        crawl_result: CrawlResult,
    ) -> tuple[CrawlabilityAssessment, list[TechnicalSEOFinding]]:
        """Perform deterministic crawlability and link connectivity analysis."""
        if not pages:
            return CrawlabilityAssessment(status="unknown"), []

        findings: list[TechnicalSEOFinding] = []
        evidence_ids = pages[0].source_evidence_ids[:3]

        # 1. Crawler permissions
        robots_allowed = crawl_result.website_info.robots_txt_allowed
        status = "permitted" if robots_allowed else "restricted"

        if not robots_allowed:
            findings.append(
                TechnicalSEOFinding(
                    finding_id="TS-CRW-01",
                    title="حظر زحف محركات البحث عبر ملف robots.txt (Crawler Disallowed)",
                    category="crawlability",
                    description="قواعد ملف robots.txt تحظر زحف محركات البحث أو البوتات المحددة إلى الموقع.",
                    page_url=crawl_result.website_info.initial_url,
                    evidence_ids=evidence_ids,
                    observation_type="observed",
                    severity="high",
                    confidence_category="measured",
                    potential_technical_impact="منع محركات البحث من الوصول للمحتوى وفهرسته.",
                    recommended_action="مراجعة قواعد Disallow في robots.txt والتأكد من فتح المسارات المخصصة للنشر العام.",
                )
            )

        # 2. HTTP accessibility
        broken_links_count = 0
        crawl_depth_max = max((p.depth for p in crawl_result.pages if hasattr(p, "depth")), default=0)

        if crawl_depth_max > 4:
            findings.append(
                TechnicalSEOFinding(
                    finding_id="TS-CRW-DEEP",
                    title="عمق زحف مفرط للصفحات (Excessive Crawl Depth)",
                    category="crawlability",
                    description=f"وصل عمق الزحف لبعض الصفحات إلى {crawl_depth_max} مستويات، وهو ما يتجاوز الحد الموصى به (أقل من 4 مستويات).",
                    page_url=crawl_result.website_info.initial_url,
                    evidence_ids=evidence_ids,
                    observation_type="observed",
                    severity="medium",
                    confidence_category="measured",
                    potential_technical_impact="صعوبة وصول محركات البحث للصفحات العميقة وتقليل وتيرة إعادة زحفها.",
                    recommended_action="تبسيط الهيكلية الهرمية للموقع وضمان عدم ابتعاد أي صفحة هامة بأكثر من 3 نقرات عن الرئيسية.",
                )
            )

        # Build in-memory link map
        incoming_links: dict[str, int] = {p.requested_url.rstrip("/"): 0 for p in pages}
        unique_destinations = set()

        for p in pages:
            # Check for non-200 status
            if p.http_status >= 400:
                broken_links_count += 1
                findings.append(
                    TechnicalSEOFinding(
                        finding_id=f"TS-CRW-ERR-{p.http_status}",
                        title=f"استجابة غير ناجحة لرمز الحالة HTTP {p.http_status} (HTTP Error Status)",
                        category="crawlability",
                        description=f"الصفحة تُرجع رمز حالة فشل {p.http_status} بدلاً من 200 OK: '{p.requested_url}'",
                        page_url=p.requested_url,
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="observed",
                        severity="high" if p.http_status >= 500 else "medium",
                        confidence_category="measured",
                        potential_technical_impact="إهدار ميزانية الزحف وتعذر وصول الزوار ومحركات البحث للصفحة.",
                        recommended_action="إصلاح الخلل في الخادم أو تصحيح مسار الرابط أو إعادة التوجيه 301 إلى البديل المناسب.",
                    )
                )

            # Internal links audit
            for lnk in p.internal_links:
                clean_dest = lnk.rstrip("/")
                unique_destinations.add(clean_dest)
                if clean_dest in incoming_links and clean_dest != p.requested_url.rstrip("/"):
                    incoming_links[clean_dest] += 1

        # 3. Orphaned pages detection (in-sample)
        orphaned_pages_detected = 0
        if len(pages) > 1:
            home_url = pages[0].requested_url.rstrip("/")
            for p_url, count in incoming_links.items():
                if p_url != home_url and count == 0:
                    orphaned_pages_detected += 1
                    findings.append(
                        TechnicalSEOFinding(
                            finding_id="TS-CRW-ORPHAN",
                            title="صفحة يتيمة بدون روابط داخلية واردة (Orphaned Page)",
                            category="crawlability",
                            description=f"الصفحة لا تحتوي على أي روابط داخلية تشير إليها ضمن عينة الزحف المستكشفة: '{p_url}'",
                            page_url=p_url,
                            evidence_ids=evidence_ids,
                            observation_type="derived",
                            severity="medium",
                            confidence_category="derived",
                            potential_technical_impact="صعوبة اكتشاف الصفحة من قبل محركات البحث وتراجع قيمتها في الترتيب الهرمي.",
                            recommended_action="إضافة روابط سياقية تشير إلى الصفحة من الصفحات الرئيسية أو التصنيفات ذات الصلة.",
                        )
                    )

        assessment = CrawlabilityAssessment(
            status=status,
            total_internal_links=sum(len(p.internal_links) for p in pages),
            unique_destinations=len(unique_destinations),
            broken_links_count=broken_links_count,
            crawl_depth_max=crawl_depth_max,
            orphaned_pages_detected=orphaned_pages_detected,
            evidence_ids=evidence_ids,
            findings=[f.title for f in findings],
        )

        return assessment, findings
