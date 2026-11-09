"""Root-Cause Candidate Synthesis Engine for Site DNA Phase 11."""

from collections import defaultdict
from typing import Any

from site_dna.schemas.strategic_intelligence import RootCauseCandidate, UnifiedFinding


class RootCauseAnalyzer:
    """Hypothesizes underlying structural causes from recurring cross-page patterns without claiming private code access."""

    def analyze_root_causes(self, findings: list[UnifiedFinding]) -> list[RootCauseCandidate]:
        """Group recurring defects across pages into plausible candidate root causes."""
        candidates: list[RootCauseCandidate] = []

        # 1. Pattern: Missing labels across multiple forms/pages
        label_findings = [
            f
            for f in findings
            if any(term in (f.title + f.description).lower() for term in ("label", "تسمية", "input label"))
        ]
        if len(label_findings) >= 2 or len({f.page_url for f in label_findings if f.page_url}) >= 2:
            pages = sorted(list({f.page_url for f in label_findings if f.page_url}))
            ev_ids = sorted(list({ev for f in label_findings for ev in f.evidence_ids}))
            candidates.append(
                RootCauseCandidate(
                    title="Shared Input Component Lacking Accessible Label Association",
                    title_ar="مكون إدخال مشترك يفتقر إلى الربط البرمجي السليم للتسميات",
                    description="Multiple pages exhibit unlabeled inputs with identical patterns, indicating a reusable form control or template that omits explicit for/id or aria-label bindings.",
                    description_ar="تكرار غياب التسميات عبر عدة صفحات ونماذج يشير إلى استخدام مكون إدخال موحد يفتقر إلى ربط سمات for/id أو aria-label بشكل افتراضي.",
                    confidence="strong_candidate",
                    related_finding_ids=[f.unified_finding_id for f in label_findings],
                    affected_pages=pages,
                    shared_pattern="Repeated missing <label for> association across distinct form instances.",
                    evidence_ids=ev_ids,
                )
            )

        # 2. Pattern: Missing security headers across all responses
        sec_header_findings = [
            f
            for f in findings
            if f.source_phase == "security_privacy" and "header" in (f.title + f.category).lower()
        ]
        if len(sec_header_findings) >= 3:
            pages = sorted(list({f.page_url for f in sec_header_findings if f.page_url}))
            ev_ids = sorted(list({ev for f in sec_header_findings for ev in f.evidence_ids}))
            candidates.append(
                RootCauseCandidate(
                    title="Ingress Web Server / CDN Lacking Hardened Security Header Configuration",
                    title_ar="خادم الويب أو شبكة CDN تفتقر إلى ضبط ترويسات الحماية المركزية",
                    description="Consistent absence of fundamental headers (HSTS, CSP, X-Content-Type-Options) across multiple routes indicates a missing global configuration at the reverse proxy or CDN edge.",
                    description_ar="غياب ترويسات الأمان الأساسية عبر مختلف المسارات يؤكد عدم تفعيلها مركزياً على مستوى خادم الويب (Nginx/Apache) أو وسيط CDN.",
                    confidence="confirmed_by_evidence",
                    related_finding_ids=[f.unified_finding_id for f in sec_header_findings],
                    affected_pages=pages,
                    shared_pattern="Zero security headers injected at reverse-proxy or edge layer.",
                    evidence_ids=ev_ids,
                )
            )

        # 3. Pattern: Mobile horizontal overflow across responsive views
        overflow_findings = [
            f
            for f in findings
            if any(term in (f.title + f.description).lower() for term in ("overflow", "320px", "horizontal scroll"))
        ]
        if len(overflow_findings) >= 1:
            pages = sorted(list({f.page_url for f in overflow_findings if f.page_url}))
            ev_ids = sorted(list({ev for f in overflow_findings for ev in f.evidence_ids}))
            candidates.append(
                RootCauseCandidate(
                    title="Global Unconstrained Container Width or Fixed Pixel Viewport CSS",
                    title_ar="قاعدة CSS عامة أو حاوية ذات عرض ثابت تسبب فيضاناً أفقياً في الجوال",
                    description="Horizontal scrolling triggered at narrow viewports indicates fixed pixel width constraints (e.g. width: 1200px) or unconstrained elements failing to respect 100vw bounds.",
                    description_ar="ظهور شريط التمرير الأفقي في الشاشات الضيقة يعود لقواعد CSS ذات قياسات بكسل ثابتة تمنع الحاوية من الانكماش المرن.",
                    confidence="strong_candidate",
                    related_finding_ids=[f.unified_finding_id for f in overflow_findings],
                    affected_pages=pages,
                    shared_pattern="Fixed pixel containers or unconstrained tables overflowing 320px viewport.",
                    evidence_ids=ev_ids,
                )
            )

        # 4. Pattern: Contrast issues across diverse components
        contrast_findings = [
            f
            for f in findings
            if any(term in (f.title + f.description).lower() for term in ("contrast", "luminance", "تباين"))
        ]
        if len(contrast_findings) >= 2:
            pages = sorted(list({f.page_url for f in contrast_findings if f.page_url}))
            ev_ids = sorted(list({ev for f in contrast_findings for ev in f.evidence_ids}))
            candidates.append(
                RootCauseCandidate(
                    title="Design System Color Palette Incompliance with WCAG Luminance Ratios",
                    title_ar="لوحة ألوان دليل الهوية (Design System) لا تحقق نسب التباين المطلوبة",
                    description="Multiple low-contrast text and UI elements indicate brand secondary/accent color tokens that inherently fail the 4.5:1 ratio against light or dark canvas backgrounds.",
                    description_ar="تكرار عوائق التباين في أزرار ونصوص مختلفة يدل على أن درجات الألوان المعتمدة في دليل التصميم الأساسي تفتقر إلى التباين الكافي.",
                    confidence="possible_candidate",
                    related_finding_ids=[f.unified_finding_id for f in contrast_findings],
                    affected_pages=pages,
                    shared_pattern="Muted text and secondary button colors failing 4.5:1 luminance ratio.",
                    evidence_ids=ev_ids,
                )
            )

        return candidates
