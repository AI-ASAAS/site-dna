"""Remediation Recommendation Synthesis Engine for Site DNA Phase 10."""

import uuid

from site_dna.schemas.accessibility import (
    AccessibilityFinding,
    AccessibilityPageRecord,
    AccessibilityRecommendation,
)


class AccessibilityRecommendationEngine:
    """Generates prioritized, code-grounded remediation recommendations for observed barriers."""

    def synthesize_recommendations(
        self,
        pages: list[AccessibilityPageRecord],
        findings: list[AccessibilityFinding],
    ) -> list[AccessibilityRecommendation]:
        """Group and prioritize remediation actions based on verified findings."""
        recommendations: list[AccessibilityRecommendation] = []
        primary_url = pages[0].page_url if pages else "https://example.com"

        # Check for missing form labels (P1)
        form_findings = [f for f in findings if "unlabeled" in f.finding_id or f.category == "forms_interaction"]
        if form_findings:
            recommendations.append(
                AccessibilityRecommendation(
                    recommendation_id=f"rec-{uuid.uuid4().hex[:8]}",
                    title="Associate Explicit Programmatic Labels with All Form Inputs",
                    title_ar="ربط تسميات برمجية صريحة بكافة حقول ونماذج الإدخال",
                    related_finding_ids=[f.finding_id for f in form_findings],
                    priority="P1",
                    affected_pages=[primary_url],
                    wcag_criteria=[
                        "1.3.1 Info and Relationships",
                        "3.3.2 Labels or Instructions",
                        "4.1.2 Name, Role, Value",
                    ],
                    evidence_ids=[ev for f in form_findings for ev in f.evidence_ids],
                    observed_barrier="Form fields lacking accessible names or <label> programmatic association.",
                    observed_barrier_ar="حقول إدخال تفتقر للتسميات البرمجية المتاحة أو الارتباط الصريح بوسم <label>.",
                    user_impact="Screen reader users cannot identify what input is expected, causing form abandonment.",
                    user_impact_ar="مستخدمو قارئات الشاشة لا يستطيعون معرفة المطلوب في الحقل، مما يؤدي إلى فشل التفاعل.",
                    recommended_remediation="Add <label for='input-id'> matching the input ID or provide aria-label.",
                    recommended_remediation_ar="أضف وسم <label for='input-id'> متطابق مع معرف الحقل أو وفر سمة aria-label واضحة.",
                    code_snippet="<!-- Accessible Form Field Markup -->\n<label for='user-email' class='block text-sm font-medium'>البريد الإلكتروني</label>\n<input id='user-email' type='email' name='email' autocomplete='email' required aria-required='true' class='border rounded p-2' />",
                    implementation_guidance="Ensure every interactive input has a corresponding label element whose 'for' attribute strictly matches the input's 'id'.",
                    implementation_guidance_ar="تأكد من أن كل حقل تفاعلي يمتلك عنصر label متطابق تماماً في سمة for مع معرف الحقل id.",
                    verification_steps=[
                        "Inspect rendered HTML to confirm matching 'for' and 'id' attributes.",
                        "Click the visual label text; the browser focus must automatically jump into the input field.",
                    ],
                    verification_steps_ar=[
                        "عاين الكود للتأكد من تطابق سمة for مع معرف الحقل id.",
                        "انقر بالفأرة على النص التوضيحي، وتأكد من انتقال مؤشر الكتابة تلقائياً إلى داخل الحقل.",
                    ],
                    manual_validation_needed=False,
                    estimated_effort="low",
                )
            )

        # Check for functional icon buttons missing accessible names (P1)
        btn_findings = [f for f in findings if "button-name" in f.finding_id or "icon" in f.title.lower()]
        if btn_findings:
            recommendations.append(
                AccessibilityRecommendation(
                    recommendation_id=f"rec-{uuid.uuid4().hex[:8]}",
                    title="Provide Accessible Names for Icon-Only Buttons and Links",
                    title_ar="توفير أسماء متاحة للأزرار والروابط التي تعتمد على الأيقونات فقط",
                    related_finding_ids=[f.finding_id for f in btn_findings],
                    priority="P1",
                    affected_pages=[primary_url],
                    wcag_criteria=["1.1.1 Non-text Content", "4.1.2 Name, Role, Value"],
                    evidence_ids=[ev for f in btn_findings for ev in f.evidence_ids],
                    observed_barrier="Buttons containing only SVG icons without text or aria-label.",
                    observed_barrier_ar="أزرار تفاعلية تحتوي على أيقونات SVG فقط دون نص أو تسمية aria-label.",
                    user_impact="Assistive technologies announce the button as 'unlabelled button' without explaining its action.",
                    user_impact_ar="تقوم قارئات الشاشة بقراءة الزر كـ 'زر غير مسمى' دون شرح للإجراء الذي يؤديه.",
                    recommended_remediation="Add an aria-label attribute describing the action or include visually-hidden text.",
                    recommended_remediation_ar="أضف سمة aria-label تصف الإجراء بوضوح أو أضف نصاً مخفياً بصرياً داخل الزر.",
                    code_snippet="<!-- Accessible Icon Button -->\n<button type='button' aria-label='إغلاق النافذة' class='p-2'>\n  <svg aria-hidden='true' class='w-5 h-5'>...</svg>\n</button>",
                    implementation_guidance="Attach aria-label to the button tag and mark the inner SVG with aria-hidden='true' to prevent redundant announcements.",
                    implementation_guidance_ar="ضع سمة aria-label على وسم button وضع سمة aria-hidden='true' على أيقونة SVG لتفادي التكرار.",
                    verification_steps=[
                        "Inspect button with browser accessibility tree.",
                        "Confirm accessible name matches the intended action (e.g., 'Close', 'Search').",
                    ],
                    verification_steps_ar=[
                        "عاين الزر في شجرة إمكانية الوصول بالمتصفح Accessibility Tree.",
                        "تأكد من أن الاسم المتاح يصف الوظيفة الحقيقية بدقة (مثل: 'إغلاق', 'بحث').",
                    ],
                    manual_validation_needed=False,
                    estimated_effort="low",
                )
            )

        # Check for visible focus suppression (P2)
        focus_findings = [f for f in findings if "focus" in f.title.lower() or "outline" in f.title.lower()]
        if focus_findings:
            recommendations.append(
                AccessibilityRecommendation(
                    recommendation_id=f"rec-{uuid.uuid4().hex[:8]}",
                    title="Restore High-Visibility Focus Indicators for Keyboard Users",
                    title_ar="استعادة مؤشرات التركيز المرئية بوضوح لمستخدمي لوحة المفاتيح",
                    related_finding_ids=[f.finding_id for f in focus_findings],
                    priority="P2",
                    affected_pages=[primary_url],
                    wcag_criteria=["2.4.7 Focus Visible", "2.4.11 Focus Not Obscured (Minimum)"],
                    evidence_ids=[ev for f in focus_findings for ev in f.evidence_ids],
                    observed_barrier="CSS styles suppress native outline without providing a visible focus-visible replacement.",
                    observed_barrier_ar="أنماط CSS تلغي الإطار الافتراضي outline:none دون توفير بديل بارز عند التنقل باللوحة.",
                    user_impact="Sighted keyboard users cannot determine which element currently has focus.",
                    user_impact_ar="المستخدمون الذين يعتمدون على لوحة المفاتيح يفقدون مسار التحديد ولا يعرفون أين يقف التركيز.",
                    recommended_remediation="Apply distinct :focus-visible outlines with at least 3:1 contrast against background.",
                    recommended_remediation_ar="طبق إطار :focus-visible واضح بنسبة تباين 3:1 على الأقل أمام الخلفية المحيطة.",
                    code_snippet="/* Accessible Focus Visible Styling */\n:focus-visible {\n  outline: 2px solid #ba9555 !important;\n  outline-offset: 2px !important;\n}",
                    implementation_guidance="Do not remove outlines globally with ':focus { outline: none }'. Always specify high-contrast ':focus-visible' styles.",
                    implementation_guidance_ar="لا تلغِ مؤشرات التركيز بشكل عام عبر outline:none، واحرص دوماً على تخصيص :focus-visible واضح.",
                    verification_steps=[
                        "Press Tab repeatedly to navigate across links and buttons.",
                        "Verify a crisp, visible ring appears around each focused element.",
                    ],
                    verification_steps_ar=[
                        "اضغط زر Tab للتنقل بين الأزرار والروابط.",
                        "تأكد من ظهور حلقة تركيز واضحة ومتباينة تحيط بالعنصر المحدد مباشرة.",
                    ],
                    manual_validation_needed=True,
                    estimated_effort="low",
                )
            )

        # Check for missing skip link (P2)
        if not any("skip" in r.title.lower() for r in recommendations):
            recommendations.append(
                AccessibilityRecommendation(
                    recommendation_id=f"rec-{uuid.uuid4().hex[:8]}",
                    title="Implement a Skip-to-Content Link at the Top of Every Page",
                    title_ar="إضافة رابط 'تجاوز إلى المحتوى الرئيسي' في أعلى كل صفحة",
                    related_finding_ids=[],
                    priority="P2",
                    affected_pages=[primary_url],
                    wcag_criteria=["2.4.1 Bypass Blocks"],
                    evidence_ids=[],
                    observed_barrier="Repetitive header and navigation blocks lack a quick bypass mechanism.",
                    observed_barrier_ar="تكرار قوائم الترويسة والتنقل في كل صفحة دون وسيلة سريعة لتجاوزها.",
                    user_impact="Keyboard users must press Tab dozens of times on every page before reaching main content.",
                    user_impact_ar="يضطر مستخدم لوحة المفاتيح للضغط على Tab عشرات المرات في كل صفحة للوصول للمحتوى.",
                    recommended_remediation="Add a visually hidden link as the first body element that becomes visible on focus and jumps to <main id='main-content'>.",
                    recommended_remediation_ar="أضف رابطاً مخفياً في بداية body يظهر فور التركيز عليه وينقل المؤشر مباشرة إلى <main id='main-content'>.",
                    code_snippet="<!-- Skip Link Example -->\n<a href='#main-content' class='sr-only focus:not-sr-only focus:fixed focus:top-4 focus:right-4 focus:z-50 focus:bg-amber-600 focus:text-white focus:p-3 focus:rounded-lg'>\n  تجاوز إلى المحتوى الرئيسي\n</a>\n...\n<main id='main-content' tabindex='-1'>...</main>",
                    implementation_guidance="Place the skip link as the very first focusable element inside the document body.",
                    implementation_guidance_ar="ضع رابط التجاوز كأول عنصر تفاعلي داخل وسم body مباشرة ليكون أول ما يصله زر Tab.",
                    verification_steps=[
                        "Refresh page and press Tab once.",
                        "Verify the skip link becomes visible and pressing Enter scrolls directly to main content.",
                    ],
                    verification_steps_ar=[
                        "حدث الصفحة واضغط Tab مرة واحدة.",
                        "تأكد من ظهور رابط التجاوز وعند الضغط على Enter ينتقل التركيز فوراً إلى بداية المحتوى الرئيسي.",
                    ],
                    manual_validation_needed=False,
                    estimated_effort="low",
                )
            )

        return recommendations
