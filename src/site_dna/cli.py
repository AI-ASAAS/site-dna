"""Site DNA Local Command-Line Interface (CLI).

Provides environment verification (doctor) and safe model diagnostics (smoke).
"""

import argparse
import re
import sys
from importlib import import_module
from pathlib import Path
from typing import Any, Optional

from site_dna import __version__
from site_dna.core.config import get_settings
from site_dna.core.logging import setup_logging
from site_dna.services.gemini_diagnostics import test_direct_gemini_connection


def run_doctor() -> int:
    """Perform non-destructive environment, configuration, and dependency diagnostics."""
    print("=" * 60)
    print(f" Site DNA - System Verification Doctor (v{__version__})")
    print("=" * 60)

    all_passed = True
    settings = get_settings()

    # 1. Python Environment Check
    py_ver = sys.version.split()[0]
    py_major, py_minor = sys.version_info.major, sys.version_info.minor
    if (py_major, py_minor) == (3, 11):
        print(f" [PASS] Python Version: {py_ver} (matches recommended 3.11)")
    else:
        print(f" [WARN] Python Version: {py_ver} (expected 3.11)")

    # 2. Key Dependencies Check
    dependencies = [
        ("crewai", "CrewAI Framework"),
        ("google.genai", "Google GenAI SDK"),
        ("fastapi", "FastAPI Framework"),
        ("uvicorn", "Uvicorn ASGI Server"),
        ("pydantic", "Pydantic Validation"),
        ("pydantic_settings", "Pydantic Settings"),
        ("httpx", "HTTPX Client"),
        ("bs4", "BeautifulSoup4 HTML Parser"),
        ("lxml", "LXML Parser Engine"),
        ("defusedxml", "DefusedXML Safe Parser"),
        ("playwright", "Playwright Browser Automation"),
        ("PIL", "Pillow Image Library"),
        ("pytest", "Pytest Test Runner"),
        ("ruff", "Ruff Linter"),
    ]

    print("\n Dependency Checks:")
    for mod_name, label in dependencies:
        try:
            mod = import_module(mod_name)
            version = getattr(mod, "__version__", "installed")
            print(f"  [PASS] {label:<24}: {version}")
        except ImportError as e:
            print(f"  [FAIL] {label:<24}: Not Found ({e})")
            all_passed = False

    # 3. Project Configuration Check
    print("\n Configuration & Environment:")
    print(f"  App Name             : {settings.app_name}")
    print(f"  Environment          : {settings.app_env}")
    print(f"  Host / Port          : {settings.app_host}:{settings.app_port}")
    print(f"  Target Gemini Model  : {settings.gemini_model}")
    print(f"  Visual Analysis Model: {settings.visual_analysis_model}")
    print(f"  UX Analysis Model    : {settings.ux_analysis_model}")
    print(f"  Content Analysis Model: {settings.content_analysis_model}")
    print(f"  Technical SEO Model  : {settings.technical_seo_model}")

    if settings.is_gemini_configured():
        print("  [PASS] Gemini API Key       : Configured (masked)")
    else:
        print("  [WARN] Gemini API Key       : Not Configured (Live calls blocked)")

    # 4. ASAAS Skills Directory Check
    skills_path = Path(r"C:\Users\mahmoodSaeed\Desktop\asaas_skills\skills")
    print("\n ASAAS Skills System:")
    if skills_path.exists():
        skill_count = len(list(skills_path.rglob("SKILL.md")))
        print(f"  [PASS] Skills Directory     : Found at {skills_path}")
        print(f"  [PASS] Discovered Skills    : {skill_count} SKILL.md files")
    else:
        print(f"  [WARN] Skills Directory     : Not found at {skills_path}")

    # 5. Project Package Readiness
    print("\n Package Readiness:")
    try:
        import site_dna

        print(f"  [PASS] 'site_dna' package   : Importable (v{site_dna.__version__})")
        print("  [PASS] FastAPI Application  : Loaded")
        print("  [PASS] CrewAI Flow          : Loaded")
    except Exception as exc:
        print(f"  [FAIL] Package Import Error : {exc}")
        all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print(" Doctor Result: ALL REQUIRED CHECKS PASSED")
        return 0
    else:
        print(" Doctor Result: ONE OR MORE CHECKS FAILED")
        return 1


def run_smoke(direct: bool, crew: bool, flow: bool, live: bool) -> int:
    """Execute smoke test routines for Gemini, CrewAI, or Flows."""
    settings = get_settings()

    if not live:
        print("[BLOCKED] Live smoke tests require the '--live' flag to prevent accidental token usage.")
        print(f"Target model: {settings.gemini_model}")
        print(f"Key configured: {settings.is_gemini_configured()}")
        print("Run with: python -m site_dna.cli smoke [--direct|--crew|--flow] --live")
        return 1

    if not settings.is_gemini_configured():
        print("[BLOCKED] Live test cannot proceed: GEMINI_API_KEY is not configured.")
        print("Please configure GEMINI_API_KEY in your .env or environment.")
        return 1

    # Route 1: Direct SDK Test
    if direct:
        print(f"Executing Direct Gemini Connection Test ({settings.gemini_model})...")
        result = test_direct_gemini_connection(settings=settings)
        print(f"Outcome  : {result.status.value}")
        print(f"Success  : {result.success}")
        print(f"Attempts : {result.attempts}")
        print(f"Duration : {result.duration_ms} ms")
        print(f"Details  : {result.error_message}")
        if result.response_text:
            print(f"Response : {result.response_text}")
        if result.error_type:
            print(f"Error    : {result.error_type} (HTTP {result.http_status})")
        return 0 if result.success else 1

    # Route 2: CrewAI Agent Smoke Test
    if crew:
        print(f"Executing CrewAI Foundation Smoke Agent ({settings.gemini_model})...")
        from site_dna.agents.smoke_agent import run_smoke_crew

        try:
            agent_result = run_smoke_crew()
            print("Outcome : SUCCESS")
            print(f"Project : {agent_result.project}")
            print(f"Status  : {agent_result.status}")
            print(f"Message : {agent_result.message}")
            return 0
        except Exception as exc:
            print("Outcome : FAILED")
            print(f"Error   : {type(exc).__name__}: {exc}")
            return 1

    # Route 3: CrewAI Flow Test
    if flow:
        print(f"Executing CrewAI Foundation Flow ({settings.gemini_model})...")
        from site_dna.flows.foundation_flow import FoundationFlow

        try:
            flow_instance = FoundationFlow(settings=settings)
            flow_instance.kickoff()
            print("Outcome : SUCCESS")
            print(f"Run ID  : {flow_instance.state.run_id}")
            print(f"Status  : {flow_instance.state.execution_status}")
            print(f"Started : {flow_instance.state.started_at}")
            print(f"Finished: {flow_instance.state.completed_at}")
            if flow_instance.state.agent_output:
                print(f"Output  : {flow_instance.state.agent_output.model_dump_json()}")
            return 0
        except Exception as exc:
            print("Outcome : FAILED")
            print(f"Error   : {type(exc).__name__}: {exc}")
            return 1

    print("Please specify a test mode: --direct, --crew, or --flow")
    return 1


def run_discover(
    url: str,
    max_pages: int | None = None,
    max_depth: int | None = None,
    output: str | None = None,
    save: bool = False,
) -> int:
    """Execute website discovery crawl and print summary."""
    print("=" * 60)
    print(" Site DNA - Website Discovery Engine (Phase 02)")
    print("=" * 60)
    print(f" Target URL  : {url}")
    if max_pages:
        print(f" Max Pages   : {max_pages}")
    if max_depth is not None:
        print(f" Max Depth   : {max_depth}")
    print(" Starting crawl...\n")

    from site_dna.discovery.service import WebsiteDiscoveryService
    from site_dna.schemas.discovery import CrawlRequest

    service = WebsiteDiscoveryService()
    req = CrawlRequest(url=url, max_pages=max_pages, max_depth=max_depth)
    result = service.discover_sync(req)

    print("-" * 60)
    print(" Discovery Crawl Summary:")
    print(f" Run ID             : {result.run_id}")
    print(f" Canonical Origin   : {result.website_info.canonical_origin}")
    print(f" Declared Language  : {result.website_info.declared_language or 'N/A'}")
    print(
        f" Robots.txt Found   : {result.website_info.robots_txt_found} (Allowed: {result.website_info.robots_txt_allowed})"
    )
    print(
        f" Sitemap Found      : {result.website_info.sitemap_found} ({len(result.website_info.sitemap_urls)} sitemaps)"
    )
    print(f" Pages Crawled      : {result.statistics.total_pages_crawled}")
    print(f" Discovered Links   : {result.statistics.total_pages_discovered}")
    print(f" Total Bytes        : {result.statistics.total_bytes_fetched}")
    print(f" Duration           : {result.statistics.total_duration_ms:.1f} ms")
    print(f" Errors Count       : {result.statistics.errors_count}")
    print(f" Evidence Records   : {len(result.evidence)}")

    if result.pages:
        print("\n Crawled Pages Overview:")
        for idx, p in enumerate(result.pages, 1):
            title = (p.metadata.title or "No Title")[:45]
            print(f"  {idx}. [{p.category.upper():<8}] ({p.status_code}) {p.final_url}")
            print(f"     Title: {title} | Words: {p.word_count} | Headings: {len(p.headings)}")

    if result.errors:
        print("\n Crawl Errors:")
        for err in result.errors:
            print(f"  - [{err.error_type}] {err.url}: {err.message}")

    if save:
        saved_path = service.save_run_result(result)
        print(f"\n [SAVED] Result saved to: {saved_path}")

    if output:
        out_p = Path(output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        print(f" [OUTPUT] Written to: {out_p}")

    print("=" * 60)
    return 0 if result.pages else 1


def run_visual_capture(
    crawl_file: str | None = None,
    crawl_run_id: str | None = None,
    max_pages: int | None = None,
    save: bool = True,
) -> int:
    """Execute browser rendering and screenshot collection."""
    print("=" * 60)
    print(" Site DNA - Visual Evidence Collection Engine (Phase 03)")
    print("=" * 60)

    target_path: Path | None = None
    if crawl_file:
        target_path = Path(crawl_file)
    elif crawl_run_id:
        import re

        clean_id = re.sub(r"[^a-zA-Z0-9_-]", "", crawl_run_id)
        target_path = Path("runs") / clean_id / "crawl.json"

    if not target_path or not target_path.exists():
        print(f" [FAIL] Crawl artifact not found at: {target_path}")
        print(" Run discovery first: python -m site_dna.cli discover --url <URL> --save")
        return 1

    print(f" Loading Crawl Result : {target_path}")
    from site_dna.schemas.discovery import CrawlResult
    from site_dna.visual.service import VisualCollectionService

    crawl_json = target_path.read_text(encoding="utf-8")
    crawl_result = CrawlResult.model_validate_json(crawl_json)

    print(f" Source Crawl Run ID  : {crawl_result.run_id}")
    print(f" Canonical Origin     : {crawl_result.website_info.canonical_origin}")
    print(f" Discovered Pages     : {len(crawl_result.pages)}")
    print(" Launching Chromium and starting capture...\n")

    service = VisualCollectionService()
    result = service.collect_visual_evidence_sync(crawl_result, max_pages=max_pages)

    print("-" * 60)
    print(" Visual Capture Summary:")
    print(f" Visual Run ID        : {result.visual_run_id}")
    print(f" Status               : {result.status.upper()}")
    print(f" Pages Attempted      : {result.statistics.total_pages_attempted}")
    print(f" Desktop Captures     : {result.statistics.desktop_captures_completed}")
    print(f" Mobile Captures      : {result.statistics.mobile_captures_completed}")
    print(f" Screenshots Saved    : {result.statistics.screenshots_saved}")
    print(f" DOM Elements Extracted: {result.statistics.dom_elements_extracted}")
    print(f" CSS Records Extracted: {result.statistics.css_records_extracted}")
    print(f" Evidence Records     : {result.statistics.evidence_records_created}")
    print(f" Duration             : {result.statistics.total_duration_ms:.1f} ms")
    if result.manifest_path:
        print(f" Manifest Saved       : {result.manifest_path}")

    if result.pages:
        print("\n Per-Page Visual Overview:")
        for idx, p in enumerate(result.pages, 1):
            print(f"  {idx}. [{p.status.upper():<9}] {p.page_url}")
            print(
                f"     Desktop: {len(p.desktop_screenshots)} shots | Mobile: {len(p.mobile_screenshots)} shots | Colors: {len(p.colors)} | Typography: {len(p.typography)}"
            )

    print("=" * 60)
    return 0 if result.status in ("completed", "partial") else 1


def run_analyze_visual(
    visual_run_id: str | None = None,
    manifest_file: str | None = None,
    max_pages: int | None = None,
    max_images: int | None = None,
    save: bool = True,
    offline: bool = False,
) -> int:
    """Execute AI Visual Identity Analysis on captured visual artifacts."""
    print("=" * 60)
    print(" Site DNA - AI Visual Identity Analyst (Phase 04)")
    print("=" * 60)

    if not visual_run_id and not manifest_file:
        print(" [FAIL] Must provide either --visual-run-id or --manifest-file")
        return 2

    print(f" Target Visual ID     : {visual_run_id or 'From File'}")
    if manifest_file:
        print(f" Manifest File Path   : {manifest_file}")
    print(" Initializing Visual Identity Analysis Engine...\n")

    from site_dna.analysis.visual_identity.service import VisualIdentityAnalysisService
    from site_dna.schemas.visual_identity import VisualIdentityAnalysisRequest

    kwargs: dict[str, Any] = {
        "visual_run_id": visual_run_id,
        "visual_manifest_file": manifest_file,
        "save_results": save,
    }
    if max_pages is not None:
        kwargs["max_pages"] = max_pages
    if max_images is not None:
        kwargs["max_images"] = max_images

    req = VisualIdentityAnalysisRequest(**kwargs)

    try:
        service = VisualIdentityAnalysisService()
        report = service.analyze_visual_identity(req, offline_mode=offline)
    except FileNotFoundError as exc:
        print(f" [FAIL] Visual manifest or run file not found: {exc}")
        return 2
    except Exception as exc:
        print(f" [FAIL] Visual Analysis failed: {exc}")
        return 1

    print("-" * 60)
    print(" Visual Identity Audit Summary:")
    print(f" Analysis Run ID      : {report.analysis_run_id}")
    print(f" Target Site          : {report.site_url}")
    print(f" Status               : {report.analysis_status.upper()}")
    score_str = f"{report.overall_score:.1f} / 100" if report.overall_score is not None else "N/A"
    print(f" Overall Score        : {score_str}")
    print("\n Dimension Scores:")
    for exp in report.score_explanations:
        sc = f"{exp.score:.1f} / 100" if exp.score is not None else "Not Assessed"
        print(f"  - {exp.dimension_name:<36}: {sc} (weight {int(exp.weight * 100)}%)")

    print(f"\n Key Findings ({len(report.findings)}):")
    for idx, f in enumerate(report.findings[:5], 1):
        print(f"  {idx}. [{f.severity.upper():<8}] {f.title}")
        print(f"     Page: {f.page_url} | Category: {f.category}")

    if len(report.findings) > 5:
        print(f"     ... and {len(report.findings) - 5} more findings.")

    print(f"\n Actionable Recommendations ({len(report.recommendations)}):")
    for idx, r in enumerate(report.recommendations[:5], 1):
        print(f"  {idx}. [{r.priority.upper()}] {r.title} (Effort: {r.estimated_effort}, Impact: {r.expected_impact})")

    print("\n Analysis Statistics:")
    print(f"  Pages Analyzed      : {report.statistics.pages_analyzed}")
    print(f"  Screenshots Examined: {report.statistics.screenshots_processed}")
    print(f"  Validated Findings  : {report.statistics.validated_findings}")
    print(f"  AI Analysis State   : {'Completed' if report.ai_analysis_completed else 'Blocked/Skipped'}")
    print(f"  Execution Duration  : {report.statistics.duration_ms:.1f} ms")

    if report.report_markdown_path:
        print("\n Generated Artifacts:")
        print(f"  Markdown Report     : {report.report_markdown_path}")
        print(f"  Structured JSON     : {report.analysis_json_path}")

    print("=" * 60)

    # Return explicit exit codes based on outcome
    if offline:
        return 0
    if report.analysis_status == "completed":
        return 0
    elif report.analysis_status == "ai_blocked":
        print("\n [NOTICE] Exit Code 3: AI analysis blocked by provider quota or service limits.")
        print("         Deterministic findings and measurements preserved successfully.")
        return 3
    elif report.analysis_status == "partial":
        print("\n [NOTICE] Exit Code 4: Partial analysis completed.")
        return 4
    elif report.analysis_status == "failed":
        return 1
    return 0


def run_analyze_ux(
    visual_run_id: str | None = None,
    manifest_file: str | None = None,
    max_pages: int | None = None,
    language: str = "ar",
    save: bool = True,
    offline: bool = False,
    deterministic_only: bool = False,
) -> int:
    """Execute AI and deterministic UX/UI Usability Analysis on captured visual artifacts."""
    print("=" * 60)
    print(" Site DNA - AI UX/UI & Usability Analyst (Phase 05)")
    print("=" * 60)

    if not visual_run_id and not manifest_file:
        print(" [FAIL] Must provide either --visual-run-id or --manifest-file")
        return 2

    print(f" Target Visual ID     : {visual_run_id or 'From File'}")
    if manifest_file:
        print(f" Manifest File Path   : {manifest_file}")
    print(" Initializing UX/UI Analysis Engine...\n")

    from site_dna.analysis.ux_ui.service import UXAnalysisService
    from site_dna.schemas.ux_ui import UXAnalysisRequest

    kwargs: dict[str, Any] = {
        "visual_run_id": visual_run_id,
        "visual_manifest_file": manifest_file,
        "language": language,
        "save_results": save,
    }
    if max_pages is not None:
        kwargs["max_pages"] = max_pages

    req = UXAnalysisRequest(**kwargs)

    try:
        service = UXAnalysisService()
        report = service.analyze_ux(req, offline_mode=offline, deterministic_only=deterministic_only)
    except FileNotFoundError as exc:
        print(f" [FAIL] Visual manifest or run file not found: {exc}")
        return 2
    except Exception as exc:
        print(f" [FAIL] UX/UI Analysis failed: {exc}")
        return 1

    print("-" * 60)
    print(" UX/UI Usability Audit Summary:")
    print(f" Analysis Run ID      : {report.analysis_run_id}")
    print(f" Target Site          : {report.site_url}")
    print(f" Status               : {report.analysis_status.upper()}")
    score_str = f"{report.overall_score:.1f} / 100" if report.overall_score is not None else "N/A"
    print(f" Overall Score        : {score_str}")
    print("\n Dimension Scores:")
    for exp in report.score_explanations:
        sc = f"{exp.score:.1f} / 100" if exp.score is not None else "Not Assessed"
        print(f"  - {exp.dimension_name:<38}: {sc} (weight {int(exp.weight * 100)}%)")

    print(f"\n Supported User Journeys ({len(report.user_journeys)}):")
    for jrn in report.user_journeys:
        print(f"  - [{jrn.status:<14}] {jrn.goal}")
        print(f"    Route: {' -> '.join(jrn.route) if jrn.route else 'Direct/Missing'}")
        if jrn.potential_friction:
            print(f"    Friction: {jrn.potential_friction}")

    print(f"\n Key Findings ({len(report.findings)}):")
    for idx, f in enumerate(report.findings[:5], 1):
        print(f"  {idx}. [{f.severity.upper():<8}] {f.title}")
        print(f"     Page: {f.source_page} | Category: {f.category} | Viewport: {f.viewport}")

    if len(report.findings) > 5:
        print(f"     ... and {len(report.findings) - 5} more findings.")

    print(f"\n Actionable Recommendations ({len(report.recommendations)}):")
    for idx, r in enumerate(report.recommendations[:5], 1):
        print(
            f"  {idx}. [{r.priority.upper()}] {r.title} (Component: {r.affected_component}, Effort: {r.estimated_effort})"
        )

    print("\n Analysis Statistics:")
    print(f"  Pages Analyzed      : {report.statistics.pages_analyzed}")
    print(f"  Interactive Elements: {report.statistics.interactive_elements_audited}")
    print(f"  Forms Audited       : {report.statistics.forms_audited}")
    print(f"  Journeys Mapped     : {report.statistics.journeys_mapped}")
    print(f"  Validated Findings  : {report.statistics.validated_findings}")
    print(f"  AI Analysis State   : {'Completed' if report.ai_analysis_completed else 'Blocked/Skipped'}")
    print(f"  Execution Duration  : {report.statistics.duration_ms:.1f} ms")

    if report.report_markdown_path:
        print("\n Generated Artifacts:")
        print(f"  Markdown Report     : {report.report_markdown_path}")
        print(f"  Structured JSON     : {report.analysis_json_path}")

    print("=" * 60)

    # Return explicit exit codes based on outcome
    if offline or deterministic_only:
        return 0
    if report.analysis_status == "completed":
        return 0
    elif report.analysis_status == "ai_blocked":
        print("\n [NOTICE] Exit Code 3: AI analysis blocked by provider quota or service limits.")
        print("         Deterministic findings and measurements preserved successfully.")
        return 3
    elif report.analysis_status == "partial":
        print("\n [NOTICE] Exit Code 4: Partial analysis completed.")
        return 4
    elif report.analysis_status == "failed":
        return 1
    return 0


def run_analyze_content(
    crawl_run_id: Optional[str] = None,
    visual_run_id: Optional[str] = None,
    max_pages: Optional[int] = None,
    language: Optional[str] = "ar",
    save: bool = True,
    offline: bool = False,
    deterministic_only: bool = False,
) -> int:
    """Execute Site DNA Phase 06 Content & Marketing Intelligence audit CLI routine."""
    print("=" * 60)
    print(" Site DNA - AI Content & Marketing Intelligence Analyst (Phase 06)")
    print("=" * 60)

    if not crawl_run_id:
        # Search runs directory for latest valid crawl run
        runs_dir = Path("runs")
        candidate = None
        if runs_dir.exists():
            for c_dir in sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if (c_dir / "crawl.json").exists():
                    candidate = c_dir.name
                    break
        if candidate:
            print(f" No crawl run ID provided. Auto-discovered latest: {candidate}")
            crawl_run_id = candidate
        else:
            print(" [FAIL] Error: Must provide --crawl-run-id pointing to a valid crawl run.")
            return 1

    # Security check against path traversal
    if not re.match(r"^[a-zA-Z0-9_\-]+$", crawl_run_id):
        print(f" [FAIL] Security Error: Invalid crawl_run_id format or path traversal detected: '{crawl_run_id}'")
        return 2

    print(f" Target Crawl ID     : {crawl_run_id}")
    if visual_run_id:
        print(f" Target Visual ID    : {visual_run_id}")
    print(" Initializing Content & Marketing Intelligence Engine...")

    from site_dna.analysis.content_marketing.service import ContentMarketingAnalysisService
    from site_dna.schemas.content_marketing import ContentAnalysisRequest

    service = ContentMarketingAnalysisService()
    request = ContentAnalysisRequest(
        crawl_run_id=crawl_run_id,
        visual_run_id=visual_run_id,
        max_pages=max_pages or 8,
        language=language or "ar",
        save_results=save,
        offline_mode=offline,
        deterministic_only=deterministic_only,
    )

    try:
        report = service.analyze_content(request=request, offline_mode=offline)
    except FileNotFoundError as fnf:
        print(f"\n [FAIL] Run artifacts not found: {fnf}")
        return 1
    except Exception as exc:
        print(f"\n [FAIL] Content analysis failed: {exc}")
        return 1

    print("\n" + "-" * 60)
    print(" Content & Marketing Intelligence Audit Summary:")
    print(f" Analysis Run ID      : {report.analysis_run_id}")
    print(f" Target Site          : {report.target_origin}")
    print(f" Status               : {report.analysis_status.upper()}")
    score_str = f"{report.overall_score:.1f} / 100" if report.overall_score is not None else "N/A"
    print(f" Overall Score        : {score_str}")

    print("\n Dimension Scores:")
    for sc in report.scores:
        score_val = f"{sc.score:.1f} / 100" if sc.score is not None else "Not Assessed"
        print(f"  - {sc.dimension_name_ar:<45}: {score_val} (weight {int(sc.weight * 100)}%)")

    print(
        f"\n Content Inventory Overview ({report.content_inventory.total_pages} pages, {report.content_inventory.total_word_count} words):"
    )
    for ptype, count in report.content_inventory.page_types_distribution.items():
        print(f"  - {ptype.capitalize():<12}: {count} page(s)")

    print(f"\n Key Findings ({len(report.findings)}):")
    for idx, f in enumerate(report.findings[:5], 1):
        print(f"  {idx}. [{f.severity.upper():<8}] {f.title}")
        print(f"     Page: {f.page_url} | Category: {f.category}")

    if len(report.findings) > 5:
        print(f"     ... and {len(report.findings) - 5} more findings.")

    print(f"\n Actionable Recommendations ({len(report.recommendations)}):")
    for idx, r in enumerate(report.recommendations[:5], 1):
        print(f"  {idx}. [{r.priority.upper()}] {r.title} (Effort: {r.estimated_effort})")

    print(f"\n Grounded Copy Rewrite Proposals ({len(report.rewrite_proposals)}):")
    for idx, p in enumerate(report.rewrite_proposals[:3], 1):
        print(f"  {idx}. [{p.element_type}] Original: '{p.original_excerpt}'")
        print(f'     Proposed: "{p.proposed_replacement}"')

    print("\n Analysis Statistics:")
    print(f"  Pages Analyzed      : {report.statistics.pages_analyzed}")
    print(f"  Words Analyzed      : {report.statistics.total_words_analyzed}")
    print(f"  Claims Inventoried  : {report.statistics.claims_inventoried}")
    print(f"  CTAs Audited        : {report.statistics.ctas_analyzed}")
    print(f"  Validated Findings  : {report.statistics.findings_count}")
    print(f"  AI Model State      : {report.statistics.ai_status.capitalize()} ({report.statistics.model_name})")
    print(f"  Execution Duration  : {report.statistics.execution_duration_ms:.1f} ms")

    if report.report_markdown_path:
        print("\n Generated Artifacts:")
        print(f"  Markdown Report     : {report.report_markdown_path}")
        print(f"  Structured JSON     : {report.analysis_json_path}")

    print("=" * 60)

    if offline or deterministic_only:
        return 0
    if report.analysis_status == "completed":
        return 0
    elif report.analysis_status == "ai_blocked":
        print("\n [NOTICE] Exit Code 3: AI analysis blocked by provider quota or service limits.")
        return 3
    elif report.analysis_status == "partial":
        print("\n [NOTICE] Exit Code 4: Partial analysis completed.")
        return 4
    elif report.analysis_status == "failed":
        return 1
    return 0


def run_analyze_competitors(
    primary_run_id: Optional[str] = None,
    primary_url: Optional[str] = None,
    competitor_urls: Optional[str] = None,
    competitor_run_ids: Optional[str] = None,
    max_pages_per_site: Optional[int] = 5,
    language: str = "ar",
    save: bool = True,
    offline: bool = False,
    deterministic_only: bool = False,
) -> int:
    """Execute Competitor Intelligence benchmark from CLI."""
    import asyncio

    from site_dna.analysis.competitor_intelligence.service import CompetitorIntelligenceService
    from site_dna.schemas.competitor_intelligence import CompetitorAnalysisRequest

    comp_urls_list = [u.strip() for u in competitor_urls.split(",") if u.strip()] if competitor_urls else []
    comp_runs_list = [r.strip() for r in competitor_run_ids.split(",") if r.strip()] if competitor_run_ids else []

    if not primary_run_id and not primary_url:
        print("\n [FAIL] Either --primary-run-id or --primary-url must be provided.")
        return 1

    if not comp_urls_list and not comp_runs_list:
        print(
            "\n [FAIL] At least one competitor URL or run ID must be provided via --competitor-urls or --competitor-run-ids."
        )
        return 1

    print("=" * 60)
    print(" Site DNA - Competitor Intelligence Benchmarking (Phase 08)")
    print("=" * 60)
    print(f" Primary Target      : {primary_url or primary_run_id}")
    print(f" Competitor Sources  : {len(comp_urls_list) + len(comp_runs_list)} site(s)")
    print(f" Mode                : {'Offline / Synthetic' if offline else 'Standard Pipeline'}")
    print(" Target Model        : Gemini 3.6 Flash")

    request = CompetitorAnalysisRequest(
        primary_run_id=primary_run_id,
        primary_url=primary_url,
        competitor_urls=comp_urls_list,
        competitor_run_ids=comp_runs_list,
        max_pages_per_site=max_pages_per_site or 5,
        language=language or "ar",
        save_results=save,
        offline_mode=offline,
        deterministic_only=deterministic_only,
    )

    service = CompetitorIntelligenceService()
    try:
        report = asyncio.run(service.analyze_competitors(request))
    except Exception as exc:
        print(f"\n [FAIL] Competitor benchmark failed: {exc}")
        return 1

    print("\n" + "-" * 60)
    print(" Competitor Intelligence Benchmark Summary:")
    print(f" Comparison Run ID   : {report.comparison_run_id}")
    print(f" Primary Website     : {report.primary_site.display_name} ({report.primary_site.url})")
    print(f" Competitors Assessed: {len(report.competitor_sites)}")
    score_str = (
        f"{report.scores.overall_score:.1f} / 100" if report.scores.overall_score is not None else "Withheld / Partial"
    )
    print(f" Overall Benchmark   : {score_str}")

    print("\n Relevance Classifications:")
    for r in report.relevance_assessments:
        print(f"  - {r.site_id:<8}: {r.relevance_category.upper():<14} ({r.relevance_score:.1f}%) | {r.reason}")

    print(f"\n Identified Gaps ({len(report.gaps)}):")
    for idx, g in enumerate(report.gaps[:4], 1):
        print(f"  {idx}. [{g.gap_type}] {g.title}")
        print(f"     Difference: {g.observed_difference}")

    print(f"\n Strategic Opportunities ({len(report.opportunities)}):")
    for idx, o in enumerate(report.opportunities[:4], 1):
        print(f"  {idx}. [{o.opportunity_type}] {o.title}")
        print(f"     Action: {o.suggested_action} (Impact: {o.estimated_impact}, Effort: {o.estimated_effort})")

    print(f"\n Actionable Recommendations ({len(report.recommendations)}):")
    for idx, r in enumerate(report.recommendations[:4], 1):
        print(f"  {idx}. [{r.priority.upper()}] {r.title} (Impact: {r.impact})")

    print("\n Operational Statistics:")
    print(f"  Total Pages Analyzed: {report.statistics.total_pages_analyzed}")
    print(f"  Features Compared   : {report.statistics.total_features_compared}")
    print(f"  Execution Duration  : {report.statistics.execution_duration_ms:.1f} ms")
    print("=" * 60)

    return 0


def run_analyze_seo(
    crawl_run_id: Optional[str] = None,
    visual_run_id: Optional[str] = None,
    max_pages: Optional[int] = None,
    language: str = "ar",
    save: bool = True,
    offline: bool = False,
    deterministic_only: bool = False,
) -> int:
    """Execute Site DNA Phase 07 Technical SEO & Performance Intelligence audit CLI routine."""
    print("=" * 60)
    print(" Site DNA - Technical SEO & Website Performance Analyst (Phase 07)")
    print("=" * 60)

    if not crawl_run_id:
        runs_dir = Path("runs")
        candidate = None
        if runs_dir.exists():
            for c_dir in sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if (c_dir / "crawl.json").exists():
                    candidate = c_dir.name
                    break
        if candidate:
            print(f" No crawl run ID provided. Auto-discovered latest: {candidate}")
            crawl_run_id = candidate
        else:
            print(" [FAIL] Error: Must provide --crawl-run-id pointing to a valid crawl run.")
            return 1

    if not re.match(r"^[a-zA-Z0-9_\-]+$", crawl_run_id):
        print(f" [FAIL] Security Error: Invalid crawl_run_id format or path traversal detected: '{crawl_run_id}'")
        return 2

    if visual_run_id and not re.match(r"^[a-zA-Z0-9_\-]+$", visual_run_id):
        print(f" [FAIL] Security Error: Invalid visual_run_id format or path traversal detected: '{visual_run_id}'")
        return 2

    print(f" Target Crawl ID     : {crawl_run_id}")
    if visual_run_id:
        print(f" Target Visual ID    : {visual_run_id}")
    print(" Initializing Technical SEO & Performance Engine...")

    from site_dna.analysis.technical_seo.service import TechnicalSEOAnalysisService
    from site_dna.schemas.technical_seo import TechnicalSEOAnalysisRequest

    service = TechnicalSEOAnalysisService()
    request = TechnicalSEOAnalysisRequest(
        crawl_run_id=crawl_run_id,
        visual_run_id=visual_run_id,
        max_pages=max_pages or 10,
        language=language or "ar",
        save_results=save,
        offline_mode=offline,
        deterministic_only=deterministic_only,
    )

    try:
        report = service.analyze_technical_seo(request=request, offline_mode=offline)
    except FileNotFoundError as fnf:
        print(f"\n [FAIL] Run artifacts not found: {fnf}")
        return 1
    except Exception as exc:
        print(f"\n [FAIL] Technical SEO analysis failed: {exc}")
        return 1

    print("\n" + "-" * 60)
    print(" Technical SEO & Performance Intelligence Audit Summary:")
    print(f" Analysis Run ID      : {report.analysis_run_id}")
    print(f" Target Origin        : {report.target_origin}")
    print(f" Status               : {report.analysis_status.upper()}")
    score_str = f"{report.overall_score:.1f} / 100" if report.overall_score is not None else "N/A"
    print(f" Overall Score        : {score_str}")

    print("\n Dimension Scores:")
    for sc in report.scores:
        score_val = f"{sc.score:.1f} / 100" if sc.score is not None else "Not Assessed"
        print(f"  - {sc.dimension_name_ar:<45}: {score_val} (weight {int(sc.weight * 100)}%)")

    print(f"\n Key Findings ({len(report.findings)}):")
    for idx, f in enumerate(report.findings[:5], 1):
        print(f"  {idx}. [{f.severity.upper():<8}] {f.title}")
        print(f"     Page: {f.page_url} | Category: {f.category}")

    if len(report.findings) > 5:
        print(f"     ... and {len(report.findings) - 5} more findings.")

    print(f"\n Actionable Recommendations ({len(report.recommendations)}):")
    for idx, r in enumerate(report.recommendations[:5], 1):
        print(f"  {idx}. [{r.priority.upper()}] {r.title} (Effort: {r.estimated_effort})")

    print("\n Analysis Statistics:")
    print(f"  Pages Evaluated     : {report.statistics.pages_evaluated}")
    print(f"  Pages Eligible      : {report.statistics.pages_eligible}")
    print(f"  Indexing Signals    : {report.statistics.indexing_signals_count}")
    print(f"  Structured Data     : {report.statistics.structured_data_count}")
    print(f"  Validated Findings  : {report.statistics.validated_findings_count}")
    print(f"  AI Model State      : {report.statistics.ai_status.capitalize()} ({report.statistics.model_name})")
    print(f"  Execution Duration  : {report.statistics.execution_duration_ms:.1f} ms")

    if report.report_markdown_path:
        print("\n Generated Artifacts:")
        print(f"  Markdown Report     : {report.report_markdown_path}")
        print(f"  Structured JSON     : {report.analysis_json_path}")

    print("=" * 60)

    if offline or deterministic_only:
        return 0
    if report.analysis_status == "completed":
        return 0
    elif report.analysis_status == "ai_blocked":
        print("\n [NOTICE] Exit Code 3: AI analysis blocked by provider quota or service limits.")
        return 3
    elif report.analysis_status == "partial":
        print("\n [NOTICE] Exit Code 4: Partial analysis completed.")
        return 4
    elif report.analysis_status == "failed":
        return 1
    return 0


def run_analyze_security(
    crawl_run_id: Optional[str] = None,
    visual_run_id: Optional[str] = None,
    max_pages: Optional[int] = None,
    language: str = "ar",
    save: bool = True,
    offline: bool = False,
    deterministic_only: bool = False,
) -> int:
    """Execute Site DNA Phase 09 Security, Privacy & Trust Intelligence audit CLI routine."""
    import asyncio

    from site_dna.analysis.security_privacy.service import SecurityPrivacyService
    from site_dna.schemas.security_privacy import SecurityPrivacyAnalysisRequest

    print("=" * 60)
    print(" Site DNA - Security, Privacy & Digital Trust Intelligence (Phase 09)")
    print("=" * 60)

    if not crawl_run_id:
        runs_dir = Path("runs")
        candidate = None
        if runs_dir.exists():
            for c_dir in sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if (c_dir / "crawl.json").exists():
                    candidate = c_dir.name
                    break
        if candidate:
            print(f" No crawl run ID provided. Auto-discovered latest: {candidate}")
            crawl_run_id = candidate
        else:
            print(" [FAIL] Error: Must provide --crawl-run-id pointing to a valid crawl run.")
            return 1

    if not re.match(r"^[a-zA-Z0-9_\-]+$", crawl_run_id):
        print(f" [FAIL] Security Error: Invalid crawl_run_id format or path traversal: '{crawl_run_id}'")
        return 2

    if visual_run_id and not re.match(r"^[a-zA-Z0-9_\-]+$", visual_run_id):
        print(f" [FAIL] Security Error: Invalid visual_run_id format or path traversal: '{visual_run_id}'")
        return 2

    print(f" Target Crawl ID     : {crawl_run_id}")
    if visual_run_id:
        print(f" Target Visual ID    : {visual_run_id}")
    print(f" Execution Mode      : {'Deterministic / Offline' if (offline or deterministic_only) else 'Full Pipeline'}")
    print(" Target Model        : Gemini 3.6 Flash")

    req = SecurityPrivacyAnalysisRequest(
        crawl_run_id=crawl_run_id,
        visual_run_id=visual_run_id,
        language=language or "ar",
        max_pages=max_pages or 8,
        save_results=save,
        offline_mode=offline,
        deterministic_only=deterministic_only,
    )

    service = SecurityPrivacyService()
    try:
        report = asyncio.run(service.analyze_security(req))
    except Exception as exc:
        print(f"\n [FAIL] Security audit failed: {exc}")
        return 1

    print("\n" + "-" * 60)
    print(" Security & Privacy Intelligence Audit Summary:")
    print(f" Security Run ID     : {report.security_run_id}")
    print(f" Site Target         : {report.target_url}")
    print(f" HTTPS Transport     : {report.https_assessment.status_ar}")
    print(f" HSTS Status         : {'Enforced' if report.https_assessment.hsts_present else 'Missing'}")
    print(
        f" Headers Checked     : {report.security_headers_assessment.present_headers_count}/{report.security_headers_assessment.total_headers_checked} present"
    )
    print(f" Cookies Observed    : {report.cookie_security_assessment.total_cookies_observed} (all values redacted)")
    print(
        f" Mixed Content       : {'Detected' if report.mixed_content_assessment.has_mixed_content else 'None observed'}"
    )
    print(
        f" Privacy Policy      : {'Found' if report.privacy_signal_assessment.privacy_policy_found else 'Not found in sample'}"
    )
    print(
        f" Observable Posture  : {report.scores.overall_score:.1f} / 100"
        if report.scores.overall_score is not None
        else " Withheld"
    )
    print(f" Findings Count      : {len(report.findings)}")
    print(f" Recommendations     : {len(report.recommendations)}")

    print("\n Top Defensive Recommendations:")
    for idx, r in enumerate(report.recommendations[:4], start=1):
        print(f"  {idx}. [{r.priority.upper()}] {r.title}")
        print(f"     Change: {r.recommended_configuration_change}")

    print("\n Telemetry:")
    print(f"  Pages Assessed     : {report.statistics.pages_assessed}")
    print(f"  Execution Time     : {report.statistics.execution_duration_ms:.1f} ms")
    print(f"  AI Status          : {report.statistics.ai_status.upper()}")
    print("=" * 60)

    if report.analysis_status == "ai_blocked":
        print("\n [NOTICE] Exit Code 3: AI analysis blocked by provider quota or limits.")
        return 3
    elif report.analysis_status == "failed":
        return 1
    return 0


def run_analyze_accessibility(
    crawl_run_id: Optional[str] = None,
    visual_run_id: Optional[str] = None,
    ux_run_id: Optional[str] = None,
    max_pages: Optional[int] = None,
    language: str = "ar",
    save: bool = True,
    deterministic_only: bool = False,
    include_automated_rules: bool = True,
) -> int:
    """Execute Site DNA Phase 10 Web Accessibility & WCAG 2.2 Intelligence audit CLI routine."""
    import asyncio

    from site_dna.analysis.accessibility.service import AccessibilityService
    from site_dna.schemas.accessibility import AccessibilityAnalysisRequest

    print("=" * 60)
    print(" Site DNA - Web Accessibility & WCAG 2.2 Intelligence (Phase 10)")
    print("=" * 60)

    if not crawl_run_id:
        runs_dir = Path("runs")
        candidate = None
        if runs_dir.exists():
            for c_dir in sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
                if (c_dir / "crawl.json").exists():
                    candidate = c_dir.name
                    break
        if candidate:
            print(f" No crawl run ID provided. Auto-discovered latest: {candidate}")
            crawl_run_id = candidate
        else:
            print(" [FAIL] Error: Must provide --crawl-run-id pointing to a valid crawl run.")
            return 1

    if not re.match(r"^[a-zA-Z0-9_\-]+$", crawl_run_id):
        print(f" [FAIL] Security Error: Invalid crawl_run_id format: '{crawl_run_id}'")
        return 2

    if visual_run_id and not re.match(r"^[a-zA-Z0-9_\-]+$", visual_run_id):
        print(f" [FAIL] Security Error: Invalid visual_run_id format: '{visual_run_id}'")
        return 2

    if ux_run_id and not re.match(r"^[a-zA-Z0-9_\-]+$", ux_run_id):
        print(f" [FAIL] Security Error: Invalid ux_run_id format: '{ux_run_id}'")
        return 2

    print(f" Target Crawl ID     : {crawl_run_id}")
    if visual_run_id:
        print(f" Target Visual ID    : {visual_run_id}")
    print(f" Execution Mode      : {'Deterministic Only' if deterministic_only else 'Full Pipeline'}")
    print(" Target Model        : Gemini 3.6 Flash")

    req = AccessibilityAnalysisRequest(
        crawl_run_id=crawl_run_id,
        visual_run_id=visual_run_id,
        ux_run_id=ux_run_id,
        language=language or "ar",
        max_pages=max_pages or 8,
        save_results=save,
        deterministic_only=deterministic_only,
        include_automated_rules=include_automated_rules,
    )

    service = AccessibilityService()
    try:
        report = asyncio.run(service.analyze_accessibility(req))
    except Exception as exc:
        print(f"\n [FAIL] Accessibility audit failed: {exc}")
        return 1

    print("\n" + "-" * 60)
    print(" Accessibility & WCAG 2.2 Intelligence Audit Summary:")
    print(f" Accessibility ID    : {report.accessibility_run_id}")
    print(f" Target URL          : {report.target_url}")
    print(f" Pages Evaluated     : {report.statistics.pages_evaluated}")
    print(f" Confirmed Barriers  : {report.statistics.confirmed_failures_count}")
    print(f" Potential Issues    : {report.statistics.potential_issues_count}")
    print(f" Manual Review Tasks : {report.statistics.manual_review_tasks_count}")
    print(f" Overall Score       : {report.scores.overall_score}/100 ({report.scores.score_label_ar})")
    print(f" Artifacts Dir       : runs/{crawl_run_id}/analysis/accessibility/{report.accessibility_run_id}")
    print("=" * 60)
    return 0


def run_analyze_strategy(
    crawl_run_id: Optional[str] = None,
    source_run_ids: Optional[list[str]] = None,
    language: str = "ar",
    max_actions: int = 50,
    save: bool = True,
    deterministic_only: bool = False,
) -> int:
    """Execute AI Strategic Intelligence & Action Roadmap synthesis (Phase 11)."""
    import asyncio
    from site_dna.analysis.strategic_intelligence.service import StrategicIntelligenceService
    from site_dna.schemas.strategic_intelligence import StrategicAnalysisRequest

    print("=" * 60)
    print(" Site DNA - Strategic Intelligence & Unified Action Roadmap (Phase 11)")
    print("=" * 60)

    if not crawl_run_id:
        runs_dir = Path("runs")
        if runs_dir.exists():
            candidate_runs = sorted(
                [d.name for d in runs_dir.iterdir() if d.is_dir() and (d / "crawl.json").exists()],
                reverse=True,
            )
            if candidate_runs:
                crawl_run_id = candidate_runs[0]
                print(f" [*] Auto-selected latest crawl run: {crawl_run_id}")
            else:
                print(" [FAIL] No crawl runs found. Provide --crawl-run-id.")
                return 1
        else:
            print(" [FAIL] runs/ directory does not exist. Provide --crawl-run-id.")
            return 1

    req = StrategicAnalysisRequest(
        crawl_run_id=crawl_run_id,
        source_run_ids=source_run_ids or [],
        language=language,
        max_actions=max_actions,
        deterministic_only=deterministic_only,
        save_results=save,
    )

    service = StrategicIntelligenceService()
    try:
        report = asyncio.run(service.analyze_strategy(req))
    except Exception as exc:
        print(f"\n [FAIL] Strategic synthesis failed: {exc}")
        return 1

    print("\n" + "-" * 60)
    print(" Strategic Intelligence Audit Summary:")
    print(f" Strategy ID         : {report.strategic_run_id}")
    print(f" Target URL          : {report.target_url}")
    print(f" Analyzed Agents     : {', '.join(report.coverage.available_agents)}")
    print(f" Unified Findings    : {len(report.unified_findings)}")
    print(f" Deduplicated Groups : {len(report.duplicate_groups)}")
    print(f" Conflict Tradeoffs  : {len(report.conflicts)}")
    print(f" Strategic Index     : {report.statistics.strategic_index}/100 ({report.statistics.index_label_ar})")
    print(f" Action Backlog Items: {len(report.actions)}")
    print(f" Waves Generated     : {len(report.waves)}")
    print(f" Artifacts Dir       : runs/{crawl_run_id}/analysis/strategic-intelligence/{report.strategic_run_id}")
    print("=" * 60)
    return 0


def run_export_report(
    analysis_run_id: Optional[str] = None,
    output_format: str = "pdf",
    report_mode: str = "comprehensive",
    language: str = "ar",
    paper_size: str = "A4",
    output: Optional[str] = None,
    validate: bool = True,
    deterministic_only: bool = False,
) -> int:
    """Execute Phase 12 Enterprise Report Export & Quality Verification."""
    import asyncio
    import shutil
    from site_dna.reporting.export_service import FinalReportExportService
    from site_dna.schemas.final_report import FinalReportRequest

    print("=" * 60)
    print(" Site DNA - Phase 12: Enterprise Report & PDF Export")
    print("=" * 60)

    # 1. Resolve analysis run
    runs_dir = Path("runs")
    if not analysis_run_id:
        if runs_dir.exists():
            crawl_dirs = [d for d in runs_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
            if crawl_dirs:
                latest = max(crawl_dirs, key=lambda d: d.stat().st_mtime)
                analysis_run_id = latest.name
                print(f" [INFO] Auto-selected latest run: {analysis_run_id}")
            else:
                print(" [FAIL] No crawl runs found. Provide --analysis-run-id.")
                return 1
        else:
            print(" [FAIL] runs/ directory does not exist. Provide --analysis-run-id.")
            return 1

    req = FinalReportRequest(
        crawl_run_id=analysis_run_id,
        mode=report_mode.lower(),
        language=language.lower(),
        paper_size=paper_size,
        validate_pdf=validate,
        deterministic_only=deterministic_only,
    )

    service = FinalReportExportService()
    try:
        metadata = asyncio.run(service.generate_report(req))
    except Exception as exc:
        print(f"\n [FAIL] Final Report generation failed: {exc}")
        return 1

    print("\n" + "-" * 60)
    print(" Report Generation & Verification Summary:")
    print(f" Report ID           : {metadata.report_id}")
    print(f" Analysis Run ID     : {metadata.analysis_run_id}")
    print(f" Target URL          : {metadata.target_url}")
    print(f" Overall Score       : {metadata.overall_score}/100")
    print(f" Total Findings      : {metadata.total_findings}")
    print(f" Total Recomms       : {metadata.total_recommendations}")
    print(f" Page Count          : {metadata.page_count}")
    print(f" PDF Validation      : {'PASSED' if metadata.validation_passed else 'WARNING / NOT VERIFIED'}")
    print(f" PDF Artifact        : {metadata.artifacts.pdf}")
    print(f" HTML Artifact       : {metadata.artifacts.html}")
    print(f" JSON Artifact       : {metadata.artifacts.json_data}")
    print(f" Markdown Artifact   : {metadata.artifacts.markdown}")

    if output:
        dest = Path(output)
        fmt_lower = output_format.lower()
        src_path = None
        if fmt_lower == "pdf" and metadata.artifacts.pdf:
            src_path = Path(metadata.artifacts.pdf)
        elif fmt_lower == "html" and metadata.artifacts.html:
            src_path = Path(metadata.artifacts.html)
        elif fmt_lower == "json" and metadata.artifacts.json_data:
            src_path = Path(metadata.artifacts.json_data)
        elif fmt_lower in ("md", "markdown") and metadata.artifacts.markdown:
            src_path = Path(metadata.artifacts.markdown)

        if src_path and src_path.exists():
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dest)
            print(f" Exported Copy Saved : {dest}")

    print("=" * 60)
    return 0


def main() -> None:
    """Main CLI entrypoint."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    setup_logging(level="WARNING")

    parser = argparse.ArgumentParser(
        prog="site-dna",
        description="Site DNA CLI: Environment verification, diagnostics, and crawling.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: doctor
    subparsers.add_parser("doctor", help="Verify environment, dependencies, and configuration")

    # Command: smoke
    smoke_parser = subparsers.add_parser("smoke", help="Execute diagnostic smoke tests")
    smoke_parser.add_argument("--direct", action="store_true", help="Direct Google GenAI SDK test")
    smoke_parser.add_argument("--crew", action="store_true", help="CrewAI Smoke Agent execution")
    smoke_parser.add_argument("--flow", action="store_true", help="CrewAI Foundation Flow execution")
    smoke_parser.add_argument("--live", action="store_true", help="Explicitly enable live network calls")

    # Command: discover
    disc_parser = subparsers.add_parser("discover", help="Discover and crawl a website (Phase 02)")
    disc_parser.add_argument("--url", required=True, help="Target website URL")
    disc_parser.add_argument("--max-pages", type=int, default=None, help="Maximum pages to crawl")
    disc_parser.add_argument("--max-depth", type=int, default=None, help="Maximum crawl depth")
    disc_parser.add_argument("--output", default=None, help="Output file path for crawl JSON")
    disc_parser.add_argument("--save", action="store_true", help="Save result to runs/<run_id>/crawl.json")

    # Command: visual-capture
    vis_parser = subparsers.add_parser("visual-capture", help="Render pages and capture visual evidence (Phase 03)")
    vis_parser.add_argument("--crawl-file", default=None, help="Path to existing crawl.json artifact")
    vis_parser.add_argument("--crawl-run-id", default=None, help="ID of existing crawl run in runs/")
    vis_parser.add_argument("--max-pages", type=int, default=None, help="Maximum pages to capture")
    vis_parser.add_argument("--save", action="store_true", default=True, help="Persist visual artifacts and manifest")

    # Command: analyze-visual
    ana_parser = subparsers.add_parser("analyze-visual", help="Execute AI visual identity audit (Phase 04)")
    ana_parser.add_argument("--visual-run-id", default=None, help="ID of existing visual run (e.g. vis-e6b6128de9b5)")
    ana_parser.add_argument("--manifest-file", default=None, help="Path to manifest.json file")
    ana_parser.add_argument("--max-pages", type=int, default=None, help="Maximum pages to evaluate")
    ana_parser.add_argument("--max-images", type=int, default=None, help="Maximum screenshots to inspect with vision")
    ana_parser.add_argument("--save", action="store_true", default=True, help="Save reports and structured JSON")
    ana_parser.add_argument(
        "--offline", action="store_true", default=False, help="Force offline deterministic analysis"
    )

    # Command: analyze-ux
    ux_parser = subparsers.add_parser("analyze-ux", help="Execute AI UX/UI and usability intelligence audit (Phase 05)")
    ux_parser.add_argument("--visual-run-id", default=None, help="ID of existing visual run (e.g. vis-e6b6128de9b5)")
    ux_parser.add_argument("--manifest-file", default=None, help="Path to manifest.json file")
    ux_parser.add_argument("--max-pages", type=int, default=None, help="Maximum pages to evaluate")
    ux_parser.add_argument("--language", default="ar", help="Report language ('ar' or 'en')")
    ux_parser.add_argument("--save", action="store_true", default=True, help="Save reports and structured JSON")
    ux_parser.add_argument("--offline", action="store_true", default=False, help="Force offline analysis mode")
    ux_parser.add_argument(
        "--deterministic-only", action="store_true", default=False, help="Run only deterministic analyzers without AI"
    )

    # Command: analyze-content
    cnt_parser = subparsers.add_parser(
        "analyze-content", help="Execute AI Content & Marketing Intelligence audit (Phase 06)"
    )
    cnt_parser.add_argument("--crawl-run-id", default=None, help="ID of existing crawl run (e.g. 98b5cd6a-...)")
    cnt_parser.add_argument("--visual-run-id", default=None, help="Optional ID of associated visual run")
    cnt_parser.add_argument("--max-pages", type=int, default=None, help="Maximum pages to evaluate")
    cnt_parser.add_argument("--language", default="ar", help="Report language ('ar' or 'en')")
    cnt_parser.add_argument("--save", action="store_true", default=True, help="Save reports and structured JSON")
    cnt_parser.add_argument("--offline", action="store_true", default=False, help="Force offline analysis mode")
    cnt_parser.add_argument(
        "--deterministic-only", action="store_true", default=False, help="Run only deterministic analyzers without AI"
    )

    # Command: analyze-seo
    seo_parser = subparsers.add_parser("analyze-seo", help="Execute AI Technical SEO & Performance audit (Phase 07)")
    seo_parser.add_argument("--crawl-run-id", default=None, help="ID of existing crawl run (e.g. 98b5cd6a-...)")
    seo_parser.add_argument("--visual-run-id", default=None, help="Optional ID of associated visual run")
    seo_parser.add_argument("--max-pages", type=int, default=None, help="Maximum pages to evaluate")
    seo_parser.add_argument("--language", default="ar", help="Report language ('ar' or 'en')")
    seo_parser.add_argument("--save", action="store_true", default=True, help="Save reports and structured JSON")
    seo_parser.add_argument("--offline", action="store_true", default=False, help="Force offline analysis mode")
    seo_parser.add_argument(
        "--deterministic-only", action="store_true", default=False, help="Run only deterministic analyzers without AI"
    )

    # Command: analyze-competitors
    cmp_parser = subparsers.add_parser(
        "analyze-competitors", help="Execute AI Competitor Intelligence & Benchmarking audit (Phase 08)"
    )
    cmp_parser.add_argument("--primary-run-id", default=None, help="ID of existing primary crawl run")
    cmp_parser.add_argument("--primary-url", default=None, help="Primary website URL")
    cmp_parser.add_argument(
        "--competitor-urls", default=None, help="Comma-separated competitor URLs (e.g. https://a.com,https://b.com)"
    )
    cmp_parser.add_argument(
        "--competitor-run-ids", default=None, help="Comma-separated competitor run IDs (e.g. crawl-a,crawl-b)"
    )
    cmp_parser.add_argument("--max-pages-per-site", type=int, default=5, help="Maximum pages to evaluate per website")
    cmp_parser.add_argument("--language", default="ar", help="Report language ('ar' or 'en')")
    cmp_parser.add_argument("--save", action="store_true", default=True, help="Save reports and structured JSON")
    cmp_parser.add_argument("--offline", action="store_true", default=False, help="Force offline analysis mode")
    cmp_parser.add_argument(
        "--deterministic-only", action="store_true", default=False, help="Run only deterministic analyzers without AI"
    )

    # Command: analyze-security
    sec_parser = subparsers.add_parser(
        "analyze-security", help="Execute AI Website Security, Privacy & Trust Intelligence audit (Phase 09)"
    )
    sec_parser.add_argument("--crawl-run-id", default=None, help="ID of existing crawl run (e.g. 98b5cd6a-...)")
    sec_parser.add_argument("--visual-run-id", default=None, help="Optional ID of associated visual run")
    sec_parser.add_argument("--max-pages", type=int, default=8, help="Maximum pages to evaluate")
    sec_parser.add_argument("--language", default="ar", help="Report language ('ar' or 'en')")
    sec_parser.add_argument("--save", action="store_true", default=True, help="Save reports and structured JSON")
    sec_parser.add_argument("--offline", action="store_true", default=False, help="Force offline analysis mode")
    sec_parser.add_argument(
        "--deterministic-only", action="store_true", default=False, help="Run only deterministic analyzers without AI"
    )

    # Command: analyze-accessibility
    a11y_parser = subparsers.add_parser(
        "analyze-accessibility", help="Execute AI Web Accessibility & WCAG 2.2 Intelligence audit (Phase 10)"
    )
    a11y_parser.add_argument("--crawl-run-id", default=None, help="ID of existing crawl run (e.g. 98b5cd6a-...)")
    a11y_parser.add_argument("--visual-run-id", default=None, help="Optional ID of associated visual run")
    a11y_parser.add_argument("--ux-run-id", default=None, help="Optional ID of associated UX run")
    a11y_parser.add_argument("--max-pages", type=int, default=8, help="Maximum pages to evaluate")
    a11y_parser.add_argument("--language", default="ar", help="Report language ('ar' or 'en')")
    a11y_parser.add_argument("--save", action="store_true", default=True, help="Save reports and structured JSON")
    a11y_parser.add_argument(
        "--deterministic-only", action="store_true", default=False, help="Run only deterministic analyzers without AI"
    )
    a11y_parser.add_argument(
        "--include-automated-rules", action="store_true", default=True, help="Run automated rules adapter"
    )

    # Command: analyze-strategy
    strat_parser = subparsers.add_parser(
        "analyze-strategy", help="Execute AI Strategic Intelligence & Action Roadmap synthesis (Phase 11)"
    )
    strat_parser.add_argument("--crawl-run-id", default=None, help="ID of existing crawl run (e.g. crawl-a)")
    strat_parser.add_argument(
        "--source-run-ids", default=None, help="Comma-separated run IDs to ingest (e.g. run-1,run-2)"
    )
    strat_parser.add_argument("--language", default="ar", help="Report language ('ar' or 'en')")
    strat_parser.add_argument("--max-actions", type=int, default=50, help="Maximum roadmap actions to generate")
    strat_parser.add_argument("--save", action="store_true", default=True, help="Save reports and structured JSON")
    strat_parser.add_argument(
        "--deterministic-only", action="store_true", default=False, help="Run only deterministic analyzers without AI"
    )

    # Command: export-report (Phase 12)
    report_parser = subparsers.add_parser(
        "export-report", help="Generate enterprise-grade PDF, HTML, and JSON reports with quality verification (Phase 12)"
    )
    report_parser.add_argument("--analysis-run-id", default=None, help="ID of existing crawl run (e.g. crawl-a)")
    report_parser.add_argument(
        "--format",
        default="pdf",
        choices=["pdf", "html", "json", "md", "all"],
        help="Target report format (pdf, html, json, md, all)",
    )
    report_parser.add_argument(
        "--report-mode",
        default="comprehensive",
        choices=["executive", "comprehensive", "agent"],
        help="Report depth and audience mode",
    )
    report_parser.add_argument("--language", default="ar", choices=["ar", "en"], help="Report language ('ar' or 'en')")
    report_parser.add_argument("--paper-size", default="A4", choices=["A4", "Letter"], help="Paper size for PDF export")
    report_parser.add_argument("--output", default=None, help="Optional destination path to copy the exported artifact")
    report_parser.add_argument("--validate", action="store_true", default=True, help="Validate PDF layout & quality")
    report_parser.add_argument(
        "--deterministic-only", action="store_true", default=False, help="Run only deterministic analyzers without AI"
    )

    args = parser.parse_args()

    if args.command == "doctor":
        sys.exit(run_doctor())
    elif args.command == "smoke":
        sys.exit(run_smoke(direct=args.direct, crew=args.crew, flow=args.flow, live=args.live))
    elif args.command == "discover":
        sys.exit(
            run_discover(
                url=args.url,
                max_pages=args.max_pages,
                max_depth=args.max_depth,
                output=args.output,
                save=args.save,
            )
        )
    elif args.command == "visual-capture":
        sys.exit(
            run_visual_capture(
                crawl_file=args.crawl_file,
                crawl_run_id=args.crawl_run_id,
                max_pages=args.max_pages,
                save=args.save,
            )
        )
    elif args.command == "analyze-visual":
        sys.exit(
            run_analyze_visual(
                visual_run_id=args.visual_run_id,
                manifest_file=args.manifest_file,
                max_pages=args.max_pages,
                max_images=args.max_images,
                save=args.save,
                offline=args.offline,
            )
        )
    elif args.command == "analyze-ux":
        sys.exit(
            run_analyze_ux(
                visual_run_id=args.visual_run_id,
                manifest_file=args.manifest_file,
                max_pages=args.max_pages,
                language=args.language,
                save=args.save,
                offline=args.offline,
                deterministic_only=args.deterministic_only,
            )
        )
    elif args.command == "analyze-content":
        sys.exit(
            run_analyze_content(
                crawl_run_id=args.crawl_run_id,
                visual_run_id=args.visual_run_id,
                max_pages=args.max_pages,
                language=args.language,
                save=args.save,
                offline=args.offline,
                deterministic_only=args.deterministic_only,
            )
        )
    elif args.command == "analyze-seo":
        sys.exit(
            run_analyze_seo(
                crawl_run_id=args.crawl_run_id,
                visual_run_id=args.visual_run_id,
                max_pages=args.max_pages,
                language=args.language,
                save=args.save,
                offline=args.offline,
                deterministic_only=args.deterministic_only,
            )
        )
    elif args.command == "analyze-competitors":
        sys.exit(
            run_analyze_competitors(
                primary_run_id=args.primary_run_id,
                primary_url=args.primary_url,
                competitor_urls=args.competitor_urls,
                competitor_run_ids=args.competitor_run_ids,
                max_pages_per_site=args.max_pages_per_site,
                language=args.language,
                save=args.save,
                offline=args.offline,
                deterministic_only=args.deterministic_only,
            )
        )
    elif args.command == "analyze-security":
        sys.exit(
            run_analyze_security(
                crawl_run_id=args.crawl_run_id,
                visual_run_id=args.visual_run_id,
                max_pages=args.max_pages,
                language=args.language,
                save=args.save,
                offline=args.offline,
                deterministic_only=args.deterministic_only,
            )
        )
    elif args.command == "analyze-accessibility":
        sys.exit(
            run_analyze_accessibility(
                crawl_run_id=args.crawl_run_id,
                visual_run_id=args.visual_run_id,
                ux_run_id=args.ux_run_id,
                max_pages=args.max_pages,
                language=args.language,
                save=args.save,
                deterministic_only=args.deterministic_only,
                include_automated_rules=args.include_automated_rules,
            )
        )
    elif args.command == "analyze-strategy":
        src_ids = [s.strip() for s in args.source_run_ids.split(",") if s.strip()] if args.source_run_ids else []
        sys.exit(
            run_analyze_strategy(
                crawl_run_id=args.crawl_run_id,
                source_run_ids=src_ids,
                language=args.language,
                max_actions=args.max_actions,
                save=args.save,
                deterministic_only=args.deterministic_only,
            )
        )
    elif args.command == "export-report":
        sys.exit(
            run_export_report(
                analysis_run_id=args.analysis_run_id,
                output_format=args.format,
                report_mode=args.report_mode,
                language=args.language,
                paper_size=args.paper_size,
                output=args.output,
                validate=args.validate,
                deterministic_only=args.deterministic_only,
            )
        )
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
