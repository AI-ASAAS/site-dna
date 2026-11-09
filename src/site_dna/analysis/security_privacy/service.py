"""Master Orchestration Service for Site DNA Phase 09 — Security, Privacy & Trust Intelligence."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from site_dna.analysis.security_privacy.browser_isolation import BrowserIsolationAnalyzer
from site_dna.analysis.security_privacy.client_side_observations import ClientSideObservationsAnalyzer
from site_dna.analysis.security_privacy.consent_observations import ConsentObservationsAnalyzer
from site_dna.analysis.security_privacy.context_builder import SecurityPrivacyContextBuilder
from site_dna.analysis.security_privacy.cookie_analyzer import CookieSecurityAnalyzer
from site_dna.analysis.security_privacy.csp_analyzer import CSPAnalyzer
from site_dna.analysis.security_privacy.evidence_validator import SecurityEvidenceValidator
from site_dna.analysis.security_privacy.https_analyzer import HTTPSAnalyzer
from site_dna.analysis.security_privacy.mixed_content import MixedContentAnalyzer
from site_dna.analysis.security_privacy.privacy_signals import PrivacySignalsAnalyzer
from site_dna.analysis.security_privacy.recommendations import SecurityRecommendationEngine
from site_dna.analysis.security_privacy.report_builder import SecurityReportBuilder
from site_dna.analysis.security_privacy.risk_assessment import RiskAssessmentEngine
from site_dna.analysis.security_privacy.scoring import SecurityScoringEngine
from site_dna.analysis.security_privacy.security_headers import SecurityHeadersAnalyzer
from site_dna.analysis.security_privacy.third_party_resources import ThirdPartyResourceAnalyzer
from site_dna.analysis.security_privacy.tls_observations import TLSObservationsAnalyzer
from site_dna.analysis.security_privacy.trust_signals import TrustSignalsAnalyzer
from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.schemas.security_privacy import (
    SecurityAnalysisStatistics,
    SecurityPrivacyAnalysisRequest,
    SecurityPrivacyReport,
)

logger = get_logger("analysis.security_privacy.service")


class SecurityPrivacyService:
    """Master service executing passive security, privacy, and digital trust intelligence."""

    def __init__(self, settings: Optional[Settings] = None, base_dir: Path | str = "runs"):
        self.settings = settings or get_settings()
        self.base_dir = Path(base_dir)
        self.context_builder = SecurityPrivacyContextBuilder(base_dir=self.base_dir, settings=self.settings)
        self.https_analyzer = HTTPSAnalyzer()
        self.tls_analyzer = TLSObservationsAnalyzer()
        self.headers_analyzer = SecurityHeadersAnalyzer()
        self.csp_analyzer = CSPAnalyzer()
        self.cookie_analyzer = CookieSecurityAnalyzer()
        self.mixed_analyzer = MixedContentAnalyzer()
        self.browser_isolation_analyzer = BrowserIsolationAnalyzer()
        self.client_analyzer = ClientSideObservationsAnalyzer()
        self.third_party_analyzer = ThirdPartyResourceAnalyzer()
        self.privacy_analyzer = PrivacySignalsAnalyzer()
        self.consent_analyzer = ConsentObservationsAnalyzer()
        self.trust_analyzer = TrustSignalsAnalyzer()
        self.risk_engine = RiskAssessmentEngine()
        self.validator = SecurityEvidenceValidator()
        self.scoring_engine = SecurityScoringEngine()
        self.recommendations_engine = SecurityRecommendationEngine()
        self.report_builder = SecurityReportBuilder()

    async def analyze_security(self, request: SecurityPrivacyAnalysisRequest) -> SecurityPrivacyReport:
        """Run the comprehensive passive security and privacy intelligence audit."""
        start_time = time.perf_counter()
        logger.info("Initiating Phase 09 Security & Privacy audit for crawl_run_id=%s", request.crawl_run_id)

        # 1. Build and validate context
        context = self.context_builder.build_context(request)
        page_records = context.page_records

        # Load raw crawl dataset for deep DOM/text checks
        runs_dir = self.base_dir
        crawl_file = runs_dir / request.crawl_run_id / "crawl.json"
        crawl_data: dict[str, Any] = {}
        if crawl_file.exists():
            try:
                crawl_data = json.loads(crawl_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        # 2. Run domain analyzers
        https_ast = self.https_analyzer.analyze(page_records)
        tls_ast = self.tls_analyzer.analyze(context.target_url, page_records, crawl_data)
        headers_ast = self.headers_analyzer.analyze(page_records)
        csp_ast = self.csp_analyzer.analyze(page_records)
        cookie_ast = self.cookie_analyzer.analyze(page_records)
        mixed_ast = self.mixed_analyzer.analyze(page_records)
        isolation_ast = self.browser_isolation_analyzer.analyze(page_records)
        client_ast = self.client_analyzer.analyze(page_records, crawl_data)
        third_party_ast = self.third_party_analyzer.analyze(page_records)
        privacy_ast = self.privacy_analyzer.analyze(page_records, crawl_data)
        consent_ast = self.consent_analyzer.analyze(page_records, crawl_data)
        trust_ast = self.trust_analyzer.analyze(page_records, crawl_data)

        # 3. Formulate findings
        raw_findings = self.risk_engine.synthesize_findings(
            page_records=page_records,
            https_assessment=https_ast,
            headers_assessment=headers_ast,
            csp_assessment=csp_ast,
            cookie_assessment=cookie_ast,
            mixed_content_assessment=mixed_ast,
            browser_isolation_assessment=isolation_ast,
            privacy_signal_assessment=privacy_ast,
        )

        # 4. Anti-hallucination and evidence validation
        all_evidence_ids = (
            set(https_ast.evidence_ids)
            | set(tls_ast.evidence_ids)
            | set(csp_ast.evidence_ids)
            | set(cookie_ast.evidence_ids)
            | set(mixed_ast.evidence_ids)
            | set(isolation_ast.evidence_ids)
            | set(client_ast.evidence_ids)
            | set(third_party_ast.evidence_ids)
            | set(privacy_ast.evidence_ids)
            | set(consent_ast.evidence_ids)
            | set(trust_ast.evidence_ids)
        )
        for h in headers_ast.header_records:
            all_evidence_ids.update(h.evidence_ids)

        validated_findings, quarantined = self.validator.validate_findings(raw_findings, all_evidence_ids)
        if quarantined:
            logger.info("Quarantined %d ungrounded findings during evidence validation.", len(quarantined))

        # 5. Compute scores
        scores = self.scoring_engine.compute_scores(
            https_assessment=https_ast,
            headers_assessment=headers_ast,
            csp_assessment=csp_ast,
            cookie_assessment=cookie_ast,
            mixed_content_assessment=mixed_ast,
            browser_isolation_assessment=isolation_ast,
            client_side_observation=client_ast,
            privacy_signal_assessment=privacy_ast,
            trust_signal_assessment=trust_ast,
        )

        # 6. Derive recommendations
        recommendations = self.recommendations_engine.derive_recommendations(validated_findings)

        # 7. Optional CrewAI Flow enrichment (strictly Gemini 3.6 Flash)
        ai_status = "offline_deterministic" if request.deterministic_only or request.offline_mode else "completed"
        ai_calls = 0
        if not request.deterministic_only and not request.offline_mode and self.settings.is_gemini_configured():
            try:
                from site_dna.flows.security_privacy_flow import SecurityPrivacyFlow

                flow = SecurityPrivacyFlow(settings=self.settings)
                flow_result = await flow.run_ai_interpretation(
                    context=context,
                    findings=validated_findings,
                    scores=scores,
                )
                if flow_result:
                    ai_calls = 1
                    ai_status = "completed"
            except Exception as e:
                logger.warning("CrewAI Flow execution bypassed or quota blocked: %s", e)
                ai_status = "quota_blocked" if "quota" in str(e).lower() else "offline_deterministic"

        # 8. Telemetry and statistics
        duration_ms = (time.perf_counter() - start_time) * 1000
        sev_counts: dict[str, int] = {}
        for f in validated_findings:
            sev_counts[f.severity] = sev_counts.get(f.severity, 0) + 1

        prio_counts: dict[str, int] = {}
        for r in recommendations:
            prio_counts[r.priority] = prio_counts.get(r.priority, 0) + 1

        statistics = SecurityAnalysisStatistics(
            pages_assessed=len(page_records),
            total_headers_analyzed=headers_ast.total_headers_checked,
            total_cookies_analyzed=cookie_ast.total_cookies_observed,
            total_resources_analyzed=mixed_ast.insecure_references_count + third_party_ast.total_third_party_requests,
            total_third_party_origins=third_party_ast.unique_third_party_origins,
            findings_count_by_severity=sev_counts,
            recommendations_count_by_priority=prio_counts,
            execution_duration_ms=duration_ms,
            ai_calls_made=ai_calls,
            ai_status=ai_status,  # type: ignore
            model_identifier=self.settings.get_effective_security_model(),
        )

        report = SecurityPrivacyReport(
            security_run_id=context.security_run_id,
            crawl_run_id=request.crawl_run_id,
            visual_run_id=request.visual_run_id,
            target_url=context.target_url,
            site_origin=context.site_origin,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            analysis_status="completed" if ai_status in ("completed", "offline_deterministic") else "partial",
            model_name=self.settings.get_effective_security_model(),
            https_assessment=https_ast,
            tls_observations=tls_ast,
            security_headers_assessment=headers_ast,
            csp_assessment=csp_ast,
            cookie_security_assessment=cookie_ast,
            mixed_content_assessment=mixed_ast,
            browser_isolation_assessment=isolation_ast,
            client_side_observation=client_ast,
            third_party_resource_assessment=third_party_ast,
            privacy_signal_assessment=privacy_ast,
            consent_observation=consent_ast,
            trust_signal_assessment=trust_ast,
            scores=scores,
            findings=validated_findings,
            recommendations=recommendations,
            statistics=statistics,
        )

        # 9. Persist artifacts
        if request.save_results:
            self._save_artifacts(report)

        logger.info(
            "Phase 09 Security & Privacy audit completed in %.1f ms with score %s",
            duration_ms,
            scores.overall_score,
        )
        return report

    def _save_artifacts(self, report: SecurityPrivacyReport) -> Path:
        """Persist structured JSON files and Arabic Markdown report to disk."""
        runs_dir = self.base_dir
        out_dir = runs_dir / report.crawl_run_id / "analysis" / "security-privacy" / report.security_run_id
        out_dir.mkdir(parents=True, exist_ok=True)

        # Generate markdown report
        md_content = self.report_builder.build_markdown_report(report)
        (out_dir / "report.md").write_text(md_content, encoding="utf-8")

        # Full analysis.json
        (out_dir / "analysis.json").write_text(report.model_dump_json(indent=2), encoding="utf-8")

        # Modular artifacts
        (out_dir / "findings.json").write_text(
            json.dumps([f.model_dump() for f in report.findings], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (out_dir / "recommendations.json").write_text(
            json.dumps([r.model_dump() for r in report.recommendations], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (out_dir / "security-headers.json").write_text(
            report.security_headers_assessment.model_dump_json(indent=2),
            encoding="utf-8",
        )
        (out_dir / "cookie-security.json").write_text(
            report.cookie_security_assessment.model_dump_json(indent=2),
            encoding="utf-8",
        )
        (out_dir / "execution-summary.json").write_text(
            report.statistics.model_dump_json(indent=2),
            encoding="utf-8",
        )

        return out_dir
