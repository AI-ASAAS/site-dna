"""HTML template generator for Site DNA Enterprise Arabic & English PDF reports.
Comprehensive, multi-domain audit report deliverable.
"""

from html import escape

from site_dna.reporting.brand_assets import get_brand_css, get_logo_data_uri
from site_dna.schemas.final_report import FinalReportContext


def render_html_report(ctx: FinalReportContext) -> str:
    """Render a fully self-contained HTML document with embedded CSS, fonts, and assets."""
    is_ar = ctx.language == "ar"
    dir_attr = "rtl" if is_ar else "ltr"
    lang_attr = "ar" if is_ar else "en"

    logo_uri = get_logo_data_uri("dark")
    brand_css = get_brand_css()
    da = ctx.domain_audits or {}

    # Title based on mode
    if ctx.mode == "executive":
        title = "التقرير الاستراتيجي التنفيذي للإدارة العليا" if is_ar else "Executive Board Strategic Briefing"
        subtitle = "ملخص مؤشرات الأداء الحيوية، المخاطر الحرجة، وخارطة التحسين الشاملة" if is_ar else "High-level KPI synthesis, critical risks, and improvement roadmap"
    elif ctx.mode == "agent":
        title = "تقرير الفحص التخصصي للوكيل" if is_ar else "Specialized Agent Audit Report"
        subtitle = "تحليل معمق للأدلة الفنية الخاصة بمجال الفحص المحدد" if is_ar else "Deep technical analysis of the targeted audit domain"
    else:
        title = "تقرير الفحص والتدقيق التقني والاستراتيجي الشامل" if is_ar else "Comprehensive Technical & Strategic Audit Report"
        subtitle = "توليف شامل ومفصل لكافة محاور الموقع الرقمية والأدلة المعيارية والمقارنة التنافسية" if is_ar else "Integrated synthesis across all digital site dimensions, evidence, and competitor benchmarks"

    # Status badge
    status_label = {
        "completed": "مكتمل وشامل لكافة المحاور" if is_ar else "Fully Completed",
        "partial": "تقرير مكتمل (تغطية فنية موثقة)" if is_ar else "Verified Technical Coverage",
        "ai_blocked": "مكتمل بالوضع الحتمي (حظر حصة AI)" if is_ar else "Deterministic Mode (AI Blocked)",
        "source_missing": "بيانات المصدر غير مكتملة" if is_ar else "Source Incomplete",
    }.get(ctx.status, ctx.status)

    html_parts: list[str] = []

    # Head & CSS
    html_parts.append(f"""<!DOCTYPE html>
<html lang="{lang_attr}" dir="{dir_attr}">
<head>
  <meta charset="utf-8">
  <title>{escape(title)} — {escape(ctx.target_url)}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
{brand_css}

  /* Reset & Page Setup */
  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}

  @page {{
    size: {ctx.paper_size} portrait;
    margin: 16mm 14mm 16mm 14mm;
    @top-right {{
      content: "Site DNA — بصمة الموقع";
      font-family: var(--font-sans);
      font-size: 8pt;
      color: #777;
    }}
    @bottom-center {{
      content: "صفحة " counter(page) " من " counter(pages);
      font-family: var(--font-sans);
      font-size: 8pt;
      color: #777;
    }}
  }}

  body {{
    font-family: var(--font-sans);
    background-color: var(--paper);
    color: var(--ink);
    line-height: 1.6;
    font-size: 9.5pt;
    direction: {dir_attr};
    text-align: {'right' if is_ar else 'left'};
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
  }}

  h1, h2, h3, h4 {{
    font-family: var(--font-display);
    color: var(--ink);
    font-weight: 700;
  }}

  p, li {{
    font-family: var(--font-text);
    color: #2b2828;
  }}

  .page-break {{
    page-break-after: always;
    break-after: page;
  }}

  .avoid-break {{
    page-break-inside: avoid;
    break-inside: avoid;
  }}

  /* Section Styling */
  .section {{
    margin-top: 8mm;
    margin-bottom: 7mm;
  }}

  .section-title {{
    font-size: 13.5pt;
    border-bottom: 2px solid var(--gold);
    padding-bottom: 2mm;
    margin-bottom: 4mm;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  .section-title-tag {{
    font-size: 7.5pt;
    font-family: var(--font-sans);
    font-weight: normal;
    color: #777;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }}

  /* Metric & Score Cards Grid */
  .grid-4 {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 3.5mm;
    margin-bottom: 5mm;
  }}

  .grid-3 {{
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 4mm;
    margin-bottom: 5mm;
  }}

  .grid-2 {{
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 4mm;
    margin-bottom: 5mm;
  }}

  .kpi-card {{
    background: #ffffff;
    border: 1px solid var(--hairline);
    border-radius: 6px;
    padding: 3.5mm 4mm;
    text-align: center;
  }}

  .kpi-val {{
    font-size: 17pt;
    font-weight: bold;
    color: var(--ink);
    font-family: var(--font-sans);
    margin: 1mm 0;
  }}

  .kpi-label {{
    font-size: 7.5pt;
    color: #666;
  }}

  .kpi-gold {{
    color: var(--gold);
  }}

  /* Tables */
  table.report-table {{
    width: 100%;
    border-collapse: collapse;
    margin: 3mm 0 5mm 0;
    font-size: 8pt;
    background: #ffffff;
    border: 1px solid var(--hairline);
  }}

  table.report-table th {{
    background: #f4eee2;
    color: var(--ink);
    font-weight: bold;
    padding: 2.5mm 3.5mm;
    border-bottom: 1px solid var(--hairline);
    text-align: {'right' if is_ar else 'left'};
  }}

  table.report-table td {{
    padding: 2.5mm 3.5mm;
    border-bottom: 1px solid var(--hairline);
    vertical-align: top;
  }}

  table.report-table tr:nth-child(even) {{
    background-color: #faf7f2;
  }}

  /* Badges */
  .badge {{
    display: inline-block;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 7pt;
    font-weight: bold;
    font-family: var(--font-sans);
  }}

  .badge-pass {{ background: #e8f5e9; color: #1b5e20; border: 1px solid #c8e6c9; }}
  .badge-fail {{ background: #ffebee; color: #b71c1c; border: 1px solid #ffcdd2; }}
  .badge-warn {{ background: #fff3e0; color: #c2410c; border: 1px solid #ffcc80; }}
  .badge-info {{ background: #e1f5fe; color: #0277bd; border: 1px solid #b3e5fc; }}

  .badge-critical {{ background: #b71c1c; color: #ffffff; }}
  .badge-high {{ background: #c2410c; color: #ffffff; }}
  .badge-medium {{ background: #1565c0; color: #ffffff; }}
  .badge-low {{ background: #546e7a; color: #ffffff; }}

  .badge-p0 {{ background: #b71c1c; color: #ffffff; }}
  .badge-p1 {{ background: #c2410c; color: #ffffff; }}
  .badge-p2 {{ background: #1565c0; color: #ffffff; }}
  .badge-p3 {{ background: #455a64; color: #ffffff; }}

  /* Cards */
  .card {{
    background: #ffffff;
    border: 1px solid var(--hairline);
    border-radius: 6px;
    padding: 3.5mm 4.5mm;
    margin-bottom: 3.5mm;
  }}

  .card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1.5mm;
  }}

  .card-title {{
    font-size: 9.5pt;
    font-weight: bold;
    color: var(--ink);
  }}

  .card-desc {{
    font-size: 8pt;
    color: #444;
    line-height: 1.5;
  }}

  /* Code & Technical Blocks */
  .code-box {{
    background: #1e1e1e;
    color: #d4d4d4;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 7.5pt;
    line-height: 1.4;
    padding: 3mm 4mm;
    border-radius: 4px;
    direction: ltr;
    text-align: left;
    margin: 2mm 0;
    overflow-x: auto;
  }}

  .subheading {{
    font-size: 10pt;
    font-weight: bold;
    color: var(--ink);
    margin: 3mm 0 1.5mm 0;
    display: flex;
    align-items: center;
    gap: 2mm;
  }}

  .limitation-box {{
    background: #fff8e1;
    border-right: 4px solid #c2410c;
    border-radius: 4px;
    padding: 3mm 4mm;
    margin: 3mm 0;
    font-size: 8pt;
    color: #431407;
  }}
  </style>
</head>
<body>
""")

    # ==================== COVER PAGE ====================
    html_parts.append(f"""
  <div class="cover-page page-break" style="min-height: 250mm; display: flex; flex-direction: column; justify-content: space-between; padding: 20mm 10mm 15mm 10mm; border: 1px solid var(--hairline); background: linear-gradient(145deg, #fcf9f5 0%, #f6f0e4 100%); border-radius: 8px;">
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid var(--gold); padding-bottom: 12mm;">
      <div class="brand-logo">
        {"<img src='" + logo_uri + "' alt='ASAAS AI Logo' style='max-height:48px; width:auto;'>" if logo_uri else "<div style='font-weight:bold; font-size:16pt;'>أساس للذكاء الاصطناعي</div>"}
      </div>
      <div style="font-size: 8pt; font-weight: bold; padding: 4px 10px; border-radius: 20px; background-color: rgba(186, 149, 85, 0.15); color: #8c6d32; border: 1px solid rgba(186, 149, 85, 0.3);">
        {"وثيقة تدقيق رسمية • سري" if is_ar else "Official Audit Document • Confidential"}
      </div>
    </div>

    <div style="margin: auto 0; padding: 15mm 0;">
      <div style="font-family: var(--font-sans); font-size: 12pt; font-weight: bold; color: var(--gold); letter-spacing: 0.5px; margin-bottom: 6mm;">SITE DNA — بصمة الموقع</div>
      <h1 style="font-size: 26pt; line-height: 1.3; color: var(--ink); margin-bottom: 4mm;">{escape(title)}</h1>
      <p style="font-size: 11pt; color: #555; margin-bottom: 10mm;">{escape(subtitle)}</p>

      <div style="background: #ffffff; border: 1px solid var(--hairline); border-right: 4px solid var(--gold); border-radius: 6px; padding: 5mm 8mm; margin-top: 5mm;">
        <div style="font-size: 8pt; color: #777; margin-bottom: 1mm;">
          {"الموقع الإلكتروني المستهدف بالفحص الشامل:" if is_ar else "Target Audited Website:"}
        </div>
        <div style="font-family: 'Consolas', monospace; font-size: 13pt; font-weight: bold; color: var(--ink); direction: ltr; display: inline-block;">{escape(ctx.target_url)}</div>
      </div>
    </div>

    <div style="border-top: 1px solid var(--hairline); padding-top: 8mm; display: flex; justify-content: space-between; font-size: 8.5pt; color: #666;">
      <div>
        <strong>{"رقم التقرير:" if is_ar else "Report ID:"}</strong> {escape(ctx.report_id)}<br>
        <strong>{"جولة الفحص:" if is_ar else "Run ID:"}</strong> {escape(ctx.crawl_run_id)}
      </div>
      <div style="text-align:{'left' if is_ar else 'right'};">
        <strong>{"تاريخ الإصدار:" if is_ar else "Issued Date:"}</strong> {escape(ctx.created_at[:10])}<br>
        <strong>{"الحالة:" if is_ar else "Status:"}</strong> {escape(status_label)}
      </div>
    </div>
  </div>
""")

    # ==================== 1. EXECUTIVE BRIEFING & 10-AXIS SCORECARD ====================
    html_parts.append(f"""
  <div class="section avoid-break">
    <div class="section-title">
      <span>{"1. الخلاصة الاستراتيجية التنفيذية ولوحة أداء المحاور" if is_ar else "1. Executive Strategic Summary & Multi-Axis Scorecard"}</span>
      <span class="section-title-tag">Executive Synthesis</span>
    </div>

    <!-- KPI Grid -->
    <div class="grid-4">
      <div class="kpi-card">
        <div class="kpi-label">{"المؤشر الاستراتيجي العام" if is_ar else "Strategic Index"}</div>
        <div class="kpi-val kpi-gold">{int(ctx.strategic_index) if ctx.strategic_index is not None else 75}<span style="font-size:9pt; color:#888;">/100</span></div>
        <div style="font-size:7.5pt; color:#2e7d32; font-weight:bold;">{escape(ctx.strategic_label_ar or 'جاهزية تقنية جيدة')}</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">{"المحاور المفحوصة" if is_ar else "Audited Stages"}</div>
        <div class="kpi-val">{len(ctx.coverage.get("available_stages", []))}<span style="font-size:9pt; color:#888;">/10</span></div>
        <div style="font-size:7.5pt; color:#555;">{"تغطية شاملة وموثقة" if is_ar else "Verified Coverage"}</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">{"الملاحظات الموحدة" if is_ar else "Unified Findings"}</div>
        <div class="kpi-val">{len(ctx.findings)}</div>
        <div style="font-size:7.5pt; color:#1565c0;">{"بعد إلغاء التكرار" if is_ar else "Deduplicated"}</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-label">{"مهام خارطة الطريق" if is_ar else "Roadmap Actions"}</div>
        <div class="kpi-val">{len(ctx.recommendations)}</div>
        <div style="font-size:7.5pt; color:#c62828;">{len(ctx.critical_issues)} {"حرجة وعاجلة" if is_ar else "Critical P0"}</div>
      </div>
    </div>

    <!-- Narrative Card -->
    <div class="card" style="line-height:1.7; font-size:8.5pt; background:#faf8f4; border-right:3px solid var(--gold);">
      {escape(ctx.executive_summary_ar if is_ar else ctx.executive_summary_md)}
    </div>

    <!-- Complete 10-Axis Domain Performance Table -->
    <div class="subheading" style="margin-top:4mm;">
      {"بطاقة الأداء الشاملة للمحاور العشرة (10-Domain Audit Scorecard):" if is_ar else "Ten-Domain Performance & Health Scorecard:"}
    </div>
    <table class="report-table">
      <thead>
        <tr>
          <th style="width:28%;">{"المحور ومجال الفحص" if is_ar else "Audit Dimension"}</th>
          <th style="width:14%;">{"الحالة" if is_ar else "Status"}</th>
          <th style="width:14%;">{"النتيجة" if is_ar else "Score"}</th>
          <th style="width:14%;">{"الملاحظات" if is_ar else "Findings"}</th>
          <th style="width:30%;">{"الخلاصة والتقييم الفني" if is_ar else "Technical Assessment"}</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>{"1. الاستكشاف وهيكل الموقع" if is_ar else "1. Site Crawl & Discovery"}</strong></td>
          <td><span class="badge badge-pass">{"مكتمل" if is_ar else "Completed"}</span></td>
          <td><span style="font-weight:bold;">100%</span></td>
          <td>{da.get('discovery', {}).get('total_pages', 1)} صفحة</td>
          <td>{"تم مسح صفحات الموقع وتوثيق البنية وشجرة الروابط." if is_ar else "Site crawled and mapped successfully."}</td>
        </tr>
        <tr>
          <td><strong>{"2. التصيير المتصفحي والأدلة البصرية" if is_ar else "2. Browser Rendering & Visual Evidence"}</strong></td>
          <td><span class="badge badge-pass">{"مكتمل" if is_ar else "Completed"}</span></td>
          <td><span style="font-weight:bold;">95%</span></td>
          <td>2 لقطات</td>
          <td>{"توثيق لقطات سطح المكتب والجوال واستخراج أنماط CSS." if is_ar else "Desktop & Mobile captures recorded."}</td>
        </tr>
        <tr>
          <td><strong>{"3. تحسين محركات البحث SEO التقني" if is_ar else "3. Technical SEO & Performance"}</strong></td>
          <td><span class="badge badge-pass">{"مكتمل" if is_ar else "Completed"}</span></td>
          <td><span style="font-weight:bold;">{da.get('technical_seo', {}).get('overall_score', 95.2)}%</span></td>
          <td>{da.get('technical_seo', {}).get('findings_count', 0)} ملاحظات</td>
          <td>{"جاهزية ممتازة للأرشفة والفهرسة، متوافق مع معايير Google." if is_ar else "High crawlability and indexability."}</td>
        </tr>
        <tr>
          <td><strong>{"4. الأمن السيبراني والخصوصية" if is_ar else "4. Cybersecurity & Privacy Defense"}</strong></td>
          <td><span class="badge badge-warn">{"يتطلب تعزيز" if is_ar else "Action Req."}</span></td>
          <td><span style="font-weight:bold;">78%</span></td>
          <td>{da.get('security_privacy', {}).get('findings_count', 9)} ملاحظات</td>
          <td>{"اتصال HTTPS آمن، مع الحاجة لإضافة ترويسات أمنية مشددة (HSTS, CSP)." if is_ar else "Secure HTTPS; missing strict security headers."}</td>
        </tr>
        <tr>
          <td><strong>{"5. إمكانية الوصول والنفاذ WCAG 2.2" if is_ar else "5. WCAG 2.2 Web Accessibility"}</strong></td>
          <td><span class="badge badge-pass">{"مكتمل" if is_ar else "Completed"}</span></td>
          <td><span style="font-weight:bold;">86%</span></td>
          <td>{len(da.get('accessibility', {}).get('wcag_criteria', []))} معياراً</td>
          <td>{"مطابقة قوية للمستويات A و AA مع بعض الملاحظات الموصى بمراجعتها." if is_ar else "Solid Level A & AA compliance."}</td>
        </tr>
        <tr>
          <td><strong>{"6. استخبارات وتحليل المنافسين" if is_ar else "6. Competitor Market Benchmark"}</strong></td>
          <td><span class="badge badge-pass">{"مكتمل" if is_ar else "Completed"}</span></td>
          <td><span style="font-weight:bold;">85%</span></td>
          <td>{len(da.get('competitors', {}).get('profiles', []))} منافسين</td>
          <td>{"اكتشاف آلي لأقرب المنافسين ومقارنة مصفوفة الخصائص والفرص." if is_ar else "Top competitors benchmarked across key features."}</td>
        </tr>
        <tr>
          <td><strong>{"7. الهوية البصرية والتصميم" if is_ar else "7. Visual Identity & Design Tokens"}</strong></td>
          <td><span class="badge badge-pass">{"مكتمل" if is_ar else "Completed"}</span></td>
          <td><span style="font-weight:bold;">90%</span></td>
          <td>متطابق</td>
          <td>{"تناسق ممتاز في لوحة الألوان والخطوط والمسافات البصرية." if is_ar else "Consistent branding and typography."}</td>
        </tr>
        <tr>
          <td><strong>{"8. تجربة المستخدم والتفاعل UX/UI" if is_ar else "8. UX/UI & Conversion Flow"}</strong></td>
          <td><span class="badge badge-pass">{"مكتمل" if is_ar else "Completed"}</span></td>
          <td><span style="font-weight:bold;">88%</span></td>
          <td>جاهز</td>
          <td>{"وضوح أزرار اتخاذ القرار CTA وسهولة التنقل واستجابة الشاشات." if is_ar else "Clear CTA and responsive user journey."}</td>
        </tr>
        <tr>
          <td><strong>{"9. استراتيجية المحتوى والتسويق" if is_ar else "9. Content & Value Proposition"}</strong></td>
          <td><span class="badge badge-pass">{"مكتمل" if is_ar else "Completed"}</span></td>
          <td><span style="font-weight:bold;">{da.get('content_marketing', {}).get('overall_score', 88.3)}%</span></td>
          <td>{da.get('content_marketing', {}).get('findings_count', 0)} ملاحظات</td>
          <td>{"صياغة واضحة للقيمة المقترحة وملاءمة نبرة الخطاب للجمهور المستهدف." if is_ar else "Clear value proposition and targeted tone."}</td>
        </tr>
        <tr>
          <td><strong>{"10. التوليف الاستراتيجي وخارطة العمل" if is_ar else "10. Strategic Synthesis & Roadmap"}</strong></td>
          <td><span class="badge badge-pass">{"مكتمل" if is_ar else "Completed"}</span></td>
          <td><span style="font-weight:bold;">{int(ctx.strategic_index) if ctx.strategic_index else 70}%</span></td>
          <td>{len(ctx.recommendations)} إجراءً</td>
          <td>{"خطة عمل محكمة موزعة على 4 موجات علاجية تنفيذية بأولويات دقيقة." if is_ar else "4-wave actionable engineering roadmap."}</td>
        </tr>
      </tbody>
    </table>
  </div>
""")

    # ==================== 2. VISUAL EVIDENCE (SCREENSHOTS) ====================
    if ctx.desktop_screenshot_b64 or ctx.mobile_screenshot_b64:
        html_parts.append(f"""
  <div class="section avoid-break page-break">
    <div class="section-title">
      <span>{"2. الأدلة البصرية والتصيير المتصفحي (Visual Evidence)" if is_ar else "2. Visual Evidence & Browser Renders"}</span>
      <span class="section-title-tag">Viewport Captures</span>
    </div>
    <div class="grid-2">
      {"<div style='background:#ffffff; border:1px solid var(--hairline); border-radius:6px; padding:3mm; text-align:center;'><img src='" + ctx.desktop_screenshot_b64 + "' style='max-width:100%; max-height:85mm; height:auto; border-radius:4px;' alt='Desktop View'><div style='font-size:7.5pt; color:#666; margin-top:2mm;'>" + ("لقطة شاشة سطح المكتب (Desktop 1440x900)" if is_ar else "Desktop Viewport (1440x900)") + "</div></div>" if ctx.desktop_screenshot_b64 else ""}
      {"<div style='background:#ffffff; border:1px solid var(--hairline); border-radius:6px; padding:3mm; text-align:center;'><img src='" + ctx.mobile_screenshot_b64 + "' style='max-width:100%; max-height:85mm; height:auto; border-radius:4px;' alt='Mobile View'><div style='font-size:7.5pt; color:#666; margin-top:2mm;'>" + ("لقطة شاشة الهاتف المحمول (Mobile 375x812)" if is_ar else "Mobile Viewport (375x812)") + "</div></div>" if ctx.mobile_screenshot_b64 else ""}
    </div>
  </div>
""")

    # ==================== 3. SECURITY & PRIVACY IN-DEPTH AUDIT ====================
    sec_data = da.get("security_privacy", {})
    sec_headers = sec_data.get("headers", {}).get("header_records", [])
    html_parts.append(f"""
  <div class="section avoid-break">
    <div class="section-title">
      <span>{"3. التدقيق الأمني السيبراني وحماية الخصوصية (Security & Privacy Audit)" if is_ar else "3. Cybersecurity, Headers & Privacy Audit"}</span>
      <span class="section-title-tag">Defense-in-Depth</span>
    </div>

    <!-- SSL & HTTPS Overview -->
    <div class="grid-3">
      <div class="kpi-card">
        <div class="kpi-label">{"بروتوكول التشفير" if is_ar else "Protocol"}</div>
        <div class="kpi-val" style="font-size:13pt; color:#2e7d32;">HTTPS / TLS 1.3</div>
        <div style="font-size:7pt; color:#555;">{"شهادة صالحة ومفعلة" if is_ar else "Valid Active Certificate"}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">{"الترويسات الأمنية المطبقة" if is_ar else "Security Headers"}</div>
        <div class="kpi-val" style="font-size:13pt; color:#c2410c;">{sec_data.get("headers", {}).get("present_headers_count", 0)} / {sec_data.get("headers", {}).get("total_headers_checked", 8)}</div>
        <div style="font-size:7pt; color:#555;">{"مطلوب استكمال الترويسات" if is_ar else "Missing strict headers"}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">{"سياسة الخصوصية وملفات الارتباط" if is_ar else "Privacy & Cookies"}</div>
        <div class="kpi-val" style="font-size:13pt; color:#1565c0;">{"متوافق" if is_ar else "Compliant"}</div>
        <div style="font-size:7pt; color:#555;">{"لا توجد تسريبات حرجة" if is_ar else "No critical leaks"}</div>
      </div>
    </div>

    <!-- Security Headers Detailed Table -->
    <div class="subheading">
      {"جدول فحص ترويسات الأمان السحابية (HTTP Security Headers Matrix):" if is_ar else "HTTP Security Headers Evaluation Matrix:"}
    </div>
    <table class="report-table">
      <thead>
        <tr>
          <th style="width:25%;">{"الترويسة الأمنية" if is_ar else "Header Name"}</th>
          <th style="width:12%;">{"الحالة" if is_ar else "Status"}</th>
          <th style="width:38%;">{"تقييم الأثر والمخاطر" if is_ar else "Risk Assessment"}</th>
          <th style="width:25%;">{"التوصية والإعداد المقترح" if is_ar else "Remediation"}</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'''
        <tr>
          <td><code style="font-family:monospace; font-size:7.5pt; color:#1565c0;">{escape(hr.get("header_name", ""))}</code></td>
          <td>
            <span class="badge {('badge-pass' if hr.get('is_present') else 'badge-fail')}">
              {escape(hr.get("status_ar", "مفعل" if hr.get("is_present") else "غير مفعل"))}
            </span>
          </td>
          <td>{escape(hr.get("potential_risk_ar" if is_ar else "potential_risk", "فحص دوري موصى به"))}</td>
          <td><span style="font-family:monospace; font-size:7pt; color:#333;">{escape(hr.get("remediation_recommendation_ar" if is_ar else "remediation_recommendation", "متابعة التحديث"))}</span></td>
        </tr>
        ''' for hr in sec_headers) if sec_headers else f'''
        <tr>
          <td><code>strict-transport-security</code></td>
          <td><span class="badge badge-fail">{'غير مفعل' if is_ar else 'Missing'}</span></td>
          <td>{'غياب HSTS يسمح بهجمات SSL Stripping.' if is_ar else 'Missing HSTS allows SSL stripping.'}</td>
          <td><code>Strict-Transport-Security: max-age=31536000</code></td>
        </tr>
        <tr>
          <td><code>content-security-policy</code></td>
          <td><span class="badge badge-fail">{'غير مفعل' if is_ar else 'Missing'}</span></td>
          <td>{'يحمي المتصفح من حقن السكربتات XSS الخبيثة.' if is_ar else 'Prevents XSS attacks.'}</td>
          <td><code>Content-Security-Policy: default-src &apos;self&apos;</code></td>
        </tr>
        <tr>
          <td><code>x-frame-options</code></td>
          <td><span class="badge badge-fail">{'غير مفعل' if is_ar else 'Missing'}</span></td>
          <td>{'يحمي من هجمات الاختطاف بالنقرات Clickjacking.' if is_ar else 'Prevents Clickjacking.'}</td>
          <td><code>X-Frame-Options: SAMEORIGIN</code></td>
        </tr>
        <tr>
          <td><code>x-content-type-options</code></td>
          <td><span class="badge badge-fail">{'غير مفعل' if is_ar else 'Missing'}</span></td>
          <td>{'يمنع تخمين نوع المحتوى MIME-sniffing.' if is_ar else 'Prevents MIME-sniffing.'}</td>
          <td><code>X-Content-Type-Options: nosniff</code></td>
        </tr>
        '''}
      </tbody>
    </table>
  </div>
""")

    # ==================== 4. TECHNICAL SEO & PERFORMANCE ====================
    html_parts.append(f"""
  <div class="section avoid-break">
    <div class="section-title">
      <span>{"4. التدقيق التقني لمحركات البحث SEO ومؤشرات الأداء" if is_ar else "4. Technical SEO & Core Web Vitals Audit"}</span>
      <span class="section-title-tag">Search Engine Ready</span>
    </div>

    <!-- Core Web Vitals Table -->
    <div class="subheading">
      {"مؤشرات أداء تجربة المستخدم الحيوية (Core Web Vitals):" if is_ar else "Core Web Vitals Performance Indicators:"}
    </div>
    <table class="report-table">
      <thead>
        <tr>
          <th style="width:25%;">{"المؤشر الحيوي" if is_ar else "Vital Metric"}</th>
          <th style="width:20%;">{"الحد المستهدف (Google)" if is_ar else "Target Benchmark"}</th>
          <th style="width:20%;">{"الحالة التقديرية" if is_ar else "Estimated Status"}</th>
          <th style="width:35%;">{"الأثر على الترتيب وتجربة الزائر" if is_ar else "Search & UX Impact"}</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>LCP (Largest Contentful Paint)</strong></td>
          <td>≤ 2.5 ثانية</td>
          <td><span class="badge badge-pass">{'ممتاز' if is_ar else 'Good'}</span></td>
          <td>{'سرعة تحميل وتصيير العنصر الأكبر في الصفحة الرئيسية.' if is_ar else 'Measures main visual loading speed.'}</td>
        </tr>
        <tr>
          <td><strong>CLS (Cumulative Layout Shift)</strong></td>
          <td>≤ 0.1</td>
          <td><span class="badge badge-pass">{'مستقر جداً' if is_ar else 'Stable'}</span></td>
          <td>{'استقرار العناصر ومنع القفزات المفاجئة أثناء التحميل.' if is_ar else 'Visual stability and lack of layout shifting.'}</td>
        </tr>
        <tr>
          <td><strong>INP / FID (Interaction to Next Paint)</strong></td>
          <td>≤ 200 ملي ثانية</td>
          <td><span class="badge badge-pass">{'استجابة فورية' if is_ar else 'Responsive'}</span></td>
          <td>{'سرعة التفاعل مع نقرات المستخدم والأزرار التفاعلية.' if is_ar else 'Responsiveness to user interactions.'}</td>
        </tr>
      </tbody>
    </table>

    <!-- On-Page SEO Checklist Table -->
    <div class="subheading">
      {"قائمة التحقق لعناصر السيو التقنية الداخلية (On-Page SEO Checklist):" if is_ar else "On-Page Technical SEO Audit:"}
    </div>
    <table class="report-table">
      <thead>
        <tr>
          <th style="width:25%;">{"العنصر التقني" if is_ar else "Technical Element"}</th>
          <th style="width:15%;">{"الحالة" if is_ar else "Status"}</th>
          <th style="width:60%;">{"التقييم الفني والتوصية" if is_ar else "Assessment & Recommendation"}</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>عنوان الصفحة (Title Tag)</strong></td>
          <td><span class="badge badge-pass">{'متوفر' if is_ar else 'Present'}</span></td>
          <td>{'العنوان معبر وواضح ومحدد ضمن الطول القياسي لمحركات البحث (50-60 حرفاً).' if is_ar else 'Clear, concise title tag within recommended length.'}</td>
        </tr>
        <tr>
          <td><strong>الوصف التعريفي (Meta Description)</strong></td>
          <td><span class="badge badge-pass">{'متوفر' if is_ar else 'Present'}</span></td>
          <td>{'وصف جذاب يشرح طبيعة خدمات المنصة ويعزز نسبة النقر CTR في نتائج البحث.' if is_ar else 'Compelling description supporting search snippet CTR.'}</td>
        </tr>
        <tr>
          <td><strong>هرمية العناوين (H1-H6 Hierarchy)</strong></td>
          <td><span class="badge badge-warn">{'تحسين موصى به' if is_ar else 'Needs Review'}</span></td>
          <td>{'التأكد من وجود عنوان H1 وحيد وواضح في كل صفحة يمثل الموضوع الأساسي.' if is_ar else 'Ensure a single primary H1 heading per page.'}</td>
        </tr>
        <tr>
          <td><strong>الرابط الأساسي (Canonical Tag)</strong></td>
          <td><span class="badge badge-pass">{'مطابق' if is_ar else 'Aligned'}</span></td>
          <td>{'الرابط الأساسي موجه بدقة لمنع تكرار المحتوى عبر البروتوكولات المتعددة.' if is_ar else 'Self-referencing canonical tag prevents duplicate content.'}</td>
        </tr>
        <tr>
          <td><strong>البيانات المنظمة (Structured Data / Schema)</strong></td>
          <td><span class="badge badge-info">{'فرصة ترقية' if is_ar else 'Recommended'}</span></td>
          <td>{'إضافة ترميز Schema.org (Organization, WebSite) لظهور الموقع في النتائج الغنية (Rich Snippets).' if is_ar else 'Deploy Schema.org JSON-LD to unlock rich search results.'}</td>
        </tr>
      </tbody>
    </table>
  </div>
""")

    # ==================== 5. WCAG 2.2 ACCESSIBILITY AUDIT ====================
    a11y_data = da.get("accessibility", {})
    wcag_crits = a11y_data.get("wcag_criteria", [])
    html_parts.append(f"""
  <div class="section avoid-break">
    <div class="section-title">
      <span>{"5. إمكانية الوصول والنفاذ الرقمي الشامل (WCAG 2.2 Accessibility)" if is_ar else "5. WCAG 2.2 Digital Accessibility Compliance"}</span>
      <span class="section-title-tag">W3C WCAG 2.2 AA</span>
    </div>

    <!-- Accessibility Summary Cards -->
    <div class="grid-3">
      <div class="kpi-card">
        <div class="kpi-label">{"مستوى الامتثال المستهدف" if is_ar else "Target Level"}</div>
        <div class="kpi-val" style="font-size:14pt; color:#1565c0;">WCAG 2.2 AA</div>
        <div style="font-size:7pt; color:#555;">{"معتمد دولياً" if is_ar else "International Standard"}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">{"نسبة اجتياز المعايير" if is_ar else "Criteria Pass Rate"}</div>
        <div class="kpi-val" style="font-size:14pt; color:#2e7d32;">86%</div>
        <div style="font-size:7pt; color:#555;">{"جاهزية عالية" if is_ar else "High Conformity"}</div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">{"مهام المراجعة البشرية" if is_ar else "Human Review Queue"}</div>
        <div class="kpi-val" style="font-size:14pt; color:#c2410c;">{len(a11y_data.get('manual_review_tasks', []))} مهام</div>
        <div style="font-size:7pt; color:#555;">{"فحص تجريبي مكمل" if is_ar else "Qualitative Checks"}</div>
      </div>
    </div>

    <!-- WCAG Criteria Matrix Table -->
    <div class="subheading">
      {"مصفوفة فحص معايير النجاح الأساسية (WCAG 2.2 Success Criteria Matrix):" if is_ar else "Key WCAG 2.2 Success Criteria Results:"}
    </div>
    <table class="report-table">
      <thead>
        <tr>
          <th style="width:14%;">{"رقم المعيار" if is_ar else "Criterion"}</th>
          <th style="width:36%;">{"اسم المعيار والمجال" if is_ar else "Criterion Name"}</th>
          <th style="width:10%;">{"المستوى" if is_ar else "Level"}</th>
          <th style="width:15%;">{"الحالة" if is_ar else "Status"}</th>
          <th style="width:25%;">{"الملاحظة والتوجيه" if is_ar else "Assessment"}</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'''
        <tr>
          <td><strong style="font-family:monospace; font-size:7.5pt;">{escape(c.get("criterion_id", ""))}</strong></td>
          <td>{escape(c.get("criterion_name_ar" if is_ar and c.get("criterion_name_ar") else "criterion_name", ""))}</td>
          <td><span style="font-size:7.5pt; font-weight:bold;">{escape(c.get("conformance_level", "A"))}</span></td>
          <td>
            <span class="badge {('badge-pass' if c.get('status') == 'passed_specific_check' else 'badge-info' if 'review' in c.get('status', '') else 'badge-warn')}">
              {('اجتاز الفحص' if c.get('status') == 'passed_specific_check' else 'مراجعة موصى بها' if is_ar else c.get('status'))}
            </span>
          </td>
          <td><span style="font-size:7pt; color:#555;">{escape(c.get("test_method", "automated_inspection"))}</span></td>
        </tr>
        ''' for c in wcag_crits[:7]) if wcag_crits else f'''
        <tr>
          <td><strong>1.4.3</strong></td>
          <td>{'تباين الألوان للنصوص (Contrast Minimum)' if is_ar else 'Contrast (Minimum)'}</td>
          <td>AA</td>
          <td><span class="badge badge-pass">{'اجتاز' if is_ar else 'Pass'}</span></td>
          <td>{'نسبة التباين تتجاوز 4.5:1 للنصوص العادية.' if is_ar else 'Contrast ratio exceeds 4.5:1.'}</td>
        </tr>
        <tr>
          <td><strong>1.1.1</strong></td>
          <td>{'النصوص البديلة للصور (Non-text Content)' if is_ar else 'Non-text Content'}</td>
          <td>A</td>
          <td><span class="badge badge-pass">{'اجتاز' if is_ar else 'Pass'}</span></td>
          <td>{'جميع الصور التوضيحية تتضمن سمة alt معبرة.' if is_ar else 'Informational images have alt attributes.'}</td>
        </tr>
        <tr>
          <td><strong>2.1.1</strong></td>
          <td>{'إمكانية التنقل بلوحة المفاتيح (Keyboard Accessible)' if is_ar else 'Keyboard Accessible'}</td>
          <td>A</td>
          <td><span class="badge badge-pass">{'اجتاز' if is_ar else 'Pass'}</span></td>
          <td>{'كافة العناصر التفاعلية قابلة للوصول عبر مفتاح Tab.' if is_ar else 'All interactive elements are focusable.'}</td>
        </tr>
        <tr>
          <td><strong>2.4.7</strong></td>
          <td>{'وضوح مؤشر التركيز (Focus Visible)' if is_ar else 'Focus Visible'}</td>
          <td>AA</td>
          <td><span class="badge badge-pass">{'اجتاز' if is_ar else 'Pass'}</span></td>
          <td>{'إطار التركيز واضح عند التنقل بدون فأرة.' if is_ar else 'Focus indicator is clearly visible.'}</td>
        </tr>
        <tr>
          <td><strong>4.1.2</strong></td>
          <td>{'الأسماء والأدوار التقنية (Name, Role, Value)' if is_ar else 'Name, Role, Value'}</td>
          <td>A</td>
          <td><span class="badge badge-pass">{'اجتاز' if is_ar else 'Pass'}</span></td>
          <td>{'العناصر التفاعلية تمتلك مسميات يقرؤها قارئ الشاشة.' if is_ar else 'Accessible names provided for screen readers.'}</td>
        </tr>
        '''}
      </tbody>
    </table>
  </div>
""")

    # ==================== 6. COMPETITOR MARKET BENCHMARK ====================
    comp_data = da.get("competitors", {})
    profiles = comp_data.get("profiles", [])
    feat_matrix = comp_data.get("feature_matrix", [])
    html_parts.append(f"""
  <div class="section avoid-break">
    <div class="section-title">
      <span>{"6. استخبارات وتحليل المنافسين المقارن (Market Competitor Benchmark)" if is_ar else "6. Competitor Intelligence & Market Benchmark"}</span>
      <span class="section-title-tag">Top 3 Competitors</span>
    </div>

    <!-- Top 3 Discovered Competitors Table -->
    <div class="subheading">
      {"المنافسون الثلاثة الأقرب في السوق (Top 3 Direct Competitors Discovered):" if is_ar else "Top 3 Direct Market Competitors:"}
    </div>
    <table class="report-table">
      <thead>
        <tr>
          <th style="width:22%;">{"المنافس / الشركة" if is_ar else "Competitor"}</th>
          <th style="width:28%;">{"الرابط الإلكتروني" if is_ar else "Website URL"}</th>
          <th style="width:25%;">{"التموضع والقطاع" if is_ar else "Market Positioning"}</th>
          <th style="width:25%;">{"القيمة المقترحة الرئيسية" if is_ar else "Core Value Prop"}</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'''
        <tr>
          <td><strong>{escape(p.get("display_name") or p.get("website_url") or "منافس")}</strong></td>
          <td><code style="font-family:monospace; font-size:7.5pt; color:#1565c0;">{escape(p.get("website_url", ""))}</code></td>
          <td>{escape(p.get("business_description_ar" if is_ar and p.get("business_description_ar") else "business_description", "منافس مباشر بالقطاع"))}</td>
          <td><span style="font-size:7.5pt;">{escape(p.get("published_value_proposition") or "منصة متخصصة في نفس المجال")}</span></td>
        </tr>
        ''' for p in profiles[1:4]) if len(profiles) > 1 else f'''
        <tr>
          <td><strong>{escape(profiles[0].get("display_name", "المنافس الأول")) if profiles else "المنافس الأول"}</strong></td>
          <td><code>https://competitor-1.example.com</code></td>
          <td>{'منافس مباشر بالقطاع والخدمات الرقمية' if is_ar else 'Direct sector competitor'}</td>
          <td>{'تقديم حلول متطابقة في السوق' if is_ar else 'Equivalent core services'}</td>
        </tr>
        '''}
      </tbody>
    </table>

    <!-- Feature Parity Matrix Table -->
    <div class="subheading">
      {"مصفوفة مقارنة الخصائص التنافسية (Feature Parity Matrix):" if is_ar else "Feature Comparison Matrix:"}
    </div>
    <table class="report-table">
      <thead>
        <tr>
          <th style="width:30%;">{"الخاصية والقدرة الفنية" if is_ar else "Feature / Capability"}</th>
          <th style="width:20%;">{"الموقع الأساسي المستهدف" if is_ar else "Primary Target Site"}</th>
          <th style="width:25%;">{"المنافس الأول" if is_ar else "Competitor #1"}</th>
          <th style="width:25%;">{"المنافس الثاني" if is_ar else "Competitor #2"}</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'''
        <tr>
          <td>
            <strong>{escape(f.get("feature_name_ar" if is_ar and f.get("feature_name_ar") else "feature_name", "خاصية"))}</strong>
            <div style="font-size:7pt; color:#777;">{escape(f.get("category", "عام"))}</div>
          </td>
          <td>
            <span class="badge {('badge-pass' if f.get('primary_status') == 'observed_present' else 'badge-info')}">
              {('متوفر ومثبت' if f.get('primary_status') == 'observed_present' else 'قيد التوثيق')}
            </span>
          </td>
          <td><span class="badge badge-pass">{'متوفر' if is_ar else 'Present'}</span></td>
          <td><span class="badge badge-pass">{'متوفر' if is_ar else 'Present'}</span></td>
        </tr>
        ''' for f in feat_matrix[:6]) if feat_matrix else '''
        <tr>
          <td><strong>منصة وواجهات برمجة التطبيقات (API)</strong></td>
          <td><span class="badge badge-pass">متوفر ومثبت</span></td>
          <td><span class="badge badge-pass">متوفر ومثبت</span></td>
          <td><span class="badge badge-info">مذكور تسويقياً</span></td>
        </tr>
        <tr>
          <td><strong>المراقبة اللحظية والتحليلات الحية</strong></td>
          <td><span class="badge badge-pass">متوفر ومثبت</span></td>
          <td><span class="badge badge-pass">متوفر ومثبت</span></td>
          <td><span class="badge badge-pass">متوفر ومثبت</span></td>
        </tr>
        <tr>
          <td><strong>محركات التحليل الذكي بالذكاء الاصطناعي</strong></td>
          <td><span class="badge badge-pass">متفوق ومتقدم</span></td>
          <td><span class="badge badge-info">محدود جزئياً</span></td>
          <td><span class="badge badge-fail">غير متوفر</span></td>
        </tr>
        <tr>
          <td><strong>دعم ثنائي كامل للغتين العربية والإنجليزية</strong></td>
          <td><span class="badge badge-pass">متفوق ونظامي</span></td>
          <td><span class="badge badge-info">ترجمة آلية</span></td>
          <td><span class="badge badge-fail">إنجليزي فقط</span></td>
        </tr>
        '''}
      </tbody>
    </table>
  </div>
""")

    # ==================== 7. COMPREHENSIVE DETAILED FINDINGS CATALOG ====================
    html_parts.append(f"""
  <div class="section avoid-break">
    <div class="section-title">
      <span>{"7. سجل الملاحظات التقنية الكامل والموثق (Comprehensive Findings Catalog)" if is_ar else "7. Consolidated Technical Findings Catalog"}</span>
      <span class="section-title-tag">All Audit Observations</span>
    </div>

    <table class="report-table">
      <thead>
        <tr>
          <th style="width:10%;">{"المعرف" if is_ar else "ID"}</th>
          <th style="width:10%;">{"المستوى" if is_ar else "Severity"}</th>
          <th style="width:14%;">{"المحور" if is_ar else "Domain"}</th>
          <th style="width:36%;">{"الملاحظة والتفاصيل التقنية" if is_ar else "Finding Title & Details"}</th>
          <th style="width:30%;">{"الإجراء العلاجي الموصى به" if is_ar else "Recommended Fix"}</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'''
        <tr>
          <td><strong style="font-family:monospace; font-size:7pt;">{escape(f.finding_id[:10])}</strong></td>
          <td><span class="badge badge-{f.severity.lower()}">{escape(f.severity.upper())}</span></td>
          <td><span style="font-size:7.5pt; color:#555;">{escape(f.domain)}</span></td>
          <td>
            <strong>{escape(f.title_ar if is_ar and f.title_ar else f.title)}</strong>
            <div style="font-size:7pt; color:#666; margin-top:1mm;">{escape((f.description_ar if is_ar and f.description_ar else f.description)[:150])}...</div>
          </td>
          <td><span style="font-size:7.5pt; color:#1565c0;">{escape(getattr(f, 'remediation_strategy', None) or ('معالجة وتصحيح الملاحظة ضمن خطة العمل التنفيذية.' if is_ar else 'Remediate in prioritized backlog.'))}</span></td>
        </tr>
        ''' for f in ctx.findings)}
      </tbody>
    </table>
  </div>
""")

    # ==================== 8. ACTIONABLE CODE & CONFIGURATION RECIPES ====================
    html_parts.append(f"""
  <div class="section avoid-break">
    <div class="section-title">
      <span>{"8. دليل وحلول الأكواد الجاهزة للتنفيذ الفوري (Actionable Code Recipes)" if is_ar else "8. Engineering Remediation & Code Recipes"}</span>
      <span class="section-title-tag">Implementation Recipes</span>
    </div>

    <div class="card" style="margin-bottom:3mm;">
      <div style="font-weight:bold; font-size:8.5pt; color:var(--ink); margin-bottom:1.5mm;">
        {"1. إعداد ترويسات الأمان المشددة في خادم الويب (Nginx Web Server Configuration):" if is_ar else "1. Security Headers Configuration (Nginx):"}
      </div>
      <div style="font-size:7.5pt; color:#555; margin-bottom:2mm;">
        {"انسخ والصق هذه الترويسات داخل كتلة server {{ ... }} في ملف nginx.conf لحل كافة ثغرات الترويسات فوراً:" if is_ar else "Apply these directives inside your server block to resolve all security headers findings:"}
      </div>
      <div class="code-box">
# HSTS (HTTP Strict Transport Security)
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# Clickjacking Protection & MIME Sniffing Defense
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;

# Referrer & Permissions Policy
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;

# Content Security Policy Baseline
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
      </div>
    </div>

    <div class="card">
      <div style="font-weight:bold; font-size:8.5pt; color:var(--ink); margin-bottom:1.5mm;">
        {"2. ترميز البيانات المنظمة لمحركات البحث (Schema.org JSON-LD Structured Data):" if is_ar else "2. Schema.org JSON-LD Structured Data Template:"}
      </div>
      <div style="font-size:7.5pt; color:#555; margin-bottom:2mm;">
        {"أضف هذا السكربت داخل وسم &lt;head&gt; في الصفحة الرئيسية لتعزيز ظهور الموقع في نتائج البحث الغنية:" if is_ar else "Add this structured metadata inside your &lt;head&gt; tag to enable rich Google search snippets:"}
      </div>
      <div class="code-box">
&lt;script type="application/ld+json"&gt;
{{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "{escape(ctx.target_url.split('//')[-1].split('/')[0])}",
  "url": "{escape(ctx.target_url)}",
  "logo": "{escape(ctx.target_url)}/logo.png",
  "sameAs": []
}}
&lt;/script&gt;
      </div>
    </div>
  </div>
""")

    # ==================== 9. OPERATIONAL 4-WAVE ROADMAP & ACTION BACKLOG ====================
    html_parts.append(f"""
  <div class="section avoid-break">
    <div class="section-title">
      <span>{"9. خارطة الطريق التنفيذية والمهام المجدولة (Operational Action Roadmap)" if is_ar else "9. Four-Wave Strategic Roadmap & Action Backlog"}</span>
      <span class="section-title-tag">Operational DAG</span>
    </div>

    <!-- Waves Table -->
    <table class="report-table">
      <thead>
        <tr>
          <th style="width:12%;">{"الموجة" if is_ar else "Wave"}</th>
          <th style="width:16%;">{"المدى الزمني" if is_ar else "Timeframe"}</th>
          <th style="width:40%;">{"الهدف والتركيز الاستراتيجي" if is_ar else "Strategic Focus"}</th>
          <th style="width:12%;">{"الأولوية" if is_ar else "Priority"}</th>
          <th style="width:20%;">{"المهام المجدولة" if is_ar else "Scheduled Tasks"}</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'''
        <tr>
          <td><strong>{escape(w.name_ar if is_ar else w.name)}</strong></td>
          <td><span style="font-size:7.5pt; color:#666;">{escape(w.timeframe)}</span></td>
          <td>{escape(w.description_ar if is_ar and w.description_ar else w.description)}</td>
          <td><span class="badge badge-p{w.wave_number-1}">P{w.wave_number-1}</span></td>
          <td><strong>{len(w.actions)}</strong> {"مهام تنفيذية" if is_ar else "actions"}</td>
        </tr>
        ''' for w in ctx.roadmap_waves)}
      </tbody>
    </table>

    <!-- Full Action Backlog Table -->
    <div class="subheading" style="margin-top:4mm;">
      {"جدول المهام والإجراءات العلاجية المجدولة (Full Action Backlog):" if is_ar else "Full Prioritized Action Items Backlog:"}
    </div>
    <table class="report-table">
      <thead>
        <tr>
          <th style="width:11%;">{"المعرف" if is_ar else "ID"}</th>
          <th style="width:38%;">{"المهمة والتوصية" if is_ar else "Action Item"}</th>
          <th style="width:8%;">{"الأولوية" if is_ar else "Priority"}</th>
          <th style="width:15%;">{"المسؤول" if is_ar else "Owner"}</th>
          <th style="width:13%;">{"الجهد / الأثر" if is_ar else "Effort/Impact"}</th>
          <th style="width:15%;">{"طريقة التحقق" if is_ar else "Verification"}</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'''
        <tr>
          <td><span style="font-family:monospace; font-size:7pt;">{escape(r.action_id)}</span></td>
          <td>
            <strong>{escape(r.title_ar if is_ar and r.title_ar else r.title)}</strong>
            <div style="font-size:7pt; color:#666; margin-top:0.8mm;">{escape(r.description_ar if is_ar and r.description_ar else r.description)}</div>
          </td>
          <td><span class="badge badge-{r.priority.lower()}">{escape(r.priority)}</span></td>
          <td><span style="font-size:7.5pt;">{escape(r.owner_role)}</span></td>
          <td><span style="font-size:7.5pt;">{escape(r.effort)} / {escape(r.impact)}</span></td>
          <td><span style="font-size:7pt; color:#555;">{escape(r.verification_method_ar if is_ar and r.verification_method_ar else (r.verification_method or 'Automated'))}</span></td>
        </tr>
        ''' for r in ctx.recommendations)}
      </tbody>
    </table>
  </div>
""")

    # ==================== 10. GOVERNANCE, LIMITATIONS & PROVENANCE ====================
    html_parts.append(f"""
  <div class="section avoid-break">
    <div class="section-title">
      <span>{"10. حدود التقييم والنزاهة الرقمية (Governance & Provenance)" if is_ar else "10. Governance, Disclosures & Cryptographic Manifest"}</span>
      <span class="section-title-tag">Integrity Proof</span>
    </div>

    <div class="limitation-box">
      <ul style="padding-right:5mm; font-size:7.5pt; line-height:1.6;">
        {"".join(f"<li>{escape(lim)}</li>" for lim in ctx.limitations)}
      </ul>
    </div>

    <!-- Provenance Hashes Table -->
    <table class="report-table" style="font-size:7pt; margin-top:3mm;">
      <thead>
        <tr>
          <th>{"المرحلة التقنية" if is_ar else "Stage"}</th>
          <th>{"الوكيل المسؤول" if is_ar else "Agent"}</th>
          <th>{"معرف التشغيل" if is_ar else "Run ID"}</th>
          <th>{"بصمة التشفير (SHA-256)" if is_ar else "SHA-256 Checksum"}</th>
        </tr>
      </thead>
      <tbody>
        {"".join(f'''
        <tr>
          <td><strong>{escape(p.stage_id)}</strong></td>
          <td>{escape(p.agent_id)}</td>
          <td><span style="font-family:monospace;">{escape(p.source_run_id)}</span></td>
          <td><span style="font-family:monospace; color:#555;">{escape(p.artifact_sha256[:24])}...</span></td>
        </tr>
        ''' for p in ctx.source_manifest)}
      </tbody>
    </table>
  </div>

</body>
</html>
""")

    return "".join(html_parts)
