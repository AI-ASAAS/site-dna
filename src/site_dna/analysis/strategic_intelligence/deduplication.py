"""Finding Deduplication Engine for Site DNA Phase 11."""

import re

from site_dna.schemas.strategic_intelligence import DuplicateFindingGroup, UnifiedFinding


class FindingDeduplicator:
    """Detects and groups cross-agent overlapping or duplicate findings with false-merge safeguards."""

    @staticmethod
    def _extract_tokens(text: str) -> set[str]:
        words = re.findall(r"\w+", text.lower())
        stopwords = {
            "the",
            "and",
            "for",
            "with",
            "page",
            "site",
            "element",
            "issue",
            "found",
            "detected",
            "في",
            "من",
            "على",
            "إلى",
            "عن",
            "مع",
            "هذا",
            "هذه",
        }
        return {w for w in words if len(w) > 2 and w not in stopwords}

    def _is_duplicate_pair(self, a: UnifiedFinding, b: UnifiedFinding) -> tuple[bool, str, str, float]:
        """Check whether two findings represent the identical underlying technical problem."""
        # Must be from different phases or different findings
        if a.source_phase == b.source_phase and a.source_finding_id == b.source_finding_id:
            return False, "", "", 0.0

        # Pattern 1: Contrast detected by Visual Identity and Accessibility
        contrast_terms = {"contrast", "تباين", "luminance", "color"}
        a_title_tokens = self._extract_tokens(a.title + " " + a.category)
        b_title_tokens = self._extract_tokens(b.title + " " + b.category)

        if a_title_tokens & contrast_terms and b_title_tokens & contrast_terms:
            if {a.source_phase, b.source_phase} <= {"visual_identity", "accessibility", "ux_ui"}:
                # If page matches or general design system
                if not a.page_url or not b.page_url or a.page_url == b.page_url:
                    return (
                        True,
                        "Low color contrast identified by both Visual Identity and Accessibility engines.",
                        "تم رصد ضعف التباين اللوني عبر محرك الهوية البصرية ومحرك النفاذ الرقمي معاً.",
                        0.95,
                    )

        # Pattern 2: Form labels missing detected by UX and Accessibility
        label_terms = {"label", "form", "input", "تسمية", "حقل", "نموذج"}
        if a_title_tokens & label_terms and b_title_tokens & label_terms:
            if {a.source_phase, b.source_phase} <= {"ux_ui", "accessibility"}:
                if not a.page_url or not b.page_url or a.page_url == b.page_url:
                    return (
                        True,
                        "Missing programmatic or visible form input labels reported by UX and Accessibility.",
                        "غياب تسميات الحقول البرمجية أو الظاهرة رصدته تحليلات تجربة المستخدم والنفاذ الرقمي.",
                        0.92,
                    )

        # Pattern 3: Broken navigation / 404 links detected by UX and Technical SEO
        nav_terms = {"broken", "navigation", "link", "404", "توجيه", "رابط", "معطل"}
        if a_title_tokens & nav_terms and b_title_tokens & nav_terms:
            if {a.source_phase, b.source_phase} <= {"ux_ui", "technical_seo"}:
                if not a.page_url or not b.page_url or a.page_url == b.page_url:
                    return (
                        True,
                        "Broken internal navigation or invalid links identified across UX and Technical SEO.",
                        "روابط داخلية معطلة أو مسارات تنقل مكسورة مشتركة بين تجربة المستخدم وSEO التقني.",
                        0.90,
                    )

        # Pattern 4: Oversized uncompressed media identified by Visual and Performance SEO
        media_terms = {"image", "media", "lcp", "performance", "صورة", "وسائط", "أداء", "حجم"}
        if a_title_tokens & media_terms and b_title_tokens & media_terms:
            if {a.source_phase, b.source_phase} <= {"visual_identity", "technical_seo", "ux_ui"}:
                if not a.page_url or not b.page_url or a.page_url == b.page_url:
                    return (
                        True,
                        "Unoptimized heavy imagery impacting visual rendering and performance metrics.",
                        "صور غير محسنة أو ثقيلة تؤثر سلباً على العرض البصري ومؤشرات الأداء وسرعة التحميل.",
                        0.88,
                    )

        # Pattern 5: Vague CTA wording between UX and Content
        cta_terms = {"cta", "call to action", "زر", "دعوة", "wording", "نص الزر"}
        if a_title_tokens & cta_terms and b_title_tokens & cta_terms:
            if {a.source_phase, b.source_phase} <= {"ux_ui", "content_marketing"}:
                # Ensure it's not confusing accessible labelling with copywriting
                if "accessibility" not in a.category.lower() and "accessibility" not in b.category.lower():
                    return (
                        True,
                        "Vague or low-converting call-to-action wording noted by UX and Content Marketing.",
                        "عبارات الدعوة لاتخاذ إجراء (CTA) مبهمة أو ضعيفة التأثير رصدها محللو المحتوى وUX.",
                        0.85,
                    )

        # Pattern 6: Evidence ID direct overlap
        overlap_ev = set(a.evidence_ids) & set(b.evidence_ids)
        if overlap_ev and (not a.page_url or not b.page_url or a.page_url == b.page_url):
            return (
                True,
                f"Shared exact evidence IDs ({', '.join(list(overlap_ev)[:3])}) across different agents.",
                f"أدلة تقنية مشتركة متطابقة ({', '.join(list(overlap_ev)[:3])}) بين الوكلاء.",
                0.90,
            )

        return False, "", "", 0.0

    def deduplicate(self, findings: list[UnifiedFinding]) -> tuple[list[UnifiedFinding], list[DuplicateFindingGroup]]:
        """Group duplicate findings into canonical groups while keeping all individual findings intact."""
        groups: list[DuplicateFindingGroup] = []
        assigned_to_group: set[str] = set()

        for i in range(len(findings)):
            f_a = findings[i]
            if f_a.unified_finding_id in assigned_to_group:
                continue

            current_group_findings = [f_a]
            reasons_en = []
            reasons_ar = []
            group_conf = 1.0

            for j in range(i + 1, len(findings)):
                f_b = findings[j]
                if f_b.unified_finding_id in assigned_to_group:
                    continue

                is_dup, r_en, r_ar, conf = self._is_duplicate_pair(f_a, f_b)
                if is_dup:
                    current_group_findings.append(f_b)
                    assigned_to_group.add(f_b.unified_finding_id)
                    reasons_en.append(r_en)
                    if r_ar:
                        reasons_ar.append(r_ar)
                    group_conf = min(group_conf, conf)

            if len(current_group_findings) > 1:
                assigned_to_group.add(f_a.unified_finding_id)
                agents = sorted(list({f.source_agent for f in current_group_findings}))
                pages = sorted(list({f.page_url for f in current_group_findings if f.page_url}))
                all_ev = sorted(list({ev for f in current_group_findings for ev in f.evidence_ids}))

                canon_title = f_a.title
                canon_title_ar = f_a.title_ar or f_a.title

                reason_text = reasons_en[0] if reasons_en else "Shared underlying defect across multiple domains."
                reason_text_ar = reasons_ar[0] if reasons_ar else "خلل تقني مشترك مرصود عبر عدة مجالات فحص."

                group = DuplicateFindingGroup(
                    canonical_title=canon_title,
                    canonical_title_ar=canon_title_ar,
                    category=f_a.category,
                    findings=current_group_findings,
                    source_agents=agents,
                    affected_pages=pages,
                    all_evidence_ids=all_ev,
                    deduplication_reason=reason_text,
                    deduplication_reason_ar=reason_text_ar,
                    confidence=group_conf,
                )
                groups.append(group)

        return findings, groups
