"""Verification Planner for Site DNA Phase 11."""

from site_dna.schemas.strategic_intelligence import RoadmapAction, VerificationPlan


class VerificationPlanner:
    """Constructs objective verification plans for every roadmap action."""

    def build_verification_plans(self, actions: list[RoadmapAction]) -> list[VerificationPlan]:
        """Generate test plans for verifying completed remediation actions."""
        plans: list[VerificationPlan] = []

        for a in actions:
            method = "automated_retest"
            domain = a.category.lower()
            steps = []

            if "security" in domain or "header" in a.title.lower():
                method = "http_headers_inspection"
                steps = [
                    "Inspect live HTTP response headers using curl or browser network monitor.",
                    "Verify exact presence and valid syntax of configured security header directives.",
                    "Confirm absence of regressions or unintended origin blocks.",
                ]
            elif "accessibility" in domain or "label" in a.title.lower() or "contrast" in a.title.lower():
                method = "accessibility_dom_and_contrast_check"
                steps = [
                    "Inspect DOM element attributes (for/id, aria-label, role).",
                    "Calculate rendered foreground-to-background color luminance contrast ratio.",
                    "Verify focus visibility and keyboard tab sequence via assistive technology testing.",
                ]
            elif "seo" in domain or "link" in a.title.lower():
                method = "crawler_metadata_verification"
                steps = [
                    "Fetch target page with browser user-agent.",
                    "Parse HTML <head> for canonical link, title, meta description, and robots directives.",
                    "Verify HTTP status code returns 200 without redirect loops.",
                ]
            elif "content" in domain or "copy" in a.title.lower() or "cta" in a.title.lower():
                method = "editorial_and_brand_review"
                steps = [
                    "Review revised copy against verified company facts and brand voice guidelines.",
                    "Confirm call-to-action text is concise, direct, and unambiguous.",
                    "Check Arabic typography and bidirectional text isolation.",
                ]
            else:
                method = "browser_render_validation"
                steps = [
                    "Render page in desktop and mobile viewports.",
                    "Confirm responsive layout stability without horizontal overflow at 320px.",
                    "Verify interactive elements meet minimum 24x24px target size requirements.",
                ]

            plans.append(
                VerificationPlan(
                    action_id=a.action_id,
                    domain=domain,
                    method=method,
                    steps=steps,
                    state="ready_for_verification" if a.status == "completed_unverified" else "not_scheduled",
                    verification_evidence_ids=a.evidence_ids,
                )
            )

        return plans
