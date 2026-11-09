"""Manual Accessibility Review Workflow Engine for Site DNA Phase 10."""

import uuid
from typing import Optional

from site_dna.schemas.accessibility import (
    AccessibilityPageRecord,
    ContrastAssessment,
    FormAccessibilityAssessment,
    ImagesMediaAssessment,
    KeyboardFocusAssessment,
    ManualReviewTask,
)


class ManualReviewEngine:
    """Generates structured human verification tasks for accessibility dimensions that require human judgment."""

    def generate_tasks(
        self,
        pages: Optional[list[AccessibilityPageRecord]] = None,
        images_media: Optional[ImagesMediaAssessment] = None,
        keyboard: Optional[KeyboardFocusAssessment] = None,
        contrast: Optional[ContrastAssessment] = None,
        forms: Optional[FormAccessibilityAssessment] = None,
        has_complex_images: bool = False,
        has_interactive_widgets: bool = False,
        has_auth_forms: bool = False,
    ) -> list[ManualReviewTask]:
        """Create structured manual review tasks with clear testing steps in Arabic and English."""
        tasks: list[ManualReviewTask] = []
        primary_url = pages[0].page_url if pages else "https://example.com"
        images_media = images_media or ImagesMediaAssessment()
        keyboard = keyboard or KeyboardFocusAssessment()
        contrast = contrast or ContrastAssessment()
        forms = forms or FormAccessibilityAssessment()

        # 1. Image alternative text quality
        if (
            images_media.informative_images_count > 0
            or images_media.manual_media_reviews_needed > 0
            or has_complex_images
        ):
            tasks.append(
                ManualReviewTask(
                    review_id=f"rev-{uuid.uuid4().hex[:8]}",
                    page_url=primary_url,
                    component_reference="img[alt]",
                    wcag_criterion="1.1.1 Non-text Content",
                    review_question="Does the alternative text convey the same purpose and meaning as the image in context?",
                    review_question_ar="هل يعبر النص البديل عن نفس المعنى والغرض الذي تؤديه الصورة في سياق الصفحة؟",
                    why_automation_is_insufficient="Automated tools can only verify that alt attributes exist, not whether the written description is accurate, helpful, or appropriate.",
                    why_automation_is_insufficient_ar="الأدوات الآلية تتحقق فقط من وجود سمة alt، لكنها تعجز عن تقييم دقة الوصف البلاغي ومدى فائدته للمستخدم.",
                    manual_steps=[
                        "Inspect informative images on the page.",
                        "Read the alt attribute text alongside surrounding content.",
                        "Verify whether a blind user hearing the text would receive equivalent information.",
                    ],
                    manual_steps_ar=[
                        "عاين الصور التوضيحية في الصفحة وسياق ظهورها.",
                        "اقرأ النص البديل المكتوب وقارنه بمحتوى الفقرات المحيطة.",
                        "تأكد مما إذا كان الكفيف الذي يستمع للوصف سيحصل على نفس المعلومة التي يراها المبصر.",
                    ],
                    expected_accessible_behavior="Alternative text succinctly conveys the key message without buzzwords, file extensions, or redundant phrases like 'image of'.",
                    expected_accessible_behavior_ar="النص البديل ينقل الرسالة الجوهرية بإيجاز ودقة دون حشو أو أسماء ملفات أو عبارات مثل 'صورة لـ'.",
                    available_evidence_ids=images_media.evidence_ids,
                    review_status="pending_manual_review",
                )
            )

        # 2. Keyboard traps and focus containment
        tasks.append(
            ManualReviewTask(
                review_id=f"rev-{uuid.uuid4().hex[:8]}",
                page_url=primary_url,
                component_reference="Interactive Modals & Menus",
                wcag_criterion="2.1.2 No Keyboard Trap",
                review_question="Can keyboard users navigate into, operate, and exit all interactive components without getting trapped?",
                review_question_ar="هل يستطيع مستخدم لوحة المفاتيح الدخول إلى كافة النوافذ والقوائم والتنقل داخلها والخروج منها دون أن يعلق؟",
                why_automation_is_insufficient="Static code inspection cannot trigger dynamic event listeners or guarantee that focus escapes upon pressing Escape or Tab.",
                why_automation_is_insufficient_ar="الفحص الساكن للكود لا يمكنه تفعيل مستمعات الأحداث الحية أو ضمان عودة التركيز عند الضغط على Escape أو Tab.",
                manual_steps=[
                    "Navigate through the entire page using only the Tab and Shift+Tab keys.",
                    "Open any modal dialog, dropdown menu, or drawer.",
                    "Attempt to close the component using the Escape key.",
                    "Verify focus returns to the triggering button.",
                ],
                manual_steps_ar=[
                    "تنقل عبر الصفحة بالكامل باستخدام زري Tab و Shift+Tab فقط دون لمس الفأرة.",
                    "افتح النوافذ المنبثقة والقوائم المنسدلة المتاحة.",
                    "حاول إغلاق المكون المفتوح بالضغط على زر Escape.",
                    "تأكد من عودة مؤشر التركيز إلى الزر الذي فتح النافذة تلقائياً.",
                ],
                expected_accessible_behavior="Focus is trapped inside open modals, closes smoothly with Escape, and returns to the initial trigger.",
                expected_accessible_behavior_ar="يتحرك التركيز بسلاسة داخل النوافذ المفتوحة، ويغلق بـ Escape، ويعود للزر الأساسي دون أي فخاخ تركيز.",
                available_evidence_ids=keyboard.evidence_ids,
                review_status="pending_manual_review",
            )
        )

        # 3. Complex background color contrast
        if contrast.complex_backgrounds_needing_review > 0 or has_complex_images:
            tasks.append(
                ManualReviewTask(
                    review_id=f"rev-{uuid.uuid4().hex[:8]}",
                    page_url=primary_url,
                    component_reference="Text over Gradients / Hero Images",
                    wcag_criterion="1.4.3 Contrast (Minimum)",
                    review_question="Is text rendered over hero images or gradients legible across all screen resolutions and dark/light modes?",
                    review_question_ar="هل النصوص الموضوعة فوق صور الخلفية أو التدرجات اللونية واضحة ومقروءة بكافة درجات السطوع؟",
                    why_automation_is_insufficient="Background images and multi-stop CSS gradients vary in luminance across different pixels and cannot be reduced to a single deterministic RGB value.",
                    why_automation_is_insufficient_ar="صور الخلفيات والتدرجات اللونية تختلف في نسبة سطوعها من بكسل لآخر ولا يمكن حسابها برقم RGB ثابت وآلي.",
                    manual_steps=[
                        "Use an eyedropper contrast tool to sample the lightest and darkest pixels directly behind the text.",
                        "Verify minimum 4.5:1 ratio against the worst-case background sample.",
                        "Check if a semi-transparent dark overlay exists between the image and text.",
                    ],
                    manual_steps_ar=[
                        "استخدم أداة قياس التباين اليدوي لأخذ عينات من أفتح وأغمق بكسل خلف حروف النص مباشرة.",
                        "تأكد من تحقيق نسبة 4.5:1 مقارنة بأسوأ نقطة خلفية ممكنة.",
                        "تحقق من وجود طبقة تظليل داكنة تحمي وضوح النص فوق الصورة.",
                    ],
                    expected_accessible_behavior="Text maintains at least 4.5:1 contrast against all portions of the underlying gradient or image.",
                    expected_accessible_behavior_ar="يحافظ النص على نسبة تباين 4.5:1 على الأقل أمام كافة أجزاء الصورة أو التدرج اللوني.",
                    available_evidence_ids=contrast.evidence_ids,
                    review_status="pending_manual_review",
                )
            )

        # 4. Accessible authentication
        if forms.has_accessible_authentication_considerations or has_auth_forms:
            tasks.append(
                ManualReviewTask(
                    review_id=f"rev-{uuid.uuid4().hex[:8]}",
                    page_url=primary_url,
                    component_reference="Auth / Sign-in Form",
                    wcag_criterion="3.3.8 Accessible Authentication (Minimum)",
                    review_question="Does the login process allow users to complete authentication without memorizing complex secrets or solving cognitive puzzles?",
                    review_question_ar="هل تتيح عملية تسجيل الدخول إتمام المصادقة دون إجبار المستخدم على حفظ كلمات سر معقدة أو حل ألغاز إدراكية؟",
                    why_automation_is_insufficient="Automated tools cannot verify if password managers can auto-fill credentials or if third-party CAPTCHAs offer accessible audio alternatives.",
                    why_automation_is_insufficient_ar="الأدوات الآلية لا يمكنها محاكاة برامج إدارة كلمات المرور أو اختبار كفاءة البدائل الصوتية لكلمات التحقق CAPTCHA.",
                    manual_steps=[
                        "Attempt to paste a password from the clipboard into the password input.",
                        "Verify browser password autofill is supported.",
                        "Check that no cognitive function test (e.g. puzzle, math question) is required without an accessible alternative.",
                    ],
                    manual_steps_ar=[
                        "جرب نسخ كلمة مرور من الحافظة ولصقها داخل حقل الإدخال للتأكد من عدم حظر اللصق.",
                        "تأكد من دعم الإكمال التلقائي لمديري كلمات المرور (وجود autocomplete='current-password').",
                        "تأكد من عدم فرض ألغاز إدراكية أو أسئلة حسابية تعجيزية دون توفير بديل سهل وميسر.",
                    ],
                    expected_accessible_behavior="Users can copy-paste credentials, use password managers, or leverage WebAuthn / passkeys seamlessly.",
                    expected_accessible_behavior_ar="يمكن للمستخدمين لصق الاعتمادات واستخدام مديري كلمات المرور ومفاتيح المرور دون أي قيود.",
                    available_evidence_ids=forms.evidence_ids,
                    review_status="pending_manual_review",
                )
            )

        return tasks


ManualReviewGenerator = ManualReviewEngine
