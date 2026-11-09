"""Product and service content completeness analyzer."""

from site_dna.schemas.content_marketing import (
    ContentFinding,
    PageContentRecord,
    ServiceContentAssessment,
)


class ServiceContentAnalyzer:
    """Analyzes the depth, clarity, and actionability of service and product descriptions."""

    @staticmethod
    def analyze(
        pages: list[PageContentRecord],
    ) -> tuple[ServiceContentAssessment, list[ContentFinding]]:
        """Audit product and service content across pages."""
        findings: list[ContentFinding] = []
        services_pages = [p for p in pages if p.page_type in ("services", "products")]

        total_services = 0
        total_products = 0
        unexplained: list[str] = []
        completeness = "adequate"
        evidence_ids: list[str] = []

        if not services_pages:
            # Check if homepage contains service sections
            home_page = next((p for p in pages if p.page_type == "home"), pages[0] if pages else None)
            if home_page and home_page.service_descriptions:
                total_services = len(home_page.service_descriptions)
                evidence_ids.extend(home_page.source_evidence_ids[:3])
            else:
                return ServiceContentAssessment(descriptions_completeness="missing"), []
        else:
            for sp in services_pages:
                evidence_ids.extend(sp.source_evidence_ids[:3])
                # Check headings for service items
                service_headings = [h.get("text", "").strip() for h in sp.headings if h.get("level") in (2, 3)]
                if sp.page_type == "products":
                    total_products += len(service_headings) or 1
                else:
                    total_services += len(service_headings) or 1

                # Check if descriptions are too sparse (< 50 words on a dedicated service page)
                if sp.word_count < 40 and not sp.paragraphs:
                    completeness = "sparse"
                    findings.append(
                        ContentFinding(
                            finding_id="CF-SRV01",
                            title=f"محتوى صفحة الخدمات مقتضب جداً (Sparse Service Content on {sp.page_url})",
                            category="service_content",
                            description=f"الصفحة المخصصة للخدمات '{sp.page_url}' تحتوي على عدد كلمات قليل جداً ({sp.word_count} كلمة) دون تفاصيل توضيحية لما تشمله الخدمة.",
                            page_url=sp.page_url,
                            evidence_ids=sp.source_evidence_ids[:2],
                            observation_type="derived",
                            severity="high",
                            confidence_category="measured",
                        )
                    )

                # Check for unexplained headings (heading followed by no paragraph)
                for sh in service_headings:
                    if not any(sh.lower() in p.get("text", "").lower() for p in sp.paragraphs):
                        unexplained.append(sh)

        if unexplained:
            findings.append(
                ContentFinding(
                    finding_id="CF-SRV02",
                    title="عناوين خدمات أو منتجات تفتقر للشرح التوضيحي (Unexplained Service Headings)",
                    category="service_content",
                    description=f"رصد عناوين خدمات مذكورة دون فقرات تفصيلية تشرح طبيعتها: {', '.join(unexplained[:3])}",
                    page_url=services_pages[0].page_url if services_pages else pages[0].page_url,
                    evidence_ids=evidence_ids[:2],
                    observation_type="derived",
                    severity="medium",
                    confidence_category="measured",
                )
            )

        assessment = ServiceContentAssessment(
            total_services_identified=total_services,
            total_products_identified=total_products,
            descriptions_completeness=completeness,
            unexplained_offerings=unexplained[:5],
            next_step_clarity=bool(total_services > 0 and completeness != "sparse"),
            evidence_ids=evidence_ids[:10],
        )

        return assessment, findings
