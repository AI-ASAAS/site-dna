"""JavaScript SEO and server-rendered HTML vs rendered DOM comparison engine."""

from typing import Optional

from site_dna.schemas.technical_seo import (
    JavaScriptSEOAssessment,
    TechnicalPageRecord,
    TechnicalSEOFinding,
)
from site_dna.schemas.visual import VisualCaptureResult


class JavaScriptSEOAnalyzer:
    """Evaluates parity and discrepancies between raw server HTML and rendered DOM."""

    @staticmethod
    def analyze(
        pages: list[TechnicalPageRecord],
        visual_result: Optional[VisualCaptureResult],
    ) -> tuple[JavaScriptSEOAssessment, list[TechnicalSEOFinding]]:
        """Compare server-rendered metadata against browser DOM rendered metadata."""
        if not pages or not visual_result:
            return JavaScriptSEOAssessment(status="not_comparable"), []

        findings: list[TechnicalSEOFinding] = []
        evidence_ids = pages[0].source_evidence_ids[:3]
        visual_pages = {vp.page_url.rstrip("/"): vp for vp in visual_result.pages}

        title_differs = False
        canonical_differs = False
        robots_differs = False
        headings_differ = False
        content_rendered_only = False

        for p in pages:
            vp = visual_pages.get(p.requested_url.rstrip("/"))
            if not vp:
                continue

            # Compare DOM element counts vs headings
            rendered_elements_count = len(vp.dom_elements)

            # Check if main content was absent in server HTML but present in DOM
            if not p.title and rendered_elements_count > 0:
                title_differs = True
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-JS-TITLE-RENDERED",
                        title="توليد عنوان الصفحة ديناميكياً عبر جافاسكربت (Client-Rendered Title)",
                        category="javascript_seo",
                        description=f"عنوان الصفحة يغيب في HTML المصدري الأولي ويُحقن فقط بعد تنفيذ جافاسكربت في المتصفح: '{p.requested_url}'",
                        page_url=p.requested_url,
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="derived",
                        severity="medium",
                        confidence_category="measured",
                        potential_technical_impact="تأخر فهرسة العنوان الصحيح في محركات البحث لحين إتمام جولة تصيير جافاسكربت الثانوية.",
                        recommended_action="تضمين وسم <title> في الـ HTML المصدري المُرسل من الخادم (SSR / Static Pre-rendering).",
                    )
                )

            # Check for substantial rendered-only content or headings rendered only in DOM
            dom_has_headings = any(el.tag_name.lower() in ("h1", "h2", "h3") for el in vp.dom_elements)
            if not p.headings and (dom_has_headings or rendered_elements_count > 5):
                headings_differ = True
                content_rendered_only = True
                findings.append(
                    TechnicalSEOFinding(
                        finding_id="TS-JS-CONTENT-RENDERED",
                        title="اعتماد هيكلية المحتوى على التصيير من جانب العميل CSR (Client-Side Rendered Content)",
                        category="javascript_seo",
                        description=f"العناوين والمحتوى الهيكلي غائبة في كود الخادم ويتم بناؤها كلياً عبر حزم جافاسكربت: '{p.requested_url}'",
                        page_url=p.requested_url,
                        evidence_ids=p.source_evidence_ids[:2],
                        observation_type="derived",
                        severity="medium",
                        confidence_category="measured",
                        potential_technical_impact="استهلاك مضاعف لميزانية الزحف وتأخير أرشفة المحتوى المتغير.",
                        recommended_action="تطبيق التصيير من جانب الخادم (Server-Side Rendering) أو التوليد المسبق (SSG) للصفحات المستهدفة للأرشفة.",
                    )
                )

        status = (
            "rendered_only"
            if content_rendered_only
            else ("conflicting" if (title_differs or canonical_differs or robots_differs) else "consistent")
        )

        assessment = JavaScriptSEOAssessment(
            status=status,
            title_differs=title_differs,
            canonical_differs=canonical_differs,
            robots_differs=robots_differs,
            headings_differ=headings_differ,
            content_rendered_only=content_rendered_only,
            evidence_ids=evidence_ids,
            findings=[f.title for f in findings],
        )

        return assessment, findings
