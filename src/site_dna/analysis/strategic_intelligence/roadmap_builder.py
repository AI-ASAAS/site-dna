"""Roadmap Builder for Site DNA Phase 11."""

from site_dna.schemas.strategic_intelligence import RoadmapAction, RoadmapWave


class RoadmapBuilder:
    """Organizes prioritized backlog actions into 4 practical execution waves without invented calendar commitments."""

    WAVE_DEFINITIONS = [
        {
            "wave_number": 1,
            "name": "Critical Fixes & Immediate Blockers",
            "name_ar": "الإصلاحات العاجلة وسد العوائق الحرجة",
            "description": "Urgent P0 blockers, critical security vulnerabilities, transport configuration, and primary conversion blockers.",
            "description_ar": "معالجة الثغرات الأمنية الحرجة، وترويسات الحماية الأساسية، وإزالة العوائق التي تمنع المستخدم من استكمال المهام الأساسية.",
        },
        {
            "wave_number": 2,
            "name": "Foundational Structural Improvements",
            "name_ar": "التحسينات الهيكلية والبنية التحتية المشتركة",
            "description": "Shared component updates, design system contrast remediation, semantic form controls, and media delivery pipelines.",
            "description_ar": "تحديث المكونات المشتركة، وتصحيح لوحة ألوان دليل الهوية، ونماذج الإدخال الميسرة، وضغط وتحسين استدعاء الصور والوسائط.",
        },
        {
            "wave_number": 3,
            "name": "Experience & Content Refinements",
            "name_ar": "تحسين تجربة الاستخدام وإثراء المحتوى",
            "description": "UX interaction streamlining, value proposition copywriting sharpening, navigation wayfinding, and search discoverability.",
            "description_ar": "تبسيط تدفقات التفاعل، وصقل صياغة القيمة المقترحة والأزرار المحفزة، وتحسين بنية العناوين والروابط الداخلية لمحركات البحث.",
        },
        {
            "wave_number": 4,
            "name": "Optimization, Experiments & Verification",
            "name_ar": "التحسين المتقدم والتجارب والتحقق المستمر",
            "description": "Follow-up metric measurements, Core Web Vitals micro-optimizations, structured data enhancements, and minor polish.",
            "description_ar": "إعادة القياس الدوري لمؤشرات الأداء (Core Web Vitals)، والبيانات المنظمة المتقدمة، وضبط اللمسات الجمالية الطفيفة.",
        },
    ]

    def build_waves(self, actions: list[RoadmapAction]) -> list[RoadmapWave]:
        """Group sequenced actions into the 4 standard execution waves."""
        waves: list[RoadmapWave] = []

        for defn in self.WAVE_DEFINITIONS:
            w_num = defn["wave_number"]
            w_actions = [a for a in actions if a.wave_number == w_num]

            waves.append(
                RoadmapWave(
                    wave_number=w_num,
                    name=defn["name"],
                    name_ar=defn["name_ar"],
                    description=defn["description"],
                    description_ar=defn["description_ar"],
                    actions=w_actions,
                    action_count=len(w_actions),
                )
            )

        return waves
