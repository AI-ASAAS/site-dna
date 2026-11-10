"""Source adapters for ingesting and normalizing artifacts across Site DNA Phases 01–11."""

import hashlib
import json
from pathlib import Path
from typing import Any, Optional

from site_dna.core.logging import get_logger
from site_dna.schemas.final_report import (
    ReportFindingItem,
    ReportProvenance,
    ReportRecommendationItem,
    ReportRoadmapWaveItem,
)

logger = get_logger("reporting.source_adapters")


def compute_sha256(path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class SourceArtifactsAdapter:
    """Adapter that reads and normalizes all available upstream stage artifacts."""

    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.crawl_run_id = run_dir.name

    def get_discovery_info(self) -> tuple[dict[str, Any], Optional[ReportProvenance]]:
        crawl_file = self.run_dir / "crawl.json"
        if not crawl_file.exists():
            return {}, None
        try:
            data = json.loads(crawl_file.read_text(encoding="utf-8"))
            prov = ReportProvenance(
                stage_id="discovery",
                agent_id="discovery_crawler",
                source_run_id=self.crawl_run_id,
                artifact_path=str(crawl_file),
                artifact_sha256=compute_sha256(crawl_file),
                captured_at=data.get("crawl_timestamp"),
                status="completed",
            )
            return data, prov
        except Exception as e:
            logger.warning("Failed parsing crawl.json: %s", e)
            return {}, None

    def get_visual_capture_data(self) -> tuple[dict[str, Any], Optional[ReportProvenance], dict[str, str]]:
        """Returns visual capture manifest data, provenance, and base64 screenshots."""
        vis_dir = self.run_dir / "visual"
        if not vis_dir.exists():
            return {}, None, {}

        subdirs = [d for d in vis_dir.iterdir() if d.is_dir()]
        if not subdirs:
            return {}, None, {}

        vis_run = sorted(subdirs, key=lambda d: d.stat().st_mtime, reverse=True)[0]
        manifest_file = vis_run / "manifest.json"
        screenshots_b64: dict[str, str] = {}

        if not manifest_file.exists():
            return {}, None, screenshots_b64

        try:
            mdata = json.loads(manifest_file.read_text(encoding="utf-8"))
            prov = ReportProvenance(
                stage_id="visual_capture",
                agent_id="visual_collector",
                source_run_id=vis_run.name,
                artifact_path=str(manifest_file),
                artifact_sha256=compute_sha256(manifest_file),
                captured_at=mdata.get("captured_at"),
                status="completed",
            )

            # Discover screenshots
            for shot in mdata.get("screenshots", []):
                file_path = shot.get("file_path")
                vtype = shot.get("viewport", {}).get("name", "desktop").lower()
                if file_path:
                    abs_path = self.run_dir / file_path if not Path(file_path).is_absolute() else Path(file_path)
                    if abs_path.exists():
                        import base64
                        b64 = base64.b64encode(abs_path.read_bytes()).decode("ascii")
                        if "mobile" in vtype:
                            screenshots_b64["mobile"] = f"data:image/png;base64,{b64}"
                        else:
                            screenshots_b64["desktop"] = f"data:image/png;base64,{b64}"

            return mdata, prov, screenshots_b64
        except Exception as e:
            logger.warning("Failed reading visual manifest: %s", e)
            return {}, None, screenshots_b64

    def extract_stage_findings_and_recs(
        self, stage_id: str, subpath: str, agent_id: str
    ) -> tuple[list[ReportFindingItem], list[ReportRecommendationItem], Optional[float], Optional[ReportProvenance]]:
        """Generic extractor for analysis stages."""
        stage_base = self.run_dir / subpath
        if not stage_base.exists():
            return [], [], None, None

        subdirs = [d for d in stage_base.iterdir() if d.is_dir()]
        latest_dir = sorted(subdirs, key=lambda d: d.stat().st_mtime, reverse=True)[0] if subdirs else stage_base
        analysis_file = latest_dir / "analysis.json"
        if not analysis_file.exists():
            return [], [], None, None

        try:
            data = json.loads(analysis_file.read_text(encoding="utf-8"))
            prov = ReportProvenance(
                stage_id=stage_id,
                agent_id=agent_id,
                source_run_id=latest_dir.name,
                artifact_path=str(analysis_file),
                artifact_sha256=compute_sha256(analysis_file),
                captured_at=data.get("created_at") or data.get("timestamp"),
                status="completed",
            )

            score = data.get("overall_score")
            if score is None and isinstance(data.get("scores"), dict):
                score = data["scores"].get("overall_score")

            findings: list[ReportFindingItem] = []
            for f in data.get("findings", []):
                sev = f.get("severity", "medium").lower()
                if sev not in ("critical", "high", "medium", "low", "info"):
                    sev = "medium"
                findings.append(
                    ReportFindingItem(
                        finding_id=f.get("finding_id", f.get("id", f"{stage_id}-{len(findings)+1}")),
                        title=f.get("title", f.get("name", "Finding")),
                        title_ar=f.get("title_ar"),
                        description=f.get("description", ""),
                        description_ar=f.get("description_ar"),
                        domain=f.get("domain", stage_id),
                        severity=sev,
                        source_agent=agent_id,
                        evidence_ids=f.get("evidence_ids", []),
                        affected_urls=f.get("affected_urls", []),
                    )
                )

            recs: list[ReportRecommendationItem] = []
            for r in data.get("recommendations", []):
                prio = r.get("priority", "P1").upper()
                if prio not in ("P0", "P1", "P2", "P3"):
                    prio = "P1"
                recs.append(
                    ReportRecommendationItem(
                        action_id=r.get("recommendation_id", r.get("action_id", f"REC-{len(recs)+1}")),
                        title=r.get("title", "Recommendation"),
                        title_ar=r.get("title_ar"),
                        description=r.get("description", ""),
                        description_ar=r.get("description_ar"),
                        priority=prio,
                        wave_number=r.get("wave_number", 1),
                        owner_role=r.get("suggested_owner_role", r.get("owner", "Engineer")),
                        effort=r.get("estimated_effort", r.get("effort", "medium")),
                        impact=r.get("impact_category", r.get("impact", "high")),
                        status=r.get("status", "proposed"),
                        verification_method=r.get("verification_method"),
                        verification_method_ar=r.get("verification_method_ar"),
                    )
                )

            return findings, recs, score, prov
        except Exception as e:
            logger.warning("Error parsing %s: %s", analysis_file, e)
            return [], [], None, None

    def get_strategic_intelligence_data(
        self,
    ) -> tuple[
        list[ReportFindingItem],
        list[ReportRecommendationItem],
        list[ReportRoadmapWaveItem],
        Optional[float],
        Optional[str],
        Optional[ReportProvenance],
        dict[str, Any],
    ]:
        """Load Phase 11 strategic roadmap and unified findings."""
        strat_base = self.run_dir / "analysis" / "strategic-intelligence"
        if not strat_base.exists():
            return [], [], [], None, None, None, {}

        subdirs = [d for d in strat_base.iterdir() if d.is_dir()]
        if not subdirs:
            return [], [], [], None, None, None, {}

        latest_dir = sorted(subdirs, key=lambda d: d.stat().st_mtime, reverse=True)[0]
        analysis_file = latest_dir / "analysis.json"
        roadmap_file = latest_dir / "roadmap.json"
        backlog_file = latest_dir / "action-backlog.json"

        if not analysis_file.exists():
            return [], [], [], None, None, None, {}

        try:
            adata = json.loads(analysis_file.read_text(encoding="utf-8"))
            prov = ReportProvenance(
                stage_id="strategic_intelligence",
                agent_id="strategic_intelligence_agent",
                source_run_id=latest_dir.name,
                artifact_path=str(analysis_file),
                artifact_sha256=compute_sha256(analysis_file),
                captured_at=adata.get("created_at"),
                status="completed",
            )

            stats = adata.get("statistics", {})
            strat_index = stats.get("strategic_index")
            strat_label = stats.get("index_label_ar")

            # Unified findings
            unified_findings: list[ReportFindingItem] = []
            for uf in adata.get("unified_findings", []):
                sev = uf.get("severity", "medium").lower()
                if sev not in ("critical", "high", "medium", "low", "info"):
                    sev = "medium"
                unified_findings.append(
                    ReportFindingItem(
                        finding_id=uf.get("unified_finding_id", f"UF-{len(unified_findings)+1}"),
                        canonical_id=uf.get("unified_finding_id"),
                        title=uf.get("title", "Unified Finding"),
                        title_ar=uf.get("title_ar"),
                        description=uf.get("description", ""),
                        description_ar=uf.get("description_ar"),
                        domain=uf.get("domain", "strategic"),
                        severity=sev,
                        source_agent="strategic_intelligence",
                        evidence_ids=uf.get("evidence_ids", []),
                        affected_urls=uf.get("affected_pages", []),
                    )
                )

            # Action backlog
            actions_raw = (
                json.loads(backlog_file.read_text(encoding="utf-8"))
                if backlog_file.exists()
                else adata.get("actions", adata.get("action_backlog", []))
            )

            actions: list[ReportRecommendationItem] = []
            for act in actions_raw:
                prio = act.get("priority", "P1").upper()
                if prio not in ("P0", "P1", "P2", "P3"):
                    prio = "P1"
                actions.append(
                    ReportRecommendationItem(
                        action_id=act.get("action_id", f"ACT-{len(actions)+1}"),
                        title=act.get("title", "Roadmap Action"),
                        title_ar=act.get("title_ar"),
                        description=act.get("description", ""),
                        description_ar=act.get("description_ar"),
                        priority=prio,
                        wave_number=act.get("wave_number", 1),
                        owner_role=act.get("suggested_owner_role", act.get("suggested_owner", "Engineer")),
                        effort=act.get("estimated_effort", act.get("effort_estimate", "medium")),
                        impact=act.get("impact_category", "high"),
                        status=act.get("status", "proposed"),
                        verification_method=act.get("verification_method"),
                        verification_method_ar=act.get("verification_method_ar"),
                    )
                )

            # Roadmap waves
            waves: list[ReportRoadmapWaveItem] = []
            if roadmap_file.exists():
                rdata = json.loads(roadmap_file.read_text(encoding="utf-8"))
                for w in rdata:
                    w_actions = [
                        ReportRecommendationItem(
                            action_id=wa.get("action_id", "ACT"),
                            title=wa.get("title", ""),
                            title_ar=wa.get("title_ar"),
                            description=wa.get("description", ""),
                            description_ar=wa.get("description_ar"),
                            priority=wa.get("priority", "P1"),
                            wave_number=w.get("wave_number", 1),
                            owner_role=wa.get("suggested_owner_role", "Engineer"),
                            effort=wa.get("estimated_effort", "medium"),
                            impact=wa.get("impact_category", "high"),
                            status=wa.get("status", "proposed"),
                            verification_method=wa.get("verification_method"),
                            verification_method_ar=wa.get("verification_method_ar"),
                        )
                        for wa in w.get("actions", [])
                    ]
                    waves.append(
                        ReportRoadmapWaveItem(
                            wave_number=w.get("wave_number", 1),
                            name=w.get("name", f"Wave {w.get('wave_number')}"),
                            name_ar=w.get("name_ar", f"الموجة {w.get('wave_number')}"),
                            timeframe=w.get("timeframe", "0-2 weeks"),
                            description=w.get("description", ""),
                            description_ar=w.get("description_ar"),
                            actions=w_actions,
                        )
                    )

            return unified_findings, actions, waves, strat_index, strat_label, prov, adata
        except Exception as e:
            logger.warning("Failed parsing strategic intelligence: %s", e)
            return [], [], [], None, None, None, {}

    def get_domain_audits(self) -> dict[str, Any]:
        """Harvest deep structured domain audit deliverables from all phases."""
        audits: dict[str, Any] = {}

        # 1. Discovery
        cdata, _ = self.get_discovery_info()
        if cdata:
            pages = cdata.get("pages", [])
            audits["discovery"] = {
                "initial_url": cdata.get("website_info", {}).get("initial_url", ""),
                "canonical_origin": cdata.get("website_info", {}).get("canonical_origin", ""),
                "total_pages": len(pages),
                "crawl_timestamp": cdata.get("crawl_timestamp", ""),
                "pages_sample": [
                    {
                        "url": p.get("url", ""),
                        "title": p.get("title", ""),
                        "status_code": p.get("status_code", 200),
                        "load_time_ms": p.get("load_time_ms", 0),
                    }
                    for p in pages[:8]
                ],
            }

        # 2. Security & Privacy
        sec_file = list(self.run_dir.glob("analysis/security-privacy/*/analysis.json"))
        if sec_file:
            try:
                sdata = json.loads(sec_file[0].read_text(encoding="utf-8"))
                audits["security_privacy"] = {
                    "scores": sdata.get("scores", {}),
                    "https": sdata.get("https_assessment", {}),
                    "tls": sdata.get("tls_observations", {}),
                    "headers": sdata.get("security_headers_assessment", {}),
                    "csp": sdata.get("csp_assessment", {}),
                    "cookies": sdata.get("cookie_security_assessment", {}),
                    "privacy": sdata.get("privacy_signal_assessment", {}),
                    "findings_count": len(sdata.get("findings", [])),
                }
            except Exception as e:
                logger.warning("Error loading security audit: %s", e)

        # 3. Technical SEO
        seo_file = list(self.run_dir.glob("analysis/technical-seo/*/analysis.json"))
        if seo_file:
            try:
                tdata = json.loads(seo_file[0].read_text(encoding="utf-8"))
                audits["technical_seo"] = {
                    "overall_score": tdata.get("overall_score", 90),
                    "crawlability": tdata.get("crawlability", {}),
                    "indexability": tdata.get("indexability", {}),
                    "robots": tdata.get("robots", {}),
                    "sitemap": tdata.get("sitemap", {}),
                    "metadata": tdata.get("metadata", {}),
                    "structured_data": tdata.get("structured_data", {}),
                    "core_web_vitals": tdata.get("core_web_vitals", {}),
                    "performance": tdata.get("performance", []),
                    "findings_count": len(tdata.get("findings", [])),
                }
            except Exception as e:
                logger.warning("Error loading SEO audit: %s", e)

        # 4. Accessibility
        a11y_file = list(self.run_dir.glob("analysis/accessibility/*/analysis.json"))
        if a11y_file:
            try:
                adata = json.loads(a11y_file[0].read_text(encoding="utf-8"))
                audits["accessibility"] = {
                    "scores": adata.get("scores", {}),
                    "wcag_criteria": adata.get("wcag_criteria", []),
                    "contrast": adata.get("contrast", {}),
                    "keyboard_focus": adata.get("keyboard_focus", {}),
                    "semantics": adata.get("semantics", {}),
                    "images_media": adata.get("images_media", {}),
                    "manual_review_tasks": adata.get("manual_review_tasks", []),
                    "findings_count": len(adata.get("findings", [])),
                }
            except Exception as e:
                logger.warning("Error loading Accessibility audit: %s", e)

        # 5. Competitor Intelligence
        comp_file = list(self.run_dir.glob("analysis/competitors/*/analysis.json"))
        if comp_file:
            try:
                cdata = json.loads(comp_file[0].read_text(encoding="utf-8"))
                audits["competitors"] = {
                    "primary_site": cdata.get("primary_site", {}),
                    "competitor_sites": cdata.get("competitor_sites", []),
                    "profiles": cdata.get("profiles", []),
                    "feature_matrix": cdata.get("feature_matrix", []),
                    "pricing_comparison": cdata.get("pricing_comparison", []),
                    "gaps": cdata.get("gaps", []),
                    "opportunities": cdata.get("opportunities", []),
                    "scores": cdata.get("scores", {}),
                }
            except Exception as e:
                logger.warning("Error loading Competitor audit: %s", e)

        # 6. Content & Marketing
        cnt_file = list(self.run_dir.glob("analysis/content*/*/analysis.json"))
        if cnt_file:
            try:
                cndata = json.loads(cnt_file[0].read_text(encoding="utf-8"))
                audits["content_marketing"] = {
                    "overall_score": cndata.get("overall_score"),
                    "value_prop": cndata.get("value_proposition", {}),
                    "tone": cndata.get("messaging_tone", {}),
                    "audience": cndata.get("target_audience_alignment", {}),
                    "inventory": cndata.get("content_inventory", {}),
                    "findings_count": len(cndata.get("findings", [])),
                }
            except Exception as e:
                logger.warning("Error loading Content audit: %s", e)

        return audits
