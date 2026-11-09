"""Source Agent Registry and Metadata for Site DNA Strategic Intelligence."""

from typing import Any, NamedTuple


class SourceAgentMeta(NamedTuple):
    """Metadata describing a supported source analysis phase."""

    phase_id: str
    phase_number: int
    display_name: str
    display_name_ar: str
    artifact_subfolder: str
    primary_artifact_file: str
    finding_class_name: str
    category: str


SUPPORTED_SOURCE_AGENTS: dict[str, SourceAgentMeta] = {
    "visual_identity": SourceAgentMeta(
        phase_id="visual_identity",
        phase_number=4,
        display_name="Visual Identity Analyst",
        display_name_ar="محلل الهوية البصرية الذكي",
        artifact_subfolder="visual-identity",
        primary_artifact_file="analysis.json",
        finding_class_name="VisualFinding",
        category="design",
    ),
    "ux_ui": SourceAgentMeta(
        phase_id="ux_ui",
        phase_number=5,
        display_name="UX/UI Experience Analyst",
        display_name_ar="محلل تجربة وواجهة المستخدم",
        artifact_subfolder="ux-ui",
        primary_artifact_file="analysis.json",
        finding_class_name="UXFinding",
        category="ux",
    ),
    "content_marketing": SourceAgentMeta(
        phase_id="content_marketing",
        phase_number=6,
        display_name="Content & Marketing Analyst",
        display_name_ar="محلل المحتوى والتسويق الرقمي",
        artifact_subfolder="content",
        primary_artifact_file="analysis.json",
        finding_class_name="ContentFinding",
        category="content",
    ),
    "technical_seo": SourceAgentMeta(
        phase_id="technical_seo",
        phase_number=7,
        display_name="Technical SEO & Performance Analyst",
        display_name_ar="محلل SEO التقني ومؤشرات الأداء",
        artifact_subfolder="technical-seo",
        primary_artifact_file="analysis.json",
        finding_class_name="TechnicalSEOFinding",
        category="seo",
    ),
    "competitor_intelligence": SourceAgentMeta(
        phase_id="competitor_intelligence",
        phase_number=8,
        display_name="Competitor Intelligence Analyst",
        display_name_ar="محلل استخبارات المنافسين والمقارنة",
        artifact_subfolder="competitor-intelligence",
        primary_artifact_file="analysis.json",
        finding_class_name="CompetitiveFinding",
        category="market",
    ),
    "security_privacy": SourceAgentMeta(
        phase_id="security_privacy",
        phase_number=9,
        display_name="Security & Privacy Analyst",
        display_name_ar="محلل أمان الموقع والخصوصية والثقة",
        artifact_subfolder="security-privacy",
        primary_artifact_file="analysis.json",
        finding_class_name="SecurityFinding",
        category="security",
    ),
    "accessibility": SourceAgentMeta(
        phase_id="accessibility",
        phase_number=10,
        display_name="Accessibility & WCAG 2.2 Analyst",
        display_name_ar="محلل إمكانية الوصول والنفاذ الرقمي",
        artifact_subfolder="accessibility",
        primary_artifact_file="analysis.json",
        finding_class_name="AccessibilityFinding",
        category="accessibility",
    ),
}
