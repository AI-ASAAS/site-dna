"""Unit tests for Phase 12 Playwright PDF rendering and 20-point PDF quality verification."""


import pytest

from site_dna.reporting.brand_assets import get_thmanyah_font_css
from site_dna.reporting.pdf_quality import PdfQualityInspector
from site_dna.reporting.pdf_renderer import PlaywrightPdfRenderer


@pytest.mark.asyncio
async def test_pdf_rendering_and_quality_inspection():
    """Verify PDF rendering generates valid A4 document with searchable Arabic text."""
    sample_html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<style>
{get_thmanyah_font_css()}
@page {{ size: A4 portrait; margin: 15mm; }}
body {{ font-family: 'Thmanyah Sans', sans-serif; direction: rtl; }}
h1 {{ color: #221f1f; }}
p {{ color: #555555; }}
</style>
</head>
<body>
<h1>أساس للذكاء الاصطناعي — تقرير بصمة الموقع التنفيذي الموحد لعام 2026</h1>
<p>هذا النص تجريبي كامل وموسع للتحقق من جودة إخراج وثائق PDF وتوافق خطوط ثمانية الرسمية والاتجاه الكامل من اليمين إلى اليسار والتأكد من قابلية البحث عن النصوص العربية داخل الملف المولد بصورة دقيقة ومطابقة للمواصفات المؤسسية.</p>
</body>
</html>"""

    renderer = PlaywrightPdfRenderer()
    pdf_bytes = await renderer.render_pdf(sample_html, paper_size="A4")

    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")

    # Inspect 20-point quality check
    inspector = PdfQualityInspector(pdf_bytes)
    report = inspector.inspect()

    assert report["passed"] is True
    assert report["page_count"] >= 1
    assert report["checks_passed"] > 0
    assert len(report["violations"]) == 0
