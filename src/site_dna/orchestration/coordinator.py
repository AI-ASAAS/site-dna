"""Site DNA Analysis Coordinator & Execution Orchestrator."""

import asyncio
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import HTTPException, status

from site_dna.analysis.content_marketing.service import ContentMarketingAnalysisService
from site_dna.analysis.technical_seo.service import TechnicalSEOAnalysisService
from site_dna.analysis.ux_ui.service import UXAnalysisService
from site_dna.analysis.visual_identity.service import VisualIdentityAnalysisService
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.discovery.service import WebsiteDiscoveryService
from site_dna.schemas.content_marketing import ContentAnalysisRequest
from site_dna.schemas.discovery import CrawlRequest, CrawlResult
from site_dna.schemas.runs import (
    AgentRegistryItem,
    DashboardSummary,
    RunEvent,
    RunRecord,
    RunSubmissionRequest,
    StageExecutionRecord,
)
from site_dna.schemas.technical_seo import TechnicalSEOAnalysisRequest
from site_dna.schemas.ux_ui import UXAnalysisRequest
from site_dna.schemas.visual import VisualCaptureResult
from site_dna.schemas.visual_identity import VisualIdentityAnalysisRequest
from site_dna.visual.service import VisualCollectionService

logger = get_logger("orchestration.coordinator")

AGENT_REGISTRY: list[AgentRegistryItem] = [
    AgentRegistryItem(
        id="phase_01_core",
        phase=1,
        name="Foundation & Core Infrastructure",
        name_ar="البنية التحتية والواجهات الأساسية",
        description="Configuration, logging, resilience, health checks, and API foundations.",
        description_ar="إدارة الإعدادات، التسجيل، عوازل الأمان، والواجهات البرمجية الأساسية.",
        icon="cpu",
        category="infrastructure",
        implementation_status="implemented",
        runtime_availability="ready",
        can_execute=False,
        requires_visual=False,
        dependencies=[],
        output_types=["config", "health"],
        display_order=1,
    ),
    AgentRegistryItem(
        id="discovery",
        phase=2,
        name="Website Discovery & Crawling",
        name_ar="الاستكشاف والزحف الذكي للروابط",
        description="Secure multi-page crawling, robots.txt, sitemaps, and raw HTML evidence collection.",
        description_ar="الزحف الآمن لمسارات الموقع، فحص robots.txt و sitemap، وجمع أدلة HTML الأولية.",
        icon="globe",
        category="discovery",
        implementation_status="implemented",
        runtime_availability="ready",
        can_execute=True,
        requires_visual=False,
        dependencies=[],
        output_types=["crawl.json", "evidence"],
        display_order=2,
    ),
    AgentRegistryItem(
        id="visual_capture",
        phase=3,
        name="Browser Rendering & Visual Evidence",
        name_ar="التصيير المتصفحي والأدلة البصرية",
        description="Playwright Chromium rendering, desktop/mobile screenshots, CSS, DOM and layout extraction.",
        description_ar="التقاط لقطات الشاشة للجوال وسطح المكتب واستخراج خصائص CSS وشجرة DOM.",
        icon="camera",
        category="visual",
        implementation_status="implemented",
        runtime_availability="ready",
        can_execute=True,
        requires_visual=False,
        dependencies=["discovery"],
        output_types=["manifest.json", "screenshots", "dom_elements"],
        display_order=3,
    ),
    AgentRegistryItem(
        id="visual_identity",
        phase=4,
        name="AI Visual Identity Analyst",
        name_ar="محلل الهوية البصرية الذكي",
        description="Multimodal visual identity audit: typography, color harmony, layout structure, and brand coherence.",
        description_ar="تدقيق الهوية البصرية وتناغم الألوان والخطوط الطباعية وتماسك الواجهات.",
        icon="palette",
        category="analysis",
        implementation_status="implemented",
        runtime_availability="ready",
        can_execute=True,
        requires_visual=True,
        dependencies=["discovery", "visual_capture"],
        output_types=["report.md", "analysis.json", "visual_scores"],
        display_order=4,
    ),
    AgentRegistryItem(
        id="ux_ui",
        phase=5,
        name="AI UX/UI & Usability Analyst",
        name_ar="محلل تجربة وواجهة المستخدم",
        description="Usability audit: navigation clarity, accessibility contrast, CTA prominence, form ergonomics, and mobile layout.",
        description_ar="تدقيق قابلية الاستخدام وسهولة التنقل، تباين الألوان، أزرار الإجراء، ونماذج الإدخال.",
        icon="layout",
        category="analysis",
        implementation_status="implemented",
        runtime_availability="ready",
        can_execute=True,
        requires_visual=True,
        dependencies=["discovery", "visual_capture"],
        output_types=["report.md", "analysis.json", "ux_scores"],
        display_order=5,
    ),
    AgentRegistryItem(
        id="content_marketing",
        phase=6,
        name="Content & Marketing Intelligence",
        name_ar="ذكاء المحتوى والتسويق الرقمي",
        description="Value proposition analysis, brand tone consistency, conversion copywriting, and message clarity.",
        description_ar="تحليل القيمة المقترحة، نبرة الصوت التسويقية، نصوص التحويل، وفجوات الرسائل الترويجية.",
        icon="pen-tool",
        category="analysis",
        implementation_status="implemented",
        runtime_availability="ready",
        can_execute=True,
        requires_visual=False,
        dependencies=["discovery"],
        output_types=["report.md", "analysis.json", "content_scores"],
        display_order=6,
    ),
    AgentRegistryItem(
        id="technical_seo",
        phase=7,
        name="Technical SEO & Performance Analyst",
        name_ar="محلل SEO التقني ومؤشرات الأداء",
        description="Crawlability, canonical consistency, Core Web Vitals (LCP/CLS), structured data (JSON-LD), and JavaScript SEO.",
        description_ar="فحص إمكانية الزحف والفهرسة، الروابط المعيارية، مؤشرات الأداء، والبيانات المنظمة.",
        icon="zap",
        category="analysis",
        implementation_status="implemented",
        runtime_availability="ready",
        can_execute=True,
        requires_visual=False,
        dependencies=["discovery"],
        output_types=["report.md", "analysis.json", "seo_scores"],
        display_order=7,
    ),
    AgentRegistryItem(
        id="competitor_intelligence",
        phase=8,
        name="Competitor Intelligence & Benchmark",
        name_ar="استخبارات المنافسين والمقارنة المعيارية",
        description="Cross-competitor positioning, market gap discovery, feature matrix comparison, and strategic benchmarking.",
        description_ar="مقارنة معيارية ذكية متعددة المواقع، مصفوفة الخصائص، مقارنة التسعير، وكشف الفجوات والفرص الاستراتيجية.",
        icon="trending-up",
        category="strategic",
        implementation_status="implemented",
        runtime_availability="ready",
        can_execute=True,
        requires_visual=True,
        dependencies=["discovery"],
        output_types=["report.md", "analysis.json", "matrix.json", "competitor_scores"],
        display_order=8,
    ),
    AgentRegistryItem(
        id="security_privacy",
        phase=9,
        name="Security, Privacy & Trust Intelligence",
        name_ar="أمان الموقع والخصوصية والثقة الرقمية",
        description="Passive security posture audit: HTTPS transport, security headers, cookie attributes, CSP, and privacy signals.",
        description_ar="فحص سلبي للوضع الأمني: أمان HTTPS وترويسات الحماية، ملفات الارتباط، سياسة CSP، ومؤشرات الخصوصية.",
        icon="shield-check",
        category="security",
        implementation_status="implemented",
        runtime_availability="ready",
        can_execute=True,
        requires_visual=False,
        dependencies=["discovery"],
        output_types=["report.md", "analysis.json", "security_scores"],
        display_order=9,
    ),
    AgentRegistryItem(
        id="accessibility",
        phase=10,
        name="Web Accessibility & WCAG 2.2 Intelligence",
        name_ar="إمكانية الوصول الرقمي ومعايير WCAG 2.2",
        description="Evidence-based accessibility audit, WCAG 2.2 Level A/AA mapping, keyboard focus, color contrast, and inclusive UX.",
        description_ar="تدقيق نفاذ رقمي قائم على الأدلة، ربط بمعايير WCAG 2.2 A/AA، وفحص لوحة المفاتيح والتباين والشمولية.",
        icon="accessibility",
        category="accessibility",
        implementation_status="implemented",
        runtime_availability="ready",
        can_execute=True,
        requires_visual=False,
        dependencies=["discovery"],
        output_types=["report.md", "analysis.json", "wcag-criteria.json", "manual-review-tasks.json"],
        display_order=10,
    ),
    AgentRegistryItem(
        id="strategic_intelligence",
        phase=11,
        name="Strategic Intelligence & Action Roadmap",
        name_ar="الذكاء الاستراتيجي وخارطة العمل الموحدة",
        description="Cross-agent synthesis, multi-dimensional prioritization (P0-P3), trade-off resolution, and sequenced 4-wave roadmap.",
        description_ar="توليف نتائج كافة الوكلاء، مصفوفة أولويات خماسية الأبعاد، حل التعارضات التقنية، وخارطة عمل تنفيذية مجدولة في 4 موجات.",
        icon="compass",
        category="strategic",
        implementation_status="implemented",
        runtime_availability="ready",
        can_execute=True,
        requires_visual=False,
        dependencies=["discovery"],
        output_types=["report.md", "analysis.json", "unified-findings.json", "action-backlog.json", "roadmap.json", "conflicts.json"],
        display_order=11,
    ),
    AgentRegistryItem(
        id="executive_synthesis",
        phase=12,
        name="Final Reporting, Executive Synthesis & PDF Export",
        name_ar="التقارير النهائية والتوليف التنفيذي وتصدير PDF",
        description="Comprehensive enterprise PDF export, executive board synthesis, Thmanyah typography, and verified action backlog.",
        description_ar="تصدير تقارير PDF احترافية للإدارة والمطورين، توليف تنفيذي شامل، خط ثمانية الأصلي، وتوثيق ناصع للأدلة.",
        icon="award",
        category="reporting",
        implementation_status="implemented",
        runtime_availability="ready",
        can_execute=True,
        requires_visual=False,
        dependencies=["discovery"],
        output_types=["report.pdf", "report.md", "report-data.json", "report.html", "source-manifest.json"],
        display_order=12,
    ),
]

EXECUTABLE_STAGE_IDS = {a.id for a in AGENT_REGISTRY if a.can_execute}
PLANNED_STAGE_IDS = {a.id for a in AGENT_REGISTRY if a.implementation_status == "planned"}


class AnalysisCoordinator:
    """Manages analysis lifecycle, selective stage orchestration, persistence, and real-time streaming."""

    def __init__(self, base_dir: str = "runs", settings: Optional[Settings] = None):
        self.base_dir = Path(base_dir).resolve()
        self.settings = settings or get_settings()
        self._event_subscribers: dict[str, list[asyncio.Queue]] = {}
        self._active_runs: dict[str, RunRecord] = {}

    def list_agents(self) -> list[AgentRegistryItem]:
        """Return the comprehensive agent registry with capability statuses."""
        return AGENT_REGISTRY

    def get_agent(self, agent_id: str) -> Optional[AgentRegistryItem]:
        """Get details for a specific registered agent."""
        for a in AGENT_REGISTRY:
            if a.id == agent_id:
                return a
        return None

    def _get_run_dir(self, run_id: str) -> Path:
        """Resolve a safe run directory path."""
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "", run_id)
        return self.base_dir / clean_id

    def _save_run_state(self, run_record: RunRecord) -> None:
        """Persist execution record to disk."""
        run_dir = self._get_run_dir(run_record.run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        exec_file = run_dir / "execution.json"
        exec_file.write_text(run_record.model_dump_json(indent=2), encoding="utf-8")
        self._active_runs[run_record.run_id] = run_record

    def _emit_event(
        self,
        run_id: str,
        event_type: Any,
        message: str,
        message_ar: str,
        stage_id: Optional[str] = None,
        data: Optional[dict[str, Any]] = None,
    ) -> None:
        """Broadcast an operational event to active subscribers and log it."""
        event = RunEvent(
            event_id=f"evt-{uuid.uuid4().hex[:8]}",
            run_id=run_id,
            stage_id=stage_id,
            event_type=event_type,
            message=message,
            message_ar=message_ar,
            timestamp=datetime.now(timezone.utc).isoformat(),
            data=data or {},
        )
        logger.info("[RUN %s] %s (%s)", run_id, message, event_type)

        # Append to run events log file
        run_dir = self._get_run_dir(run_id)
        if run_dir.exists():
            events_file = run_dir / "events.jsonl"
            with events_file.open("a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")

        # Push to in-memory queues for SSE listeners
        subscribers = self._event_subscribers.get(run_id, [])
        for q in subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass

    def subscribe_events(self, run_id: str) -> asyncio.Queue:
        """Register a queue to receive real-time execution events for a run."""
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "", run_id)
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._event_subscribers.setdefault(clean_id, []).append(q)
        return q

    def unsubscribe_events(self, run_id: str, queue: asyncio.Queue) -> None:
        """Deregister an SSE listener queue."""
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "", run_id)
        if clean_id in self._event_subscribers:
            self._event_subscribers[clean_id] = [q for q in self._event_subscribers[clean_id] if q is not queue]
            if not self._event_subscribers[clean_id]:
                del self._event_subscribers[clean_id]

    def get_run(self, run_id: str) -> RunRecord:
        """Retrieve full run status and metrics, reconstructing from artifacts if needed."""
        clean_id = re.sub(r"[^a-zA-Z0-9_\-]", "", run_id)
        if clean_id in self._active_runs:
            return self._active_runs[clean_id]

        run_dir = self._get_run_dir(clean_id)
        if not run_dir.exists():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Run '{run_id}' not found.")

        exec_file = run_dir / "execution.json"
        if exec_file.exists():
            try:
                record = RunRecord.model_validate_json(exec_file.read_text(encoding="utf-8"))
                # Merge any post-run analysis stages that exist on disk
                reconstructed = self._reconstruct_run_from_disk(clean_id, run_dir)
                for st_id, st_rec in reconstructed.stages.items():
                    if st_id not in record.stages:
                        record.stages[st_id] = st_rec
                for sc_k, sc_v in reconstructed.scores.items():
                    if sc_k not in record.scores:
                        record.scores[sc_k] = sc_v
                self._active_runs[clean_id] = record
                return record
            except Exception as exc:
                logger.warning("Failed parsing execution.json for run %s: %s", clean_id, exc)

        # Fallback: Reconstruct run record from existing artifacts
        return self._reconstruct_run_from_disk(clean_id, run_dir)

    def _reconstruct_run_from_disk(self, run_id: str, run_dir: Path) -> RunRecord:
        """Inspect directory structure and rebuild a complete RunRecord."""
        crawl_file = run_dir / "crawl.json"
        target_url = "https://unknown.com"
        created_at = datetime.fromtimestamp(run_dir.stat().st_ctime, tz=timezone.utc).isoformat()
        canonical_origin = None

        if crawl_file.exists():
            try:
                cdata = json.loads(crawl_file.read_text(encoding="utf-8"))
                target_url = cdata.get("website_info", {}).get("initial_url", target_url)
                canonical_origin = cdata.get("website_info", {}).get("canonical_origin")
            except Exception:
                pass

        stages: dict[str, StageExecutionRecord] = {}
        scores: dict[str, float] = {}
        total_findings = 0
        total_recommendations = 0

        # Check discovery
        if crawl_file.exists():
            stages["discovery"] = StageExecutionRecord(
                stage_id="discovery",
                name="Website Discovery",
                name_ar="الاستكشاف والزحف",
                status="completed",
                output_path=str(crawl_file),
            )

        # Check visual capture
        visual_dir = run_dir / "visual"
        visual_run_id = None
        if visual_dir.exists():
            vis_runs = [d for d in visual_dir.iterdir() if d.is_dir()]
            if vis_runs:
                first_vis = vis_runs[0]
                visual_run_id = first_vis.name
                stages["visual_capture"] = StageExecutionRecord(
                    stage_id="visual_capture",
                    name="Visual Evidence",
                    name_ar="الأدلة البصرية",
                    status="completed",
                    output_path=str(first_vis / "manifest.json"),
                )

        # Check visual identity
        vi_candidates = list(run_dir.glob("visual/*/analysis/visual-identity/*")) + list(
            run_dir.glob("analysis/visual-identity/*")
        )
        if vi_candidates:
            latest_vi = vi_candidates[-1]
            analysis_json = latest_vi / "analysis.json"
            score = None
            f_count = 0
            r_count = 0
            if analysis_json.exists():
                try:
                    data = json.loads(analysis_json.read_text(encoding="utf-8"))
                    score = data.get("overall_score")
                    f_count = len(data.get("findings", []))
                    r_count = len(data.get("recommendations", []))
                except Exception:
                    pass
            stages["visual_identity"] = StageExecutionRecord(
                stage_id="visual_identity",
                name="Visual Identity",
                name_ar="الهوية البصرية",
                status="completed" if score is not None else "partial",
                score=score,
                findings_count=f_count,
                recommendations_count=r_count,
                output_path=str(latest_vi),
            )
            if score is not None:
                scores["visual_identity"] = float(score)
            total_findings += f_count
            total_recommendations += r_count

        # Check UX/UI
        ux_candidates = list(run_dir.glob("visual/*/analysis/ux-ui/*")) + list(run_dir.glob("analysis/ux-ui/*"))
        if ux_candidates:
            latest_ux = ux_candidates[-1]
            analysis_json = latest_ux / "analysis.json"
            score = None
            f_count = 0
            r_count = 0
            if analysis_json.exists():
                try:
                    data = json.loads(analysis_json.read_text(encoding="utf-8"))
                    score = data.get("overall_score")
                    f_count = len(data.get("findings", []))
                    r_count = len(data.get("recommendations", []))
                except Exception:
                    pass
            stages["ux_ui"] = StageExecutionRecord(
                stage_id="ux_ui",
                name="UX/UI Usability",
                name_ar="تجربة وواجهة المستخدم",
                status="completed" if score is not None else "partial",
                score=score,
                findings_count=f_count,
                recommendations_count=r_count,
                output_path=str(latest_ux),
            )
            if score is not None:
                scores["ux_ui"] = float(score)
            total_findings += f_count
            total_recommendations += r_count

        # Check Content Marketing
        cnt_candidates = list(run_dir.glob("analysis/content/*"))
        if cnt_candidates:
            latest_cnt = cnt_candidates[-1]
            analysis_json = latest_cnt / "analysis.json"
            score = None
            f_count = 0
            r_count = 0
            if analysis_json.exists():
                try:
                    data = json.loads(analysis_json.read_text(encoding="utf-8"))
                    score = data.get("overall_score")
                    f_count = len(data.get("findings", []))
                    r_count = len(data.get("recommendations", []))
                except Exception:
                    pass
            stages["content_marketing"] = StageExecutionRecord(
                stage_id="content_marketing",
                name="Content & Marketing",
                name_ar="المحتوى والتسويق",
                status="completed" if score is not None else "partial",
                score=score,
                findings_count=f_count,
                recommendations_count=r_count,
                output_path=str(latest_cnt),
            )
            if score is not None:
                scores["content_marketing"] = float(score)
            total_findings += f_count
            total_recommendations += r_count

        # Check Technical SEO
        seo_candidates = list(run_dir.glob("analysis/technical-seo/*"))
        if seo_candidates:
            latest_seo = seo_candidates[-1]
            analysis_json = latest_seo / "analysis.json"
            score = None
            f_count = 0
            r_count = 0
            if analysis_json.exists():
                try:
                    data = json.loads(analysis_json.read_text(encoding="utf-8"))
                    score = data.get("overall_score")
                    f_count = len(data.get("findings", []))
                    r_count = len(data.get("recommendations", []))
                except Exception:
                    pass
            stages["technical_seo"] = StageExecutionRecord(
                stage_id="technical_seo",
                name="Technical SEO",
                name_ar="SEO التقني والأداء",
                status="completed" if score is not None else "partial",
                score=score,
                findings_count=f_count,
                recommendations_count=r_count,
                output_path=str(latest_seo),
            )
            if score is not None:
                scores["technical_seo"] = float(score)
            total_findings += f_count
            total_recommendations += r_count

        # Check Competitor Intelligence
        comp_candidates = list(run_dir.glob("analysis/competitors/*"))
        if comp_candidates:
            latest_comp = comp_candidates[-1]
            analysis_json = latest_comp / "analysis.json"
            score = None
            f_count = 0
            r_count = 0
            if analysis_json.exists():
                try:
                    data = json.loads(analysis_json.read_text(encoding="utf-8"))
                    score = data.get("overall_score")
                    f_count = len(data.get("findings", []))
                    r_count = len(data.get("recommendations", []))
                except Exception:
                    pass
            stages["competitor_intelligence"] = StageExecutionRecord(
                stage_id="competitor_intelligence",
                name="Competitor Intelligence",
                name_ar="استخبارات المنافسين والمقارنة",
                status="completed" if score is not None else "partial",
                score=score,
                findings_count=f_count,
                recommendations_count=r_count,
                output_path=str(latest_comp),
            )
            if score is not None:
                scores["competitor_intelligence"] = float(score)
            total_findings += f_count
            total_recommendations += r_count

        # Check Security & Privacy Intelligence (Phase 09)
        sec_candidates = list(run_dir.glob("analysis/security-privacy/*"))
        if sec_candidates:
            latest_sec = sec_candidates[-1]
            analysis_json = latest_sec / "analysis.json"
            score = None
            f_count = 0
            r_count = 0
            if analysis_json.exists():
                try:
                    data = json.loads(analysis_json.read_text(encoding="utf-8"))
                    scores_dict = data.get("scores", {})
                    score = (
                        scores_dict.get("overall_score") if isinstance(scores_dict, dict) else data.get("overall_score")
                    )
                    f_count = len(data.get("findings", []))
                    r_count = len(data.get("recommendations", []))
                except Exception:
                    pass
            stages["security_privacy"] = StageExecutionRecord(
                stage_id="security_privacy",
                name="Security & Privacy",
                name_ar="الأمان والخصوصية والثقة",
                status="completed" if score is not None else "partial",
                score=score,
                findings_count=f_count,
                recommendations_count=r_count,
                output_path=str(latest_sec),
            )
            if score is not None:
                scores["security_privacy"] = float(score)
            total_findings += f_count
            total_recommendations += r_count

        # Check for accessibility analysis (Phase 10)
        a11y_dir = run_dir / "analysis" / "accessibility"
        if a11y_dir.exists():
            a11y_subdirs = [d for d in a11y_dir.iterdir() if d.is_dir()]
            latest_a11y = (
                sorted(a11y_subdirs, key=lambda d: d.stat().st_mtime, reverse=True)[0] if a11y_subdirs else a11y_dir
            )
            analysis_file = latest_a11y / "analysis.json"
            score = None
            f_count = 0
            r_count = 0
            if analysis_file.exists():
                try:
                    data = json.loads(analysis_file.read_text(encoding="utf-8"))
                    scores_dict = data.get("scores", {})
                    score = (
                        scores_dict.get("overall_score") if isinstance(scores_dict, dict) else data.get("overall_score")
                    )
                    f_count = len(data.get("findings", []))
                    r_count = len(data.get("recommendations", []))
                except Exception:
                    pass
            stages["accessibility"] = StageExecutionRecord(
                stage_id="accessibility",
                name="Web Accessibility & WCAG",
                name_ar="إمكانية الوصول ومعايير WCAG",
                status="completed" if score is not None else "partial",
                score=score,
                findings_count=f_count,
                recommendations_count=r_count,
                output_path=str(latest_a11y),
            )
            if score is not None:
                scores["accessibility"] = float(score)
            total_findings += f_count
            total_recommendations += r_count

        # Check for strategic intelligence (Phase 11)
        strat_dir = run_dir / "analysis" / "strategic-intelligence"
        if strat_dir.exists():
            strat_subdirs = [d for d in strat_dir.iterdir() if d.is_dir()]
            latest_strat = (
                sorted(strat_subdirs, key=lambda d: d.stat().st_mtime, reverse=True)[0] if strat_subdirs else strat_dir
            )
            analysis_file = latest_strat / "analysis.json"
            score = None
            f_count = 0
            r_count = 0
            if analysis_file.exists():
                try:
                    data = json.loads(analysis_file.read_text(encoding="utf-8"))
                    f_count = len(data.get("unified_findings", []))
                    r_count = len(data.get("actions", data.get("action_backlog", [])))
                    score = data.get("statistics", {}).get("strategic_index")
                except Exception:
                    pass
            stages["strategic_intelligence"] = StageExecutionRecord(
                stage_id="strategic_intelligence",
                name="Strategic Intelligence & Action Roadmap",
                name_ar="الذكاء الاستراتيجي وخارطة العمل الموحدة",
                status="completed" if f_count or r_count else "partial",
                score=score,
                findings_count=f_count,
                recommendations_count=r_count,
                output_path=str(latest_strat),
            )
            if score is not None:
                scores["strategic_intelligence"] = float(score)
            total_findings += f_count
            total_recommendations += r_count

        # Check for final reporting (Phase 12)
        final_rep_dir = run_dir / "reports" / "final"
        if final_rep_dir.exists():
            rep_subdirs = [d for d in final_rep_dir.iterdir() if d.is_dir()]
            if rep_subdirs:
                latest_rep = sorted(rep_subdirs, key=lambda d: d.stat().st_mtime, reverse=True)[0]
                summary_file = latest_rep / "export-summary.json"
                f_count = 0
                r_count = 0
                score = scores.get("strategic_intelligence")
                if summary_file.exists():
                    try:
                        sdata = json.loads(summary_file.read_text(encoding="utf-8"))
                        f_count = sdata.get("total_findings_count", 0)
                        r_count = sdata.get("total_actions_count", 0)
                    except Exception:
                        pass
                stages["executive_synthesis"] = StageExecutionRecord(
                    stage_id="executive_synthesis",
                    name="Final Reports & PDF Export",
                    name_ar="التقارير النهائية وتصدير PDF",
                    status="completed",
                    score=score,
                    findings_count=f_count,
                    recommendations_count=r_count,
                    output_path=str(latest_rep / "report.pdf"),
                )

        # Compute aggregate score (if multiple scores exist)
        overall_score = round(sum(scores.values()) / len(scores), 1) if scores else None

        record = RunRecord(
            run_id=run_id,
            url=target_url,
            canonical_origin=canonical_origin,
            status="completed" if stages else "failed",
            created_at=created_at,
            stages=stages,
            visual_run_id=visual_run_id,
            scores=scores,
            overall_score=overall_score,
            total_findings=total_findings,
            total_recommendations=total_recommendations,
        )
        self._save_run_state(record)
        return record

    def list_runs(
        self,
        query: Optional[str] = None,
        status_filter: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[RunRecord], int]:
        """List historical runs sorted newest first with optional search and filtering."""
        if not self.base_dir.exists():
            return [], 0

        run_dirs = [d for d in self.base_dir.iterdir() if d.is_dir() and d.name not in ("cache",)]
        records: list[RunRecord] = []

        for d in run_dirs:
            try:
                r = self.get_run(d.name)
                # Apply filters
                if status_filter and status_filter.lower() != "all" and r.status.lower() != status_filter.lower():
                    continue
                if query:
                    q = query.lower()
                    if q not in r.url.lower() and q not in r.run_id.lower():
                        continue
                records.append(r)
            except Exception:
                continue

        # Sort newest first
        records.sort(key=lambda r: r.created_at, reverse=True)
        total = len(records)
        start = (page - 1) * page_size
        return records[start : start + page_size], total

    def get_dashboard_summary(self) -> DashboardSummary:
        """Compile high-level dashboard metrics across historical runs."""
        runs, total = self.list_runs(page=1, page_size=100)
        completed = sum(1 for r in runs if r.status == "completed")
        running = sum(1 for r in runs if r.status in ("running", "queued", "created"))
        failed = sum(1 for r in runs if r.status == "failed")
        total_findings = sum(r.total_findings for r in runs)
        total_recs = sum(r.total_recommendations for r in runs)

        recent = [
            {
                "run_id": r.run_id,
                "url": r.url,
                "status": r.status,
                "created_at": r.created_at,
                "overall_score": r.overall_score,
                "scores": r.scores,
                "stages_completed": sum(1 for s in r.stages.values() if s.status == "completed"),
                "total_stages": len(r.stages),
                "findings_count": r.total_findings,
            }
            for r in runs[:6]
        ]

        readiness = {
            a.id: {"name": a.name, "name_ar": a.name_ar, "status": a.runtime_availability, "phase": a.phase}
            for a in AGENT_REGISTRY
        }

        return DashboardSummary(
            total_runs=total,
            completed_runs=completed,
            running_runs=running,
            failed_runs=failed,
            total_findings=total_findings,
            total_recommendations=total_recs,
            recent_runs=recent,
            agent_readiness=readiness,
        )

    def create_and_start_run(self, request: RunSubmissionRequest) -> RunRecord:
        """Validate input, create persistent run record, and launch background pipeline execution."""
        # 1. URL Validation
        target_url = request.url.strip()
        if not re.match(r"^https?://[a-zA-Z0-9\-\.]+(\.[a-zA-Z]{2,})?(:[0-9]+)?(/.*)?$", target_url):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid URL format: '{target_url}'. Must begin with http:// or https://.",
            )

        # 2. Stage Validation: Reject any planned / future agents
        for st in request.stages:
            if st in PLANNED_STAGE_IDS:
                agent = self.get_agent(st)
                label = agent.name if agent else st
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Agent '{label}' (Phase 08-12) is planned and cannot be executed.",
                )
            if st not in EXECUTABLE_STAGE_IDS and st != "all":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unknown or unsupported stage requested: '{st}'.",
                )

        # 3. Determine active stages and dependencies
        selected_stages = list(request.stages)
        if "all" in selected_stages:
            selected_stages = [
                "discovery",
                "visual_capture",
                "visual_identity",
                "ux_ui",
                "content_marketing",
                "technical_seo",
            ]

        # Ensure discovery is included
        if "discovery" not in selected_stages:
            selected_stages.insert(0, "discovery")

        # If visual_identity or ux_ui requested, ensure visual_capture is included
        if (
            "visual_identity" in selected_stages or "ux_ui" in selected_stages
        ) and "visual_capture" not in selected_stages:
            idx = selected_stages.index("discovery") + 1
            selected_stages.insert(idx, "visual_capture")

        # 4. Initialize Run Record
        run_id = f"run-{uuid.uuid4().hex[:12]}"
        run_dir = self._get_run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        stages_dict: dict[str, StageExecutionRecord] = {}
        for st in selected_stages:
            agent = self.get_agent(st)
            stages_dict[st] = StageExecutionRecord(
                stage_id=st,
                name=agent.name if agent else st,
                name_ar=agent.name_ar if agent else st,
                status="queued",
            )

        run_record = RunRecord(
            run_id=run_id,
            url=target_url,
            status="queued",
            stages=stages_dict,
        )
        self._save_run_state(run_record)

        self._emit_event(
            run_id=run_id,
            event_type="run.created",
            message=f"Analysis run created for {target_url} with {len(selected_stages)} stages.",
            message_ar=f"تم إنشاء جولة الفحص للموقع {target_url} بـ {len(selected_stages)} مراحل مختارة.",
            data={"stages": selected_stages, "url": target_url},
        )

        # 5. Launch background execution task
        asyncio.create_task(self._execute_pipeline(run_id, request, selected_stages))

        return run_record

    async def _execute_pipeline(self, run_id: str, request: RunSubmissionRequest, stages: list[str]) -> None:
        """Asynchronously execute requested stages in topological dependency order."""
        logger.info("[PIPELINE %s] Starting execution with stages: %s", run_id, stages)
        start_time = datetime.now(timezone.utc)
        record = self.get_run(run_id)
        record.status = "running"
        self._save_run_state(record)
        self._emit_event(
            run_id=run_id,
            event_type="run.started",
            message="Execution pipeline started.",
            message_ar="بدأ تشغيل مراحل الفحص الفعلي للموقع.",
        )

        crawl_result: Optional[CrawlResult] = None
        has_blocker = False

        try:
            # Stage 1: Discovery & Crawling
            if "discovery" in stages:
                crawl_result = await self._run_discovery_stage(record, request)
                if not crawl_result:
                    has_blocker = True
            else:
                crawl_file = self._get_run_dir(record.run_id) / "crawl.json"
                if crawl_file.exists():
                    try:
                        crawl_result = CrawlResult.model_validate_json(crawl_file.read_text(encoding="utf-8"))
                    except Exception:
                        crawl_result = await self._run_discovery_stage(record, request)
                else:
                    crawl_result = await self._run_discovery_stage(record, request)
                if not crawl_result:
                    has_blocker = True

            # Stage 2: Visual Capture & Screenshots
            needs_visual = ("visual_capture" in stages) or ("visual_identity" in stages) or ("ux_ui" in stages)
            if needs_visual and not has_blocker:
                if "visual_capture" in stages or not record.visual_run_id:
                    await self._run_visual_stage(record, crawl_result, request)

            # Stage 3: Visual Identity
            if "visual_identity" in stages and not has_blocker:
                await self._run_visual_identity_stage(record, request)

            # Stage 4: UX/UI Analysis
            if "ux_ui" in stages and not has_blocker:
                await self._run_ux_stage(record, request)

            # Stage 5: Content & Marketing
            if "content_marketing" in stages and not has_blocker:
                await self._run_content_stage(record, request)

            # Stage 6: Technical SEO & Performance
            if "technical_seo" in stages and not has_blocker:
                await self._run_technical_seo_stage(record, request)

            # Stage 7: Competitor Intelligence
            if "competitor_intelligence" in stages and not has_blocker:
                await self._run_competitor_stage(record, request)

            # Stage 8: Security & Privacy Intelligence (Phase 09)
            if "security_privacy" in stages and not has_blocker:
                await self._run_security_stage(record, request)

            # Stage 9: Accessibility Intelligence & WCAG 2.2 (Phase 10)
            if "accessibility" in stages and not has_blocker:
                await self._run_accessibility_stage(record, request)

            # Stage 10: Strategic Intelligence & Action Roadmap (Phase 11)
            if "strategic_intelligence" in stages and not has_blocker:
                await self._run_strategic_stage(record, request)

            # Stage 11: Final Reporting & PDF Export (Phase 12)
            if "executive_synthesis" in stages and not has_blocker:
                await self._run_final_reporting_stage(record, request)

        except Exception as exc:
            logger.error("[PIPELINE %s] Execution crashed: %s", run_id, exc, exc_info=True)
            record.status = "failed"
            record.error_message = str(exc)
            self._emit_event(
                run_id=run_id,
                event_type="run.failed",
                message=f"Pipeline aborted: {exc}",
                message_ar=f"فشل تشغيل مسار الفحص: {exc}",
                data={"error": str(exc)},
            )
        finally:
            # Finalize run status and scores
            end_time = datetime.now(timezone.utc)
            record.completed_at = end_time.isoformat()
            record.total_duration_ms = round((end_time - start_time).total_seconds() * 1000, 1)

            # Evaluate overall status
            statuses = [s.status for s in record.stages.values()]
            if all(s == "completed" for s in statuses):
                record.status = "completed"
            elif any(s == "ai_blocked" for s in statuses):
                record.status = "ai_blocked"
            elif any(s == "completed" for s in statuses):
                record.status = "partial"
            elif record.status != "failed":
                record.status = "completed" if statuses else "failed"

            # Compute overall score from collected scores
            if record.scores:
                record.overall_score = round(sum(record.scores.values()) / len(record.scores), 1)

            record.total_findings = sum(s.findings_count for s in record.stages.values())
            record.total_recommendations = sum(s.recommendations_count for s in record.stages.values())

            self._save_run_state(record)
            self._emit_event(
                run_id=run_id,
                event_type="run.completed" if record.status in ("completed", "partial", "ai_blocked") else "run.failed",
                message=f"Run completed with status {record.status.upper()} in {record.total_duration_ms} ms.",
                message_ar=f"اكتملت الجولة بحالة {record.status} خلال {record.total_duration_ms} ميلي ثانية.",
                data={"status": record.status, "overall_score": record.overall_score},
            )

    async def _run_discovery_stage(self, record: RunRecord, request: RunSubmissionRequest) -> Optional[CrawlResult]:
        """Execute Phase 02 website discovery."""
        stage = record.stages["discovery"]
        stage.status = "running"
        stage.started_at = datetime.now(timezone.utc).isoformat()
        self._save_run_state(record)
        self._emit_event(
            record.run_id,
            "stage.started",
            "Starting Website Discovery & Crawling...",
            "بدء زحف واستكشاف مسارات الموقع...",
            "discovery",
        )

        t0 = datetime.now(timezone.utc)
        try:
            service = WebsiteDiscoveryService(settings=self.settings)
            effective_max = 50 if getattr(request, "full_site_scan", False) else (request.max_pages or 5)
            crawl_req = CrawlRequest(url=record.url, max_pages=effective_max)
            result = await service.discover(crawl_req)
            old_run_id = result.run_id
            result.run_id = record.run_id  # Align discovery run_id with coordinator run_id
            t1 = datetime.now(timezone.utc)

            # Persist crawl.json to coordinator run dir and discovery run dir
            coord_run_dir = self._get_run_dir(record.run_id)
            coord_run_dir.mkdir(parents=True, exist_ok=True)
            crawl_json_content = result.model_dump_json(indent=2)
            (coord_run_dir / "crawl.json").write_text(crawl_json_content, encoding="utf-8")
            if old_run_id and old_run_id != record.run_id:
                old_dir = self._get_run_dir(old_run_id)
                old_dir.mkdir(parents=True, exist_ok=True)
                (old_dir / "crawl.json").write_text(crawl_json_content, encoding="utf-8")

            stage.status = "completed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.output_path = str(coord_run_dir / "crawl.json")
            record.canonical_origin = result.website_info.canonical_origin

            self._emit_event(
                record.run_id,
                "stage.completed",
                f"Discovery completed: {result.statistics.total_pages_crawled} pages discovered.",
                f"اكتمل الزحف بنجاح: تم اكتشاف {result.statistics.total_pages_crawled} صفحة.",
                "discovery",
                {"pages_crawled": result.statistics.total_pages_crawled},
            )
            return result
        except Exception as exc:
            t1 = datetime.now(timezone.utc)
            stage.status = "failed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.error_message = str(exc)
            self._emit_event(
                record.run_id, "stage.failed", f"Discovery failed: {exc}", f"فشل الاستكشاف والزحف: {exc}", "discovery"
            )
            return None

    async def _run_visual_stage(
        self,
        record: RunRecord,
        crawl_result: Optional[CrawlResult],
        request: Optional[RunSubmissionRequest] = None,
    ) -> Optional[VisualCaptureResult]:
        """Execute Phase 03 visual capture and screenshots."""
        stage = record.stages["visual_capture"]
        stage.status = "running"
        stage.started_at = datetime.now(timezone.utc).isoformat()
        self._save_run_state(record)
        self._emit_event(
            record.run_id,
            "stage.started",
            "Starting Browser Rendering & Screenshot Capture...",
            "بدء تشغيل المتصفح والتقاط الأدلة البصرية لسطح المكتب والجوال...",
            "visual_capture",
        )

        t0 = datetime.now(timezone.utc)
        try:
            if not crawl_result:
                # Load crawl result from disk
                crawl_file = self._get_run_dir(record.run_id) / "crawl.json"
                if not crawl_file.exists():
                    raise FileNotFoundError("Missing crawl.json for visual capture.")
                crawl_result = CrawlResult.model_validate_json(crawl_file.read_text(encoding="utf-8"))

            service = VisualCollectionService(settings=self.settings)
            pages_limit = len(crawl_result.pages) if crawl_result and crawl_result.pages else 5
            visual_result = await service.collect_visual_evidence(crawl_result, max_pages=pages_limit)
            t1 = datetime.now(timezone.utc)

            stage.status = "completed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.output_path = str(
                self._get_run_dir(record.run_id) / "visual" / visual_result.visual_run_id / "manifest.json"
            )
            record.visual_run_id = visual_result.visual_run_id

            screenshots_count = sum(len(p.desktop_screenshots) + len(p.mobile_screenshots) for p in visual_result.pages)
            self._emit_event(
                record.run_id,
                "stage.completed",
                f"Visual capture completed: {screenshots_count} screenshots captured.",
                f"اكتمل الالتقاط البصري: تم تسجيل {screenshots_count} لقطة شاشة واستخراج شجرة DOM.",
                "visual_capture",
                {"screenshots_count": screenshots_count, "visual_run_id": visual_result.visual_run_id},
            )
            return visual_result
        except Exception as exc:
            t1 = datetime.now(timezone.utc)
            stage.status = "failed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.error_message = str(exc)
            self._emit_event(
                record.run_id,
                "stage.failed",
                f"Visual capture failed: {exc}",
                f"فشل الالتقاط البصري: {exc}",
                "visual_capture",
            )
            return None

    async def _run_visual_identity_stage(self, record: RunRecord, request: RunSubmissionRequest) -> None:
        """Execute Phase 04 AI Visual Identity analysis."""
        stage = record.stages["visual_identity"]
        stage.status = "running"
        stage.started_at = datetime.now(timezone.utc).isoformat()
        self._save_run_state(record)
        self._emit_event(
            record.run_id,
            "stage.started",
            "Analyzing Visual Identity with Gemini 3.6 Flash...",
            "تحليل الهوية البصرية وتناسق الألوان والخطوط عبر Gemini 3.6 Flash...",
            "visual_identity",
        )

        t0 = datetime.now(timezone.utc)
        try:
            service = VisualIdentityAnalysisService(settings=self.settings)
            vi_req = VisualIdentityAnalysisRequest(
                visual_run_id=record.visual_run_id,
                crawl_run_id=record.run_id,
                offline_mode=request.offline_mode or request.deterministic_only,
            )
            # Run blocking service in thread pool to prevent blocking asyncio loop
            report = await asyncio.to_thread(service.analyze_visual_identity, vi_req)
            t1 = datetime.now(timezone.utc)

            is_ai_blocked = (
                getattr(report, "status", "") == "AI_BLOCKED" or getattr(report, "ai_status", "") == "ai_blocked"
            )
            stage.status = "ai_blocked" if is_ai_blocked else "completed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.score = report.overall_score
            stage.findings_count = len(report.findings)
            stage.recommendations_count = len(report.recommendations)
            stage.analysis_run_id = report.analysis_run_id

            if report.overall_score is not None:
                record.scores["visual_identity"] = float(report.overall_score)

            self._emit_event(
                record.run_id,
                "stage.ai_blocked" if is_ai_blocked else "stage.completed",
                f"Visual Identity score: {report.overall_score}/100 ({len(report.findings)} findings).",
                f"تقييم الهوية البصرية: {report.overall_score}/100 مع {len(report.findings)} ملاحظة موثقة.",
                "visual_identity",
                {"score": report.overall_score, "findings": len(report.findings)},
            )
        except Exception as exc:
            t1 = datetime.now(timezone.utc)
            stage.status = "failed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.error_message = str(exc)
            self._emit_event(
                record.run_id,
                "stage.failed",
                f"Visual Identity failed: {exc}",
                f"فشل تحليل الهوية البصرية: {exc}",
                "visual_identity",
            )

    async def _run_ux_stage(self, record: RunRecord, request: RunSubmissionRequest) -> None:
        """Execute Phase 05 UX/UI usability analysis."""
        stage = record.stages["ux_ui"]
        stage.status = "running"
        stage.started_at = datetime.now(timezone.utc).isoformat()
        self._save_run_state(record)
        self._emit_event(
            record.run_id,
            "stage.started",
            "Analyzing UX/UI Usability and Interaction...",
            "فحص قابلية الاستخدام وتجربة المستخدم وتجاوب الواجهات...",
            "ux_ui",
        )

        t0 = datetime.now(timezone.utc)
        try:
            service = UXAnalysisService(settings=self.settings)
            ux_req = UXAnalysisRequest(
                visual_run_id=record.visual_run_id,
                crawl_run_id=record.run_id,
                offline_mode=request.offline_mode or request.deterministic_only,
            )
            report = await asyncio.to_thread(service.analyze_ux, ux_req, offline_mode=ux_req.offline_mode)
            t1 = datetime.now(timezone.utc)

            is_ai_blocked = (
                getattr(report, "status", "") == "AI_BLOCKED" or getattr(report, "ai_status", "") == "ai_blocked"
            )
            stage.status = "ai_blocked" if is_ai_blocked else "completed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.score = report.overall_score
            stage.findings_count = len(report.findings)
            stage.recommendations_count = len(report.recommendations)
            stage.analysis_run_id = report.analysis_run_id

            if report.overall_score is not None:
                record.scores["ux_ui"] = float(report.overall_score)

            self._emit_event(
                record.run_id,
                "stage.ai_blocked" if is_ai_blocked else "stage.completed",
                f"UX/UI usability score: {report.overall_score}/100 ({len(report.findings)} findings).",
                f"تقييم تجربة المستخدم: {report.overall_score}/100 مع {len(report.findings)} ملاحظة.",
                "ux_ui",
                {"score": report.overall_score, "findings": len(report.findings)},
            )
        except Exception as exc:
            t1 = datetime.now(timezone.utc)
            stage.status = "failed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.error_message = str(exc)
            self._emit_event(
                record.run_id,
                "stage.failed",
                f"UX/UI analysis failed: {exc}",
                f"فشل فحص تجربة المستخدم: {exc}",
                "ux_ui",
            )

    async def _run_content_stage(self, record: RunRecord, request: RunSubmissionRequest) -> None:
        """Execute Phase 06 Content & Marketing analysis."""
        stage = record.stages["content_marketing"]
        stage.status = "running"
        stage.started_at = datetime.now(timezone.utc).isoformat()
        self._save_run_state(record)
        self._emit_event(
            record.run_id,
            "stage.started",
            "Analyzing Content & Marketing Intelligence...",
            "تحليل نبرة المحتوى، القيمة المقترحة، ونصوص التحويل...",
            "content_marketing",
        )

        t0 = datetime.now(timezone.utc)
        try:
            service = ContentMarketingAnalysisService(settings=self.settings)
            cnt_req = ContentAnalysisRequest(
                crawl_run_id=record.run_id,
                visual_run_id=record.visual_run_id,
                offline_mode=request.offline_mode or request.deterministic_only,
            )
            report = await asyncio.to_thread(service.analyze, cnt_req, offline_mode=cnt_req.offline_mode)
            t1 = datetime.now(timezone.utc)

            is_ai_blocked = (
                getattr(report, "status", "") == "AI_BLOCKED" or getattr(report, "ai_status", "") == "ai_blocked"
            )
            stage.status = "ai_blocked" if is_ai_blocked else "completed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.score = report.overall_score
            stage.findings_count = len(report.findings)
            stage.recommendations_count = len(report.recommendations)
            stage.analysis_run_id = report.analysis_run_id

            if report.overall_score is not None:
                record.scores["content_marketing"] = float(report.overall_score)

            self._emit_event(
                record.run_id,
                "stage.ai_blocked" if is_ai_blocked else "stage.completed",
                f"Content & Marketing score: {report.overall_score}/100 ({len(report.findings)} findings).",
                f"تقييم المحتوى والتسويق: {report.overall_score}/100 مع {len(report.findings)} ملاحظة.",
                "content_marketing",
                {"score": report.overall_score, "findings": len(report.findings)},
            )
        except Exception as exc:
            t1 = datetime.now(timezone.utc)
            stage.status = "failed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.error_message = str(exc)
            self._emit_event(
                record.run_id,
                "stage.failed",
                f"Content analysis failed: {exc}",
                f"فشل فحص المحتوى والتسويق: {exc}",
                "content_marketing",
            )

    async def _run_technical_seo_stage(self, record: RunRecord, request: RunSubmissionRequest) -> None:
        """Execute Phase 07 Technical SEO and Performance analysis."""
        stage = record.stages["technical_seo"]
        stage.status = "running"
        stage.started_at = datetime.now(timezone.utc).isoformat()
        self._save_run_state(record)
        self._emit_event(
            record.run_id,
            "stage.started",
            "Auditing Technical SEO & Core Web Vitals...",
            "فحص قابلية الزحف والفهرسة وروابط Canonical ومؤشرات الأداء LCP/CLS...",
            "technical_seo",
        )

        t0 = datetime.now(timezone.utc)
        try:
            service = TechnicalSEOAnalysisService(settings=self.settings)
            seo_req = TechnicalSEOAnalysisRequest(
                crawl_run_id=record.run_id,
                visual_run_id=record.visual_run_id,
                offline_mode=request.offline_mode or request.deterministic_only,
                deterministic_only=request.deterministic_only,
            )
            report = await asyncio.to_thread(service.analyze, seo_req)
            t1 = datetime.now(timezone.utc)

            is_ai_blocked = (
                getattr(report, "analysis_status", "") == "ai_blocked" or getattr(report, "status", "") == "AI_BLOCKED"
            )
            stage.status = "ai_blocked" if is_ai_blocked else "completed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.score = report.overall_score
            stage.findings_count = len(report.findings)
            stage.recommendations_count = len(report.recommendations)
            stage.analysis_run_id = report.analysis_run_id

            if report.overall_score is not None:
                record.scores["technical_seo"] = float(report.overall_score)

            self._emit_event(
                record.run_id,
                "stage.ai_blocked" if is_ai_blocked else "stage.completed",
                f"Technical SEO score: {report.overall_score}/100 ({len(report.findings)} findings).",
                f"تقييم SEO التقني: {report.overall_score}/100 مع {len(report.findings)} ملاحظة.",
                "technical_seo",
                {"score": report.overall_score, "findings": len(report.findings)},
            )
        except Exception as exc:
            t1 = datetime.now(timezone.utc)
            stage.status = "failed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.error_message = str(exc)
            self._emit_event(
                record.run_id,
                "stage.failed",
                f"Technical SEO failed: {exc}",
                f"فشل تدقيق SEO التقني: {exc}",
                "technical_seo",
            )

    async def _run_competitor_stage(self, record: RunRecord, request: RunSubmissionRequest) -> None:
        """Execute Phase 08 Competitor Intelligence & Benchmarking."""
        stage = record.stages["competitor_intelligence"]
        stage.status = "running"
        stage.started_at = datetime.now(timezone.utc).isoformat()
        self._save_run_state(record)
        self._emit_event(
            record.run_id,
            "stage.started",
            "Starting Competitor Intelligence & Benchmarking...",
            "بدء استخبارات ومقارنة المنافسين المعيارية وتحليل التموضع...",
            "competitor_intelligence",
        )

        t0 = datetime.now(timezone.utc)
        try:
            from site_dna.analysis.competitor_intelligence.service import CompetitorIntelligenceService
            from site_dna.schemas.competitor_intelligence import CompetitorAnalysisRequest

            service = CompetitorIntelligenceService(settings=self.settings)
            comp_req = CompetitorAnalysisRequest(
                primary_url=record.url,
                primary_run_id=record.run_id,
                competitor_urls=request.competitor_urls or [],
                offline_mode=request.offline_mode or request.deterministic_only,
            )
            report = await asyncio.to_thread(service.analyze, comp_req)
            t1 = datetime.now(timezone.utc)

            is_ai_blocked = (
                getattr(report, "status", "") == "AI_BLOCKED" or getattr(report, "ai_status", "") == "ai_blocked"
            )
            stage.status = "ai_blocked" if is_ai_blocked else "completed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            comp_score = getattr(report, "overall_score", None)
            if comp_score is None and hasattr(report, "scores") and hasattr(report.scores, "overall_score"):
                comp_score = report.scores.overall_score
            stage.score = comp_score
            stage.findings_count = len(report.findings) if hasattr(report, "findings") else 0
            stage.recommendations_count = len(report.recommendations) if hasattr(report, "recommendations") else 0
            stage.analysis_run_id = getattr(report, "analysis_run_id", getattr(report, "comparison_run_id", None))

            if comp_score is not None:
                record.scores["competitor_intelligence"] = float(comp_score)

            self._emit_event(
                record.run_id,
                "stage.ai_blocked" if is_ai_blocked else "stage.completed",
                f"Competitor Intelligence score: {report.overall_score}/100 ({len(report.findings)} findings).",
                f"تقييم المقارنة التنافسية: {report.overall_score}/100 مع {len(report.findings)} ملاحظة موثقة.",
                "competitor_intelligence",
                {"score": report.overall_score, "findings": len(report.findings)},
            )
        except Exception as exc:
            t1 = datetime.now(timezone.utc)
            stage.status = "failed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.error_message = str(exc)
            self._emit_event(
                record.run_id,
                "stage.failed",
                f"Competitor Intelligence failed: {exc}",
                f"فشل فحص المنافسين والمقارنة المعيارية: {exc}",
                "competitor_intelligence",
            )

    async def _run_security_stage(self, record: RunRecord, request: RunSubmissionRequest) -> None:
        """Execute Phase 09 Security, Privacy & Digital Trust Intelligence."""
        stage = record.stages["security_privacy"]
        stage.status = "running"
        stage.started_at = datetime.now(timezone.utc).isoformat()
        self._save_run_state(record)
        self._emit_event(
            record.run_id,
            "stage.started",
            "Auditing Security, Privacy & Trust Intelligence...",
            "فحص أمان النقل وتشفير HTTPS، رؤوس الحماية، ملفات الارتباط، ومؤشرات الخصوصية والثقة...",
            "security_privacy",
        )

        t0 = datetime.now(timezone.utc)
        try:
            from site_dna.analysis.security_privacy.service import SecurityPrivacyService
            from site_dna.schemas.security_privacy import SecurityPrivacyAnalysisRequest

            service = SecurityPrivacyService(settings=self.settings)
            sec_req = SecurityPrivacyAnalysisRequest(
                crawl_run_id=record.run_id,
                visual_run_id=record.visual_run_id,
                language="ar",
                max_pages=request.max_pages or 8,
                offline_mode=request.offline_mode or request.deterministic_only,
                deterministic_only=request.deterministic_only,
                save_results=True,
            )
            report = await service.analyze_security(sec_req)
            t1 = datetime.now(timezone.utc)

            is_ai_blocked = (
                getattr(report, "analysis_status", "") == "ai_blocked"
                or getattr(report.statistics, "ai_status", "") == "quota_blocked"
            )
            stage.status = "ai_blocked" if is_ai_blocked else "completed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            score_val = (
                report.scores.overall_score if report.scores and report.scores.overall_score is not None else None
            )
            stage.score = score_val
            stage.findings_count = len(report.findings)
            stage.recommendations_count = len(report.recommendations)
            stage.analysis_run_id = report.security_run_id

            if score_val is not None:
                record.scores["security_privacy"] = float(score_val)

            self._emit_event(
                record.run_id,
                "stage.ai_blocked" if is_ai_blocked else "stage.completed",
                f"Security & Privacy score: {score_val}/100 ({len(report.findings)} findings).",
                f"تقييم الأمان والخصوصية: {score_val}/100 مع {len(report.findings)} ملاحظة موثقة.",
                "security_privacy",
                {"score": score_val, "findings": len(report.findings)},
            )
        except Exception as exc:
            t1 = datetime.now(timezone.utc)
            stage.status = "failed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.error_message = str(exc)
            self._emit_event(
                record.run_id,
                "stage.failed",
                f"Security & Privacy failed: {exc}",
                f"فشل فحص الأمان والخصوصية: {exc}",
                "security_privacy",
            )

    async def _run_accessibility_stage(self, record: RunRecord, request: RunSubmissionRequest) -> None:
        """Execute Phase 10 Web Accessibility & WCAG 2.2 Intelligence."""
        stage = record.stages["accessibility"]
        stage.status = "running"
        stage.started_at = datetime.now(timezone.utc).isoformat()
        self._save_run_state(record)
        self._emit_event(
            record.run_id,
            "stage.started",
            "Auditing Web Accessibility & WCAG 2.2...",
            "فحص إمكانية الوصول والنفاذ الرقمي ومعايير WCAG 2.2 A/AA، ولوحة المفاتيح والتباين...",
            "accessibility",
        )

        t0 = datetime.now(timezone.utc)
        try:
            from site_dna.analysis.accessibility.service import AccessibilityService
            from site_dna.schemas.accessibility import AccessibilityAnalysisRequest

            service = AccessibilityService(settings=self.settings)
            a11y_req = AccessibilityAnalysisRequest(
                crawl_run_id=record.run_id,
                visual_run_id=record.visual_run_id,
                language="ar",
                max_pages=request.max_pages or 8,
                deterministic_only=request.deterministic_only,
                save_results=True,
            )
            report = await service.analyze_accessibility(a11y_req)
            t1 = datetime.now(timezone.utc)

            is_ai_blocked = getattr(report, "analysis_status", "") == "blocked_ai"
            stage.status = "ai_blocked" if is_ai_blocked else "completed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            score_val = (
                report.scores.overall_score if report.scores and report.scores.overall_score is not None else None
            )
            stage.score = score_val
            stage.findings_count = len(report.findings)
            stage.recommendations_count = len(report.recommendations)
            stage.analysis_run_id = report.accessibility_run_id

            if score_val is not None:
                record.scores["accessibility"] = float(score_val)

            self._emit_event(
                record.run_id,
                "stage.ai_blocked" if is_ai_blocked else "stage.completed",
                f"Accessibility score: {score_val}/100 ({len(report.findings)} findings).",
                f"تقييم إمكانية الوصول: {score_val}/100 مع {len(report.findings)} ملاحظة موثقة.",
                "accessibility",
                {"score": score_val, "findings": len(report.findings)},
            )
        except Exception as exc:
            t1 = datetime.now(timezone.utc)
            stage.status = "failed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.error_message = str(exc)
            self._emit_event(
                record.run_id,
                "stage.failed",
                f"Accessibility audit failed: {exc}",
                f"فشل فحص إمكانية الوصول: {exc}",
                "accessibility",
            )

    async def _run_strategic_stage(self, record: RunRecord, request: RunSubmissionRequest) -> None:
        """Execute Phase 11 Strategic Intelligence & Action Roadmap."""
        stage = record.stages["strategic_intelligence"]
        stage.status = "running"
        stage.started_at = datetime.now(timezone.utc).isoformat()
        self._save_run_state(record)
        self._emit_event(
            record.run_id,
            "stage.started",
            "Synthesizing Cross-Agent Strategic Intelligence & Action Roadmap...",
            "توليف الذكاء الاستراتيجي عبر كافة الوكلاء وبناء خارطة العمل التنفيذية الموحدة...",
            "strategic_intelligence",
        )

        t0 = datetime.now(timezone.utc)
        try:
            from site_dna.analysis.strategic_intelligence.service import StrategicIntelligenceService
            from site_dna.schemas.strategic_intelligence import StrategicAnalysisRequest

            service = StrategicIntelligenceService(settings=self.settings)
            strat_req = StrategicAnalysisRequest(
                crawl_run_id=record.run_id,
                language="ar",
                deterministic_only=request.deterministic_only,
                save_results=True,
            )
            report = await service.analyze_strategy(strat_req)
            t1 = datetime.now(timezone.utc)

            is_ai_blocked = (
                getattr(report, "analysis_status", "") == "blocked_ai"
                or getattr(report, "ai_status", "") in ("quota_blocked", "blocked_ai")
                or getattr(getattr(report, "statistics", None), "ai_status", "") == "quota_blocked"
            )
            stage.status = "ai_blocked" if is_ai_blocked else "completed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            score_val = (
                report.statistics.strategic_index
                if report.statistics and report.statistics.strategic_index is not None
                else None
            )
            stage.score = score_val
            stage.findings_count = len(report.unified_findings)
            stage.recommendations_count = len(report.actions)
            stage.analysis_run_id = report.strategic_run_id

            if score_val is not None:
                record.scores["strategic_intelligence"] = float(score_val)

            self._emit_event(
                record.run_id,
                "stage.ai_blocked" if is_ai_blocked else "stage.completed",
                f"Strategic Intelligence score: {score_val}/100 ({len(report.unified_findings)} unified findings, {len(report.actions)} actions).",
                f"التقييم الاستراتيجي الشامل: {score_val}/100 مع {len(report.unified_findings)} ملاحظة موحدة و {len(report.actions)} إجراء علاجي.",
                "strategic_intelligence",
                {"score": score_val, "findings": len(report.unified_findings), "actions": len(report.actions)},
            )

            # Synthesize dedicated AI & Automation Readiness analysis
            try:
                from site_dna.analysis.ai_automation.analyzer import AIAutomationAnalyzer
                ai_analyzer = AIAutomationAnalyzer(base_dir=self.base_dir)
                ai_analyzer.analyze_run(record.run_id)
            except Exception as ai_exc:
                logger.warning("AI & Automation analysis failed: %s", ai_exc)
        except Exception as exc:
            t1 = datetime.now(timezone.utc)
            stage.status = "failed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.error_message = str(exc)
            self._emit_event(
                record.run_id,
                "stage.failed",
                f"Strategic Intelligence synthesis failed: {exc}",
                f"فشل توليف الذكاء الاستراتيجي: {exc}",
                "strategic_intelligence",
            )

    async def _run_final_reporting_stage(self, record: RunRecord, request: RunSubmissionRequest) -> None:
        """Execute Phase 12 Final Reporting, Enterprise PDF Export & Quality Verification."""
        stage = record.stages["executive_synthesis"]
        stage.status = "running"
        stage.started_at = datetime.now(timezone.utc).isoformat()
        self._save_run_state(record)
        self._emit_event(
            record.run_id,
            "stage.started",
            "Generating Enterprise Executive & Full System Report (Phase 12)...",
            "توليد التقرير التنفيذي والمؤسسي الموحد وتصدير وثيقة PDF عالية الجودة (المرحلة 12)...",
            "executive_synthesis",
        )

        t0 = datetime.now(timezone.utc)
        try:
            from site_dna.reporting.export_service import FinalReportExportService
            from site_dna.schemas.final_report import FinalReportRequest

            service = FinalReportExportService(settings=self.settings)
            report_req = FinalReportRequest(
                crawl_run_id=record.run_id,
                mode="comprehensive",
                language="ar",
                include_evidence_catalog=True,
                validate_pdf=True,
                deterministic_only=request.deterministic_only,
            )
            meta = await service.generate_report(report_req)
            t1 = datetime.now(timezone.utc)

            stage.status = "completed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.score = meta.overall_score
            stage.findings_count = meta.total_findings
            stage.recommendations_count = meta.total_recommendations
            stage.analysis_run_id = meta.report_id

            if meta.overall_score is not None:
                record.scores["executive_synthesis"] = float(meta.overall_score)

            self._emit_event(
                record.run_id,
                "stage.completed",
                f"Executive Report generated ({meta.page_count} pages, {meta.total_findings} findings, score: {meta.overall_score}/100).",
                f"تم توليد التقرير التنفيذي الشامل بنجاح ({meta.page_count} صفحة، {meta.total_findings} ملاحظة، التقييم: {meta.overall_score}/100).",
                "executive_synthesis",
                {
                    "report_id": meta.report_id,
                    "pages": meta.page_count,
                    "score": meta.overall_score,
                    "findings": meta.total_findings,
                    "recommendations": meta.total_recommendations,
                    "pdf_path": meta.artifacts.pdf,
                },
            )
        except Exception as exc:
            t1 = datetime.now(timezone.utc)
            stage.status = "failed"
            stage.completed_at = t1.isoformat()
            stage.duration_ms = round((t1 - t0).total_seconds() * 1000, 1)
            stage.error_message = str(exc)
            self._emit_event(
                record.run_id,
                "stage.failed",
                f"Final Reporting generation failed: {exc}",
                f"فشل توليد التقرير التنفيذي النهائي: {exc}",
                "executive_synthesis",
            )

    def get_screenshots(self, run_id: str) -> list[dict[str, Any]]:
        """List captured screenshots for a run with safe view paths."""
        run_dir = self._get_run_dir(run_id)
        manifest_files = list(run_dir.glob("visual/*/manifest.json"))
        screenshots: list[dict[str, Any]] = []

        for mf in manifest_files:
            try:
                data = json.loads(mf.read_text(encoding="utf-8"))
                vis_id = data.get("visual_run_id", "")
                for page in data.get("pages", []):
                    page_url = page.get("page_url", "")
                    safe_id = page.get("safe_page_id", "")
                    # Desktop
                    for ds in page.get("desktop_screenshots", []):
                        fn = ds.get("relative_path", "desktop-viewport.png") if isinstance(ds, dict) else str(ds)
                        screenshots.append(
                            {
                                "device": "desktop",
                                "page_url": page_url,
                                "filename": fn,
                                "safe_page_id": safe_id,
                                "visual_run_id": vis_id,
                                "api_url": f"/api/v1/runs/{run_id}/artifacts/screenshot?file={vis_id}/pages/{safe_id}/{fn}",
                            }
                        )
                    # Mobile
                    for ms in page.get("mobile_screenshots", []):
                        fn = ms.get("relative_path", "mobile-viewport.png") if isinstance(ms, dict) else str(ms)
                        screenshots.append(
                            {
                                "device": "mobile",
                                "page_url": page_url,
                                "filename": fn,
                                "safe_page_id": safe_id,
                                "visual_run_id": vis_id,
                                "api_url": f"/api/v1/runs/{run_id}/artifacts/screenshot?file={vis_id}/pages/{safe_id}/{fn}",
                            }
                        )
            except Exception:
                continue

        return screenshots

    def resolve_screenshot_path(self, run_id: str, relative_file: str) -> Path:
        """Safely resolve an actual screenshot image file preventing traversal."""
        clean_file = relative_file.replace("\\", "/").strip("/")
        if ".." in clean_file.split("/"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Path traversal not permitted.")

        run_dir = self._get_run_dir(run_id)
        target = (run_dir / "visual" / clean_file).resolve()
        # Verify bounded inside run_dir
        if not str(target).startswith(str(run_dir)):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
        if not target.exists() or not target.is_file():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Screenshot image not found.")
        return target

    def get_findings(self, run_id: str, agent_filter: Optional[str] = None) -> list[dict[str, Any]]:
        """Aggregate structured findings across all completed analysis stages for a run."""
        run_dir = self._get_run_dir(run_id)
        findings: list[dict[str, Any]] = []

        # 1. Visual Identity
        if not agent_filter or agent_filter == "visual_identity":
            for f_path in run_dir.glob("visual/*/analysis/visual-identity/*/findings.json"):
                try:
                    items = json.loads(f_path.read_text(encoding="utf-8"))
                    for it in items:
                        it["agent_id"] = "visual_identity"
                        it["agent_name"] = "الهوية البصرية (Visual Identity)"
                        findings.append(it)
                except Exception:
                    pass

        # 2. UX/UI
        if not agent_filter or agent_filter == "ux_ui":
            for f_path in run_dir.glob("visual/*/analysis/ux-ui/*/findings.json"):
                try:
                    items = json.loads(f_path.read_text(encoding="utf-8"))
                    for it in items:
                        it["agent_id"] = "ux_ui"
                        it["agent_name"] = "تجربة المستخدم (UX/UI)"
                        findings.append(it)
                except Exception:
                    pass

        # 3. Content Marketing
        if not agent_filter or agent_filter == "content_marketing":
            for f_path in run_dir.glob("analysis/content/*/findings.json"):
                try:
                    items = json.loads(f_path.read_text(encoding="utf-8"))
                    for it in items:
                        it["agent_id"] = "content_marketing"
                        it["agent_name"] = "المحتوى والتسويق (Content)"
                        findings.append(it)
                except Exception:
                    pass

        # 4. Technical SEO
        if not agent_filter or agent_filter == "technical_seo":
            for f_path in run_dir.glob("analysis/technical-seo/*/findings.json"):
                try:
                    items = json.loads(f_path.read_text(encoding="utf-8"))
                    for it in items:
                        it["agent_id"] = "technical_seo"
                        it["agent_name"] = "SEO التقني (Technical SEO)"
                        findings.append(it)
                except Exception:
                    pass

        # 5. Competitor Intelligence
        if not agent_filter or agent_filter == "competitor_intelligence":
            for f_path in run_dir.glob("analysis/competitors/*/findings.json"):
                try:
                    items = json.loads(f_path.read_text(encoding="utf-8"))
                    for it in items:
                        it["agent_id"] = "competitor_intelligence"
                        it["agent_name"] = "استخبارات المنافسين (Competitor Intelligence)"
                        findings.append(it)
                except Exception:
                    pass

        # 6. Security & Privacy Intelligence (Phase 09)
        if not agent_filter or agent_filter == "security_privacy":
            for f_path in run_dir.glob("analysis/security-privacy/*/findings.json"):
                try:
                    items = json.loads(f_path.read_text(encoding="utf-8"))
                    for it in items:
                        it["agent_id"] = "security_privacy"
                        it["agent_name"] = "الأمان والخصوصية (Security & Privacy)"
                        findings.append(it)
                except Exception:
                    pass

        # 7. Web Accessibility & WCAG 2.2 (Phase 10)
        if not agent_filter or agent_filter == "accessibility":
            for f_path in run_dir.glob("analysis/accessibility/*/findings.json"):
                try:
                    items = json.loads(f_path.read_text(encoding="utf-8"))
                    for it in items:
                        it["agent_id"] = "accessibility"
                        it["agent_name"] = "إمكانية الوصول (Accessibility)"
                        findings.append(it)
                except Exception:
                    pass

        # 8. Strategic Intelligence & Synthesis (Phase 11)
        if not agent_filter or agent_filter == "strategic_intelligence":
            for f_path in run_dir.glob("analysis/strategic-intelligence/*/unified-findings.json"):
                try:
                    items = json.loads(f_path.read_text(encoding="utf-8"))
                    for it in items:
                        it["agent_id"] = "strategic_intelligence"
                        it["agent_name"] = "الذكاء الاستراتيجي (Strategic Intelligence)"
                        findings.append(it)
                except Exception:
                    pass

        return findings

    def get_recommendations(self, run_id: str, priority_filter: Optional[str] = None) -> list[dict[str, Any]]:
        """Aggregate prioritized recommendations across all completed analysis stages."""
        run_dir = self._get_run_dir(run_id)
        recommendations: list[dict[str, Any]] = []

        # Search all recommendations.json
        rec_files = list(run_dir.glob("visual/*/analysis/*/*/recommendations.json")) + list(
            run_dir.glob("analysis/*/*/recommendations.json")
        )
        for rf in rec_files:
            stage_hint = (
                "strategic_intelligence"
                if "strategic-intelligence" in str(rf)
                else (
                    "accessibility"
                    if "accessibility" in str(rf)
                    else (
                        "security_privacy"
                        if "security-privacy" in str(rf)
                        else (
                            "competitor_intelligence"
                            if "competitors" in str(rf)
                            else (
                                "technical_seo"
                                if "technical-seo" in str(rf)
                                else (
                                    "content_marketing"
                                    if "content" in str(rf)
                                    else ("ux_ui" if "ux-ui" in str(rf) else "visual_identity")
                                )
                            )
                        )
                    )
                )
            )
            try:
                items = json.loads(rf.read_text(encoding="utf-8"))
                for it in items:
                    it["stage_id"] = stage_hint
                    if priority_filter and str(it.get("priority", "")).lower() != priority_filter.lower():
                        continue
                    recommendations.append(it)
            except Exception:
                pass

        # Sort P1, P2, P3
        priority_order = {"p1": 1, "p2": 2, "p3": 3, "high": 1, "medium": 2, "low": 3}
        recommendations.sort(key=lambda r: priority_order.get(str(r.get("priority", "")).lower(), 99))
        return recommendations

    def get_report(self, run_id: str, stage_id: str, format_type: str = "markdown") -> dict[str, Any]:
        """Fetch report content (Markdown or JSON) for an analyzed stage."""
        run_dir = self._get_run_dir(run_id)
        pattern = {
            "visual_identity": "visual/*/analysis/visual-identity/*",
            "ux_ui": "visual/*/analysis/ux-ui/*",
            "content_marketing": "analysis/content/*",
            "technical_seo": "analysis/technical-seo/*",
            "competitor_intelligence": "analysis/competitors/*",
            "security_privacy": "analysis/security-privacy/*",
            "accessibility": "analysis/accessibility/*",
            "strategic_intelligence": "analysis/strategic-intelligence/*",
        }.get(stage_id)

        if not pattern:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"No reports available for stage '{stage_id}'."
            )

        matches = list(run_dir.glob(pattern))
        if not matches:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"No completed report found for '{stage_id}'."
            )

        target_dir = matches[-1]
        target_file = target_dir / ("report.md" if format_type == "markdown" else "analysis.json")
        if not target_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Report file '{target_file.name}' not found."
            )

        content = target_file.read_text(encoding="utf-8")
        return {
            "run_id": run_id,
            "stage_id": stage_id,
            "format": format_type,
            "filename": target_file.name,
            "content": content,
        }
