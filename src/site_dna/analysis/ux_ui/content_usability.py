"""Deterministic content usability, scanability, and Arabic RTL structure analyzer."""

from site_dna.analysis.ux_ui.context_builder import UXPageContext
from site_dna.schemas.ux_ui import UXContentAssessment, UXFinding
from site_dna.schemas.visual import VisualEvidenceRecord


class ContentUsabilityAnalyzer:
    """Evaluates content structure, heading scanability, information density, and Arabic RTL alignment."""

    @staticmethod
    def analyze_content(
        pages: list[UXPageContext],
        evidence_index: dict[str, VisualEvidenceRecord],
    ) -> UXContentAssessment:
        """Analyze text scanability, heading counts, and RTL language properties."""
        findings: list[UXFinding] = []
        heading_count = 0
        rtl_supported = True
        repeated_labels: list[str] = []
        total_p_words = 0
        p_count = 0

        for page in pages:
            heading_count += len(page.headings)

            # Check RTL declared attribute or computed direction
            meta = page.page_metadata or {}
            lang = (meta.get("language") or "").lower()
            dir_attr = (meta.get("dir") or "").lower()

            # Check if Arabic is used in title or headings or paragraphs
            has_arabic_text = (
                "ar" in lang
                or any("\u0600" <= ch <= "\u06ff" for h in page.headings for ch in h.get("text", ""))
                or any("\u0600" <= ch <= "\u06ff" for p_item in page.paragraphs for ch in p_item.get("text", ""))
            )

            if has_arabic_text and dir_attr != "rtl":
                rtl_supported = False

            # Check paragraphs in page.paragraphs
            for p_item in page.paragraphs:
                p_text = p_item.get("text", "")
                if p_text:
                    p_count += 1
                    total_p_words += len(p_text.split())

            # Check paragraphs in DOM
            for el in page.dom_elements:
                tag = el.get("tag_name", "").lower()
                text = (el.get("text_excerpt") or el.get("text_content") or "").strip()

                if tag == "p" and text:
                    p_count += 1
                    total_p_words += len(text.split())

        avg_p_length = (total_p_words / p_count) if p_count > 0 else 0.0

        # Scanability score: penalized if dense walls of text without headings
        scanability = 100.0
        if avg_p_length > 80:  # Excessively dense paragraphs
            scanability -= 25.0
        if heading_count == 0 and len(pages) > 0:
            scanability -= 30.0

        # Generate Findings
        if not rtl_supported and len(pages) > 0:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-CNT-01",
                    title="غياب سمة الاتجاه dir='rtl' في موقع يعتمد اللغة العربية",
                    category="content_usability",
                    description="الموقع مصرح عنه أو يحتوي محتوى عربياً لكن وسم `<html>` أو المحتوى يفتقر للسمة `dir='rtl'`، مما يؤدي لمحاذاة خاطئة للنصوص وعلامات الترقيم.",
                    source_page=pages[0].page_url,
                    viewport="desktop",
                    element_reference="html",
                    evidence_ids=[],
                    observation_type="observed",
                    severity="high",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="انعكاس ترتيب علامات الترقيم والأقواس وصعوبة قراءة المحتوى باللغة العربية.",
                    recommended_action="إضافة السمة `dir='rtl'` و `lang='ar'` إلى وسم `<html>` وضبط المحاذاة الافتراضية إلى اليمين.",
                )
            )

        if avg_p_length > 80:
            findings.append(
                UXFinding(
                    finding_id="UX-FIND-CNT-02",
                    title="كثافة نصية عالية وضعف قابلية المسح البصري السريع (Low Scanability)",
                    category="content_usability",
                    description=(
                        f"متوسط طول الفقرات النصية مرتفع ({avg_p_length:.0f} كلمة/فقرة)، "
                        "مما يقلل من قابلية القراءة السريعة ويخلق كتل نصية صماء (Walls of Text)."
                    ),
                    source_page=pages[0].page_url if pages else "",
                    viewport="desktop",
                    element_reference="p",
                    evidence_ids=[],
                    observation_type="derived",
                    severity="medium",
                    confidence_category="confirmed_by_measurement",
                    potential_user_impact="إجهاد القارئ وصعوبة استخلاص المعلومات الأساسية في أول 5 ثوانٍ من الزيارة.",
                    recommended_action="تفكيك الفقرات الطويلة إلى نقاط موجزة واستخدام عناوين فرعية H2/H3 لتقسيم الأفكار.",
                )
            )

        return UXContentAssessment(
            heading_count=heading_count,
            average_paragraph_length=round(avg_p_length, 1),
            rtl_supported=rtl_supported,
            scanability_score=round(max(0.0, scanability), 1),
            repeated_labels=repeated_labels,
            findings=findings,
        )
