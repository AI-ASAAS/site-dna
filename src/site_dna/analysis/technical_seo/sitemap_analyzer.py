"""XML Sitemap structure and URL coverage analysis."""

from urllib.parse import urlparse

from site_dna.schemas.discovery import CrawlResult
from site_dna.schemas.technical_seo import (
    SitemapAssessment,
    TechnicalPageRecord,
    TechnicalSEOFinding,
)


class SitemapAnalyzer:
    """Evaluates XML sitemap presence, URL normalization, cross-origin rules, and crawl parity."""

    @staticmethod
    def analyze(
        pages: list[TechnicalPageRecord],
        crawl_result: CrawlResult,
    ) -> tuple[SitemapAssessment, list[TechnicalSEOFinding]]:
        """Audit sitemap discovery, structure, duplicate URLs, and coverage."""
        findings: list[TechnicalSEOFinding] = []
        info = crawl_result.website_info
        evidence_ids = pages[0].source_evidence_ids[:2] if pages else []

        sitemap_found = bool(info.sitemap_found)
        sitemap_urls = list(info.sitemap_urls) if info.sitemap_urls else []
        site_origin = urlparse(info.canonical_origin).netloc.lower()

        duplicate_urls_count = 0
        cross_origin_count = 0
        seen_urls = set()

        for u in sitemap_urls:
            clean_u = u.strip()
            if clean_u in seen_urls:
                duplicate_urls_count += 1
            seen_urls.add(clean_u)

            u_parsed = urlparse(clean_u)
            if u_parsed.netloc and u_parsed.netloc.lower() != site_origin:
                cross_origin_count += 1

        if duplicate_urls_count > 0:
            findings.append(
                TechnicalSEOFinding(
                    finding_id="TS-SIT-DUP",
                    title="تكرار روابط داخل خريطة الموقع XML (Duplicate URLs in Sitemap)",
                    category="sitemap",
                    description=f"تم رصد {duplicate_urls_count} رابط مكرر داخل ملف خريطة الموقع sitemap.xml.",
                    page_url=f"{info.canonical_origin}/sitemap.xml",
                    evidence_ids=evidence_ids,
                    observation_type="derived",
                    severity="low",
                    confidence_category="derived",
                    potential_technical_impact="إهدار ميزانية الزحف وتضخيم حجم ملفات الخريطة دون فائدة.",
                    recommended_action="تطبيق فلاتر استبعاد التكرار في نظام توليد الخريطة الآلي لضمان تفرد كل رابط.",
                )
            )

        if cross_origin_count > 0:
            findings.append(
                TechnicalSEOFinding(
                    finding_id="TS-SIT-CROSS",
                    title="روابط من نطاقات خارجية داخل خريطة الموقع (Cross-Origin URLs in Sitemap)",
                    category="sitemap",
                    description=f"تم رصد {cross_origin_count} رابط ينتمي إلى نطاق مختلف داخل خريطة الموقع، وهو ما يتعارض مع معايير بروتوكول sitemaps.org.",
                    page_url=f"{info.canonical_origin}/sitemap.xml",
                    evidence_ids=evidence_ids,
                    observation_type="derived",
                    severity="medium",
                    confidence_category="derived",
                    potential_technical_impact="تجاهل محركات البحث للروابط الخارجية داخل الخريطة واحتمال رفض معالجة الملف.",
                    recommended_action="قصر روابط خريطة الموقع على النطاق المصدر المعتمد ونطاقاته الفرعية المصرح بها.",
                )
            )

        # Cross-reference with crawled pages
        crawled_urls = {p.requested_url.rstrip("/") for p in pages}
        sitemap_set = {u.rstrip("/") for u in sitemap_urls}

        crawled_in_sitemap = len(crawled_urls.intersection(sitemap_set))
        uncrawled_sitemap_urls = max(0, len(sitemap_set) - crawled_in_sitemap)

        if not sitemap_found:
            findings.append(
                TechnicalSEOFinding(
                    finding_id="TS-SIT-MISSING",
                    title="غياب ملف خريطة الموقع sitemap.xml (Missing XML Sitemap)",
                    category="sitemap",
                    description="لم يتم اكتشاف أي ملف خريطة موقع sitemap.xml صالح في المسارات المعيارية أو عبر robots.txt.",
                    page_url=f"{info.canonical_origin}/sitemap.xml",
                    evidence_ids=evidence_ids,
                    observation_type="observed",
                    severity="medium",
                    confidence_category="measured",
                    potential_technical_impact="بطء اكتشاف محركات البحث للصفحات العميقة أو المحتوى المضاف حديثاً.",
                    recommended_action="توليد خريطة موقع sitemap.xml ديناميكية وتضمين رابطها في robots.txt وGoogle Search Console.",
                )
            )

        assessment = SitemapAssessment(
            sitemap_found=sitemap_found,
            sitemap_urls=sitemap_urls,
            total_entries_count=len(sitemap_urls),
            duplicate_urls_count=duplicate_urls_count,
            cross_origin_entries_count=cross_origin_count,
            crawled_urls_in_sitemap=crawled_in_sitemap,
            uncrawled_sitemap_urls=uncrawled_sitemap_urls,
            evidence_ids=evidence_ids,
            findings=[f.title for f in findings],
        )

        return assessment, findings
