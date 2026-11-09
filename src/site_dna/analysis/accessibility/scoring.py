"""Explainable Evidence-Based Accessibility Scoring Engine for Site DNA Phase 10."""

from site_dna.schemas.accessibility import (
    AccessibilityFinding,
    AccessibilityPageRecord,
    AccessibilityScore,
    ContrastAssessment,
    FormAccessibilityAssessment,
    ImagesMediaAssessment,
    KeyboardFocusAssessment,
    LanguageDirectionAssessment,
    ReflowZoomAssessment,
    SemanticAssessment,
    TargetSizeAssessment,
)

# 6 Weighted Dimensions (Sum = 100%)
WEIGHT_SEMANTICS_NAMES = 0.20
WEIGHT_KEYBOARD_FOCUS = 0.20
WEIGHT_VISUAL_CONTRAST = 0.20
WEIGHT_FORMS_INTERACTION = 0.15
WEIGHT_NAVIGATION_STRUCTURE = 0.15
WEIGHT_LANGUAGE_MEDIA = 0.10


class AccessibilityScoringEngine:
    """Calculates normalized accessibility posture scores based strictly on observable evidence."""

    DIMENSION_WEIGHTS = {
        "semantics_names": WEIGHT_SEMANTICS_NAMES,
        "keyboard_focus": WEIGHT_KEYBOARD_FOCUS,
        "visual_contrast": WEIGHT_VISUAL_CONTRAST,
        "forms_interaction": WEIGHT_FORMS_INTERACTION,
        "navigation_structure": WEIGHT_NAVIGATION_STRUCTURE,
        "language_media": WEIGHT_LANGUAGE_MEDIA,
    }

    def calculate_scores(
        self,
        pages: list[AccessibilityPageRecord],
        semantics: SemanticAssessment,
        images_media: ImagesMediaAssessment,
        keyboard: KeyboardFocusAssessment,
        contrast: ContrastAssessment,
        reflow: ReflowZoomAssessment,
        target_size: TargetSizeAssessment,
        forms: FormAccessibilityAssessment,
        language: LanguageDirectionAssessment,
        findings: list[AccessibilityFinding],
    ) -> AccessibilityScore:
        """Calculate weighted dimension scores and overall evidence assessment score."""
        if not pages:
            return AccessibilityScore(
                overall_score=None,
                semantics_names_score=0.0,
                keyboard_focus_score=0.0,
                visual_contrast_score=0.0,
                forms_interaction_score=0.0,
                navigation_structure_score=0.0,
                language_media_score=0.0,
                evidence_coverage_percentage=0.0,
                score_label="Insufficient Evidence",
                score_label_ar="أدلة غير كافية",
            )

        # 1. Semantics & Accessible Names (20%)
        sem_score = 100.0
        if not semantics.has_main_landmark:
            sem_score -= 25.0
        if not semantics.headings_hierarchy_valid:
            sem_score -= 15.0
        if semantics.unheaded_tables_count > 0:
            sem_score -= min(20.0, semantics.unheaded_tables_count * 5.0)
        sem_score = max(0.0, min(100.0, sem_score))

        # 2. Keyboard & Focus (20%)
        kb_score = 100.0
        if not keyboard.focus_indicators_visible:
            kb_score -= 35.0
        if not keyboard.tab_order_sequential:
            kb_score -= 20.0
        if not keyboard.skip_link_present:
            kb_score -= 15.0
        if keyboard.focus_obscured_by_sticky_elements > 0:
            kb_score -= min(15.0, keyboard.focus_obscured_by_sticky_elements * 5.0)
        kb_score = max(0.0, min(100.0, kb_score))

        # 3. Visual & Contrast (20%)
        vis_score = 100.0
        total_contrast_violations = contrast.contrast_violations_aa_normal + contrast.contrast_violations_aa_large
        if total_contrast_violations > 0:
            vis_score -= min(40.0, total_contrast_violations * 10.0)
        if reflow.horizontal_overflow_at_320px:
            vis_score -= 25.0
        if target_size.confirmed_target_size_failures > 0:
            vis_score -= min(20.0, target_size.confirmed_target_size_failures * 5.0)
        vis_score = max(0.0, min(100.0, vis_score))

        # 4. Forms & Interaction (15%)
        forms_score = 100.0
        if forms.total_form_inputs > 0:
            unlabeled_ratio = forms.unlabeled_inputs / forms.total_form_inputs
            forms_score -= unlabeled_ratio * 50.0
            if forms.unlabeled_inputs > 0:
                forms_score -= 20.0
        forms_score = max(0.0, min(100.0, forms_score))

        # 5. Navigation & Content Structure (15%)
        nav_score = 100.0
        if semantics.nav_landmarks_count == 0:
            nav_score -= 25.0
        if not keyboard.skip_link_present:
            nav_score -= 15.0
        nav_score = max(0.0, min(100.0, nav_score))

        # 6. Language, Media & Inclusion (10%)
        lang_score = 100.0
        if not language.html_lang_declared:
            lang_score -= 35.0
        if images_media.missing_alt_count > 0:
            lang_score -= min(30.0, images_media.missing_alt_count * 10.0)
        if images_media.functional_icon_buttons_without_name > 0:
            lang_score -= min(25.0, images_media.functional_icon_buttons_without_name * 10.0)
        if not language.mixed_direction_spans_isolated:
            lang_score -= 15.0
        lang_score = max(0.0, min(100.0, lang_score))

        # Composite Weighted Score
        composite = (
            WEIGHT_SEMANTICS_NAMES * sem_score
            + WEIGHT_KEYBOARD_FOCUS * kb_score
            + WEIGHT_VISUAL_CONTRAST * vis_score
            + WEIGHT_FORMS_INTERACTION * forms_score
            + WEIGHT_NAVIGATION_STRUCTURE * nav_score
            + WEIGHT_LANGUAGE_MEDIA * lang_score
        )
        overall = round(max(0.0, min(100.0, composite)), 1)

        # Label thresholds
        if overall >= 90:
            label = "Excellent"
            label_ar = "ممتاز"
        elif overall >= 75:
            label = "Good"
            label_ar = "جيد"
        elif overall >= 55:
            label = "Moderate"
            label_ar = "متوسط"
        elif overall >= 35:
            label = "Poor"
            label_ar = "ضعيف"
        else:
            label = "Critical Barriers"
            label_ar = "حرج / حواجز جسيمة"

        return AccessibilityScore(
            overall_score=overall,
            semantics_names_score=round(sem_score, 1),
            keyboard_focus_score=round(kb_score, 1),
            visual_contrast_score=round(vis_score, 1),
            forms_interaction_score=round(forms_score, 1),
            navigation_structure_score=round(nav_score, 1),
            language_media_score=round(lang_score, 1),
            evidence_coverage_percentage=100.0,
            score_label=label,
            score_label_ar=label_ar,
        )
