"""Evidence Catalog builder linking every finding and recommendation to verifiable technical evidence."""

from pathlib import Path
from typing import Any

from site_dna.schemas.final_report import ReportEvidenceItem


class EvidenceCatalogBuilder:
    """Extracts, indexes, and structures evidence items from run artifacts."""

    def __init__(self, run_dir: Path, target_url: str):
        self.run_dir = run_dir
        self.target_url = target_url

    def build_catalog(self) -> list[ReportEvidenceItem]:
        catalog: list[ReportEvidenceItem] = []

        # 1. Visual Capture Screenshots
        vis_dir = self.run_dir / "visual"
        if vis_dir.exists():
            for vis_run in vis_dir.iterdir():
                manifest_file = vis_run / "manifest.json"
                if manifest_file.exists():
                    try:
                        import json
                        mdata = json.loads(manifest_file.read_text(encoding="utf-8"))
                        for shot in mdata.get("screenshots", []):
                            catalog.append(
                                ReportEvidenceItem(
                                    evidence_id=shot.get("screenshot_id", f"EVD-SHOT-{len(catalog)+1}"),
                                    source_agent="visual_capture",
                                    observation_type="browser_screenshot",
                                    target_url=shot.get("url", self.target_url),
                                    capture_date=mdata.get("captured_at"),
                                    details={
                                        "viewport": shot.get("viewport", {}).get("name", "desktop"),
                                        "width": shot.get("viewport", {}).get("width"),
                                        "height": shot.get("viewport", {}).get("height"),
                                        "file_path": shot.get("file_path"),
                                    },
                                )
                            )
                    except Exception:
                        pass

        # 2. Security Headers Evidence
        sec_dir = self.run_dir / "analysis" / "security-privacy"
        if sec_dir.exists():
            for sdir in sec_dir.iterdir():
                afile = sdir / "analysis.json"
                if afile.exists():
                    try:
                        import json
                        sdata = json.loads(afile.read_text(encoding="utf-8"))
                        hobs = sdata.get("header_observations", [])
                        for h in hobs:
                            catalog.append(
                                ReportEvidenceItem(
                                    evidence_id=f"EVD-SEC-{h.get('header_name', 'HEADER').lower()}",
                                    source_agent="security_privacy",
                                    observation_type="http_security_header",
                                    target_url=self.target_url,
                                    details={
                                        "header_name": h.get("header_name"),
                                        "status": h.get("status"),
                                        "observed_value": h.get("observed_value"),
                                    },
                                )
                            )
                    except Exception:
                        pass

        # 3. Accessibility WCAG Evidence
        a11y_dir = self.run_dir / "analysis" / "accessibility"
        if a11y_dir.exists():
            for adir in a11y_dir.iterdir():
                afile = adir / "analysis.json"
                if afile.exists():
                    try:
                        import json
                        adata = json.loads(afile.read_text(encoding="utf-8"))
                        for crit in adata.get("wcag_criteria", []):
                            catalog.append(
                                ReportEvidenceItem(
                                    evidence_id=f"EVD-WCAG-{crit.get('criterion_id', 'CRIT')}",
                                    source_agent="accessibility",
                                    observation_type="wcag_criterion_evaluation",
                                    target_url=self.target_url,
                                    details={
                                        "criterion_id": crit.get("criterion_id"),
                                        "level": crit.get("level"),
                                        "status": crit.get("status"),
                                        "violations_count": crit.get("violations_count", 0),
                                    },
                                )
                            )
                    except Exception:
                        pass

        # 4. Technical SEO Performance Evidence
        seo_dir = self.run_dir / "analysis" / "technical-seo"
        if seo_dir.exists():
            for sdir in seo_dir.iterdir():
                afile = sdir / "analysis.json"
                if afile.exists():
                    try:
                        import json
                        seodata = json.loads(afile.read_text(encoding="utf-8"))
                        for metric, val in seodata.get("performance_metrics", {}).items():
                            catalog.append(
                                ReportEvidenceItem(
                                    evidence_id=f"EVD-PERF-{metric.upper()}",
                                    source_agent="technical_seo",
                                    observation_type="core_web_vitals_measurement",
                                    target_url=self.target_url,
                                    details={"metric": metric, "value": val},
                                )
                            )
                    except Exception:
                        pass

        return catalog
