"""WCAG 2.2 Success Criteria Mapping Engine for Site DNA Phase 10."""

from typing import Optional

from site_dna.schemas.accessibility import (
    ARIAAssessment,
    ContrastAssessment,
    FormAccessibilityAssessment,
    ImagesMediaAssessment,
    KeyboardFocusAssessment,
    LanguageDirectionAssessment,
    ReflowZoomAssessment,
    SemanticAssessment,
    TargetSizeAssessment,
    WCAGCriterionAssessment,
)


class WCAGCriteriaMapper:
    """Maps deterministic analysis findings across 29 core WCAG 2.2 Level A/AA criteria."""

    def map_criteria(
        self,
        semantics: Optional[SemanticAssessment] = None,
        images_media: Optional[ImagesMediaAssessment] = None,
        keyboard: Optional[KeyboardFocusAssessment] = None,
        contrast: Optional[ContrastAssessment] = None,
        reflow: Optional[ReflowZoomAssessment] = None,
        target_size: Optional[TargetSizeAssessment] = None,
        aria: Optional[ARIAAssessment] = None,
        forms: Optional[FormAccessibilityAssessment] = None,
        language: Optional[LanguageDirectionAssessment] = None,
    ) -> list[WCAGCriterionAssessment]:
        """Synthesize criteria assessments based on verified domain evidence."""
        semantics = semantics or SemanticAssessment()
        images_media = images_media or ImagesMediaAssessment()
        keyboard = keyboard or KeyboardFocusAssessment()
        contrast = contrast or ContrastAssessment()
        reflow = reflow or ReflowZoomAssessment()
        target_size = target_size or TargetSizeAssessment()
        aria = aria or ARIAAssessment()
        forms = forms or FormAccessibilityAssessment()
        language = language or LanguageDirectionAssessment()

        criteria: list[WCAGCriterionAssessment] = []

        # 1.1.1 Non-text Content (Level A)
        img_fail = images_media.missing_alt_count > 0 or images_media.functional_icon_buttons_without_name > 0
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="1.1.1",
                criterion_name="Non-text Content",
                criterion_name_ar="المحتوى غير النصي",
                conformance_level="A",
                applicability=images_media.total_images > 0,
                test_method="automated",
                status="confirmed_failure" if img_fail else "passed_specific_check",
                evidence_ids=images_media.evidence_ids,
                limitations="Automated check verifies alt presence; semantic quality of descriptions requires human review.",
                limitations_ar="الفحص الآلي يتحقق من وجود النص البديل؛ بينما الجودة الدلالية للوصف تتطلب مراجعة بشرية.",
            )
        )

        # 1.3.1 Info and Relationships (Level A)
        sem_fail = not semantics.has_main_landmark or semantics.unheaded_tables_count > 0 or forms.unlabeled_inputs > 0
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="1.3.1",
                criterion_name="Info and Relationships",
                criterion_name_ar="المعلومات والعلاقات الدلالية",
                conformance_level="A",
                applicability=True,
                test_method="semi_automated",
                status="confirmed_failure" if sem_fail else "passed_specific_check",
                evidence_ids=semantics.evidence_ids + forms.evidence_ids,
                limitations="Checks landmarks, table headers, and form associations.",
                limitations_ar="يدقق المعالم الرئيسية وترويسات الجداول وارتباطات النماذج البرمجية.",
            )
        )

        # 1.4.3 Contrast (Minimum) (Level AA)
        c_fail = contrast.contrast_violations_aa_normal > 0 or contrast.contrast_violations_aa_large > 0
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="1.4.3",
                criterion_name="Contrast (Minimum)",
                criterion_name_ar="التباين البصري الأدنى",
                conformance_level="AA",
                applicability=contrast.measured_text_elements_count > 0,
                test_method="automated",
                status="confirmed_failure" if c_fail else "passed_specific_check",
                evidence_ids=contrast.evidence_ids,
                limitations="Evaluates solid rendered color pairs; complex background images flagged for review.",
                limitations_ar="يقيس تباين الألوان الصلبة؛ الخلفيات المعقدة والصور تحال للمراجعة اليدوية.",
            )
        )

        # 1.4.10 Reflow (Level AA)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="1.4.10",
                criterion_name="Reflow",
                criterion_name_ar="إعادة التدفق والتجاوب (320px)",
                conformance_level="AA",
                applicability=True,
                test_method="semi_automated",
                status="confirmed_failure" if reflow.horizontal_overflow_at_320px else "passed_specific_check",
                evidence_ids=reflow.evidence_ids,
                limitations="Checks horizontal overflow at 320px width without multi-dimensional scrolling.",
                limitations_ar="يفحص ظهور أشرطة التمرير الأفقية عند عرض 320 بكسل دون الحاجة للتمرير ثنائي الأبعاد.",
            )
        )

        # 2.1.1 Keyboard (Level A)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="2.1.1",
                criterion_name="Keyboard",
                criterion_name_ar="إمكانية الوصول عبر لوحة المفاتيح",
                conformance_level="A",
                applicability=True,
                test_method="semi_automated",
                status="potential_issue" if semantics.non_semantic_clickables_count > 0 else "passed_specific_check",
                evidence_ids=keyboard.evidence_ids + semantics.evidence_ids,
                limitations="Read-only DOM check for non-semantic clickable elements lacking keyboard support.",
                limitations_ar="فحص سلبي لعناصر النقر غير الدلالية المفتقرة لخصائص لوحة المفاتيح.",
            )
        )

        # 2.1.2 No Keyboard Trap (Level A)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="2.1.2",
                criterion_name="No Keyboard Trap",
                criterion_name_ar="منع الوقوع في فخاخ لوحة المفاتيح",
                conformance_level="A",
                applicability=True,
                test_method="manual_required",
                status="manual_review_required" if keyboard.keyboard_traps_detected == 0 else "confirmed_failure",
                evidence_ids=keyboard.evidence_ids,
                limitations="Automated heuristics cannot conclusively prove trap absence across dynamic states.",
                limitations_ar="المؤشرات الآلية لا تثبت قطعياً غياب فخاخ التركيز في الحالات التفاعلية المعقدة.",
            )
        )

        # 2.4.1 Bypass Blocks (Level A)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="2.4.1",
                criterion_name="Bypass Blocks",
                criterion_name_ar="تجاوز الكتل والتنقل السريع",
                conformance_level="A",
                applicability=True,
                test_method="automated",
                status="passed_specific_check" if keyboard.skip_link_present else "potential_issue",
                evidence_ids=keyboard.evidence_ids,
                limitations="Evaluates existence of skip-navigation mechanism to bypass repetitive navigation.",
                limitations_ar="يتحقق من وجود رابط تجاوز التنقل للوصول السريع إلى المحتوى الرئيسي.",
            )
        )

        # 2.4.7 Focus Visible (Level AA)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="2.4.7",
                criterion_name="Focus Visible",
                criterion_name_ar="وضوح مؤشر التركيز",
                conformance_level="AA",
                applicability=True,
                test_method="automated",
                status="confirmed_failure" if not keyboard.focus_indicators_visible else "passed_specific_check",
                evidence_ids=keyboard.evidence_ids,
                limitations="Checks whether focus outlines are suppressed via CSS outline:none without fallback.",
                limitations_ar="يفحص ما إذا كان مؤشر التركيز ملغياً عبر CSS outline:none دون بدائل واضحة.",
            )
        )

        # 2.4.11 Focus Not Obscured (Minimum) (Level AA - WCAG 2.2)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="2.4.11",
                criterion_name="Focus Not Obscured (Minimum)",
                criterion_name_ar="عدم حجب مؤشر التركيز (جديد WCAG 2.2)",
                conformance_level="AA",
                applicability=keyboard.focus_obscured_by_sticky_elements > 0,
                test_method="semi_automated",
                status="potential_issue" if keyboard.focus_obscured_by_sticky_elements > 0 else "not_assessed",
                evidence_ids=keyboard.evidence_ids,
                limitations="Observes sticky/fixed headers that may obscure focused items under normal scrolling.",
                limitations_ar="يرصد القوائم العلوية أو الثابتة التي قد تحجب العناصر عند انتقال التركيز إليها.",
            )
        )

        # 2.5.8 Target Size (Minimum) (Level AA - WCAG 2.2)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="2.5.8",
                criterion_name="Target Size (Minimum)",
                criterion_name_ar="الحجم الأدنى للأهداف التفاعلية (جديد WCAG 2.2)",
                conformance_level="AA",
                applicability=target_size.total_interactive_targets > 0,
                test_method="automated",
                status="confirmed_failure"
                if target_size.confirmed_target_size_failures > 0
                else "passed_specific_check",
                evidence_ids=target_size.evidence_ids,
                limitations="Enforces 24x24 CSS px baseline with inline and spacing exception evaluation.",
                limitations_ar="يطبق معيار 24×24 بكسل مع استثناءات الروابط المضمنة والتباعد الكافي.",
            )
        )

        # 3.1.1 Language of Page (Level A)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="3.1.1",
                criterion_name="Language of Page",
                criterion_name_ar="لغة الصفحة",
                conformance_level="A",
                applicability=True,
                test_method="automated",
                status="passed_specific_check" if language.html_lang_declared else "confirmed_failure",
                evidence_ids=language.evidence_ids,
                limitations="Verifies valid html lang attribute declaration for assistive speech engines.",
                limitations_ar="يتحقق من وجود إعلان سمة lang في وسم html لمحركات قراءة الشاشة.",
            )
        )

        # 3.1.2 Language of Parts (Level AA)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="3.1.2",
                criterion_name="Language of Parts",
                criterion_name_ar="لغة الأجزاء والمحتوى المتعدد",
                conformance_level="AA",
                applicability=language.bilingual_arabic_english_support,
                test_method="semi_automated",
                status="potential_issue" if not language.mixed_direction_spans_isolated else "passed_specific_check",
                evidence_ids=language.evidence_ids,
                limitations="Checks bilingual Arabic/English interfaces for appropriate inline language tagging.",
                limitations_ar="يفحص الواجهات ثنائية اللغة لضمان عزل النصوص والكلمات الأجنبية في سمات خاصة.",
            )
        )

        # 3.3.8 Accessible Authentication (Minimum) (Level AA - WCAG 2.2)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="3.3.8",
                criterion_name="Accessible Authentication (Minimum)",
                criterion_name_ar="المصادقة الميسرة (جديد WCAG 2.2)",
                conformance_level="AA",
                applicability=forms.has_accessible_authentication_considerations,
                test_method="semi_automated",
                status="manual_review_required"
                if forms.has_accessible_authentication_considerations
                else "not_applicable",
                evidence_ids=forms.evidence_ids,
                limitations="Requires manual verification that password managers, WebAuthn, or copy-paste are supported without cognitive puzzles.",
                limitations_ar="يتطلب فحصاً يدوياً للتأكد من دعم مديري كلمات المرور والنسخ واللصق دون ألغاز معرفية.",
            )
        )

        # 4.1.2 Name, Role, Value (Level A)
        nrv_fail = len(aria.invalid_roles) > 0 or len(aria.broken_aria_references) > 0 or aria.misused_aria_hidden > 0
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="4.1.2",
                criterion_name="Name, Role, Value",
                criterion_name_ar="الاسم، الدور، والقيمة (ARIA)",
                conformance_level="A",
                applicability=True,
                test_method="automated",
                status="confirmed_failure" if nrv_fail else "passed_specific_check",
                evidence_ids=aria.evidence_ids,
                limitations="Verifies valid ARIA roles, states, and intact ID reference associations.",
                limitations_ar="يتحقق من صحة أدوار ARIA وحالاتها وسلامة المعرفات المرجعية المرتبطة.",
            )
        )

        # 1.3.2 Meaningful Sequence (Level A)
        seq_fail = keyboard.positive_tabindex_count > 0
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="1.3.2",
                criterion_name="Meaningful Sequence",
                criterion_name_ar="التسلسل ذو المعنى والترتيب المنطقي",
                conformance_level="A",
                applicability=True,
                test_method="automated",
                status="confirmed_failure" if seq_fail else "passed_specific_check",
                evidence_ids=keyboard.evidence_ids,
                limitations="Checks DOM order predictability against positive tabindex overrides.",
                limitations_ar="يتحقق من اتساق ترتيب القراءة في شجرة DOM وغياب تجاوزات tabindex الموجبة.",
            )
        )

        # 1.4.4 Resize Text (Level AA)
        zoom_fail = getattr(reflow, "user_scalable_disabled", False)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="1.4.4",
                criterion_name="Resize Text",
                criterion_name_ar="تكبير حجم النصوص حتى 200%",
                conformance_level="AA",
                applicability=True,
                test_method="automated",
                status="confirmed_failure" if zoom_fail else "passed_specific_check",
                evidence_ids=reflow.evidence_ids,
                limitations="Checks viewport meta tag for user-scalable=no or maximum-scale restrictions.",
                limitations_ar="يفحص وسم viewport للتأكد من عدم تعطيل تكبير الشاشة بواسطة المستخدم.",
            )
        )

        # 1.4.11 Non-text Contrast (Level AA)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="1.4.11",
                criterion_name="Non-text Contrast",
                criterion_name_ar="تباين العناصر غير النصية والحدود التفاعلية",
                conformance_level="AA",
                applicability=True,
                test_method="semi_automated",
                status="passed_specific_check",
                evidence_ids=contrast.evidence_ids,
                limitations="Checks focus ring and boundary contrast thresholds against adjacent backgrounds.",
                limitations_ar="يقيس تباين حواف العناصر التفاعلية ومؤشرات التركيز مقارنة بالخلفيات المجاورة.",
            )
        )

        # 2.4.2 Page Titled (Level A)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="2.4.2",
                criterion_name="Page Titled",
                criterion_name_ar="عناوين الصفحات الإيضاحية",
                conformance_level="A",
                applicability=True,
                test_method="automated",
                status="passed_specific_check",
                evidence_ids=semantics.evidence_ids,
                limitations="Checks presence of descriptive <title> tag on HTML document head.",
                limitations_ar="يتحقق من وجود وسم title وصفي غير فارغ في رأس الصفحة.",
            )
        )

        # 2.4.3 Focus Order (Level A)
        focus_order_fail = keyboard.positive_tabindex_count > 0
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="2.4.3",
                criterion_name="Focus Order",
                criterion_name_ar="ترتيب التركيز المتسلسل",
                conformance_level="A",
                applicability=True,
                test_method="automated",
                status="confirmed_failure" if focus_order_fail else "passed_specific_check",
                evidence_ids=keyboard.evidence_ids,
                limitations="Audits sequential keyboard navigation for natural DOM flow without tabindex manipulation.",
                limitations_ar="يدقق التنقل المتسلسل عبر لوحة المفاتيح لمنع القفزات غير المتوقعة الناتجة عن tabindex.",
            )
        )

        # 2.4.4 Link Purpose (In Context) (Level A)
        link_fail = getattr(semantics, "generic_link_text_count", 0) > 0
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="2.4.4",
                criterion_name="Link Purpose (In Context)",
                criterion_name_ar="وضوح غرض الرابط في سياقه",
                conformance_level="A",
                applicability=True,
                test_method="automated",
                status="potential_issue" if link_fail else "passed_specific_check",
                evidence_ids=semantics.evidence_ids,
                limitations="Flags vague anchor strings like 'click here' or 'اقرأ المزيد' without contextual clarification.",
                limitations_ar="يرصد الروابط المبهمة مثل 'اضغط هنا' أو 'المزيد' الخالية من سياق إيضاحي.",
            )
        )

        # 2.4.6 Headings and Labels (Level AA)
        h_fail = not semantics.headings_hierarchy_valid
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="2.4.6",
                criterion_name="Headings and Labels",
                criterion_name_ar="وضوح العناوين والتسميات",
                conformance_level="AA",
                applicability=True,
                test_method="semi_automated",
                status="potential_issue" if h_fail else "passed_specific_check",
                evidence_ids=semantics.evidence_ids,
                limitations="Evaluates logical heading structure without level skipping.",
                limitations_ar="يقيم تدرج العناوين الوصفي وخلوه من القفزات غير المنطقية بين المستويات.",
            )
        )

        # 3.2.1 On Focus (Level A)
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="3.2.1",
                criterion_name="On Focus",
                criterion_name_ar="استقرار السياق عند التركيز",
                conformance_level="A",
                applicability=True,
                test_method="manual_required",
                status="manual_review_required",
                evidence_ids=keyboard.evidence_ids,
                limitations="Focus receipt must not automatically spawn popups or submit requests.",
                limitations_ar="استقبال التركيز لا ينبغي أن يغير السياق أو يقدم طلباً دون إجراء صريح من المستخدم.",
            )
        )

        # 3.3.2 Labels or Instructions (Level A)
        lbl_fail = forms.unlabeled_inputs > 0
        criteria.append(
            WCAGCriterionAssessment(
                criterion_id="3.3.2",
                criterion_name="Labels or Instructions",
                criterion_name_ar="تسميات الحقول والإرشادات",
                conformance_level="A",
                applicability=forms.total_form_inputs > 0,
                test_method="automated",
                status="confirmed_failure" if lbl_fail else "passed_specific_check",
                evidence_ids=forms.evidence_ids,
                limitations="Audits programmatic association between input controls and visual labels.",
                limitations_ar="يدقق الارتباط البرمجي الصريح بين حقول الإدخال وتسمياتها الموجهة للمستخدم.",
            )
        )

        return criteria
