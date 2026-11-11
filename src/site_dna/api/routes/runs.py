"""FastAPI router for Site DNA Runs, Orchestration, Agent Registry & Live Monitoring."""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse, StreamingResponse

from site_dna.core.config import Settings, get_settings
from site_dna.core.logging import get_logger
from site_dna.orchestration.coordinator import AnalysisCoordinator
from site_dna.schemas.runs import (
    AgentRegistryItem,
    DashboardSummary,
    RunRecord,
    RunSubmissionRequest,
)

logger = get_logger("api.routes.runs")

router = APIRouter(prefix="/api/v1", tags=["Runs & Dashboard"])

# Global coordinator singleton
_coordinator: Optional[AnalysisCoordinator] = None


def get_coordinator(settings: Settings = Depends(get_settings)) -> AnalysisCoordinator:
    """Dependency provider for AnalysisCoordinator singleton."""
    global _coordinator
    if _coordinator is None:
        _coordinator = AnalysisCoordinator(base_dir="runs", settings=settings)
    return _coordinator


# --- 1. Agent Registry ---


@router.get("/agents", response_model=list[AgentRegistryItem], summary="List all Site DNA agents (Phases 01-12)")
async def list_agents(coordinator: AnalysisCoordinator = Depends(get_coordinator)) -> list[AgentRegistryItem]:
    """Retrieve the full agent registry with implementation readiness and execution flags."""
    return coordinator.list_agents()


@router.get("/agents/{agent_id}", response_model=AgentRegistryItem, summary="Get details for a specific agent")
async def get_agent(agent_id: str, coordinator: AnalysisCoordinator = Depends(get_coordinator)) -> AgentRegistryItem:
    """Retrieve metadata, dependencies, and readiness for a single agent."""
    agent = coordinator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent '{agent_id}' not found.")
    return agent


# --- 2. Dashboard Summary ---


@router.get("/dashboard/summary", response_model=DashboardSummary, summary="Get high-level dashboard metrics")
async def get_dashboard_summary(coordinator: AnalysisCoordinator = Depends(get_coordinator)) -> DashboardSummary:
    """Aggregate statistics across all analysis runs for the main dashboard."""
    return coordinator.get_dashboard_summary()


# --- 3. Runs Management ---


@router.get("/runs", summary="List historical website analysis runs")
async def list_runs(
    query: Optional[str] = Query(None, description="Search by URL or Run ID"),
    status: Optional[str] = Query(None, description="Filter by status (all, completed, running, failed)"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    coordinator: AnalysisCoordinator = Depends(get_coordinator),
):
    """Retrieve a paginated list of analysis runs."""
    records, total = coordinator.list_runs(query=query, status_filter=status, page=page, page_size=page_size)
    return {
        "items": records,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages_count": (total + page_size - 1) // page_size if page_size else 1,
    }


@router.post(
    "/runs", response_model=RunRecord, status_code=status.HTTP_201_CREATED, summary="Submit a new analysis run"
)
async def submit_run(
    request_data: RunSubmissionRequest,
    coordinator: AnalysisCoordinator = Depends(get_coordinator),
) -> RunRecord:
    """Create a new analysis run with user-selected agent stages."""
    logger.info("Received run submission for URL: %s with stages: %s", request_data.url, request_data.stages)
    return coordinator.create_and_start_run(request_data)


@router.get("/runs/{run_id}", response_model=RunRecord, summary="Get detailed run record and stage statuses")
async def get_run(
    run_id: str,
    coordinator: AnalysisCoordinator = Depends(get_coordinator),
) -> RunRecord:
    """Retrieve full execution status, scores, and stage breakdown for a run."""
    return coordinator.get_run(run_id)


# --- 4. Real-Time Event Streaming (SSE) ---


@router.get("/runs/{run_id}/events", summary="Stream real-time execution events via SSE")
async def stream_run_events(
    run_id: str,
    request: Request,
    coordinator: AnalysisCoordinator = Depends(get_coordinator),
):
    """Server-Sent Events endpoint pushing real-time stage transitions and progress."""
    queue = coordinator.subscribe_events(run_id)

    async def event_generator():
        # First send initial ping and current state
        try:
            current_run = coordinator.get_run(run_id)
            init_payload = json.dumps({"type": "init", "run": current_run.model_dump()})
            yield f"event: init\ndata: {init_payload}\n\n"
        except Exception:
            pass

        try:
            while True:
                # Check client disconnected
                if await request.is_disconnected():
                    break

                try:
                    # Wait up to 15s for new event or send heartbeat comment
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                    payload = json.dumps(event.model_dump())
                    yield f"event: {event.event_type}\ndata: {payload}\n\n"

                    # If run reached terminal state, send terminal marker
                    if event.event_type in ("run.completed", "run.failed"):
                        yield f"event: done\ndata: {json.dumps({'status': 'finished'})}\n\n"
                        break
                except asyncio.TimeoutError:
                    # Send keep-alive heartbeat
                    yield ": heartbeat\n\n"
        finally:
            coordinator.unsubscribe_events(run_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# --- 5. Screenshots & Visual Artifacts ---


@router.get("/runs/{run_id}/screenshots", summary="List captured screenshots for run")
async def get_run_screenshots(
    run_id: str,
    coordinator: AnalysisCoordinator = Depends(get_coordinator),
):
    """Get desktop and mobile screenshot metadata for a run."""
    return coordinator.get_screenshots(run_id)


@router.get("/runs/{run_id}/artifacts/screenshot", summary="Safely serve screenshot image file")
async def serve_screenshot_file(
    run_id: str,
    file: str = Query(..., description="Relative screenshot image path"),
    coordinator: AnalysisCoordinator = Depends(get_coordinator),
):
    """Serve a PNG screenshot image file safely preventing directory traversal."""
    target_path = coordinator.resolve_screenshot_path(run_id, file)
    return FileResponse(path=str(target_path), media_type="image/png", filename=target_path.name)


# --- 6. Findings & Recommendations ---


@router.get("/runs/{run_id}/findings", summary="Get aggregated findings across all agents")
async def get_run_findings(
    run_id: str,
    agent: Optional[str] = Query(None, description="Filter by agent ID"),
    coordinator: AnalysisCoordinator = Depends(get_coordinator),
):
    """Retrieve all structured findings across analyzed stages."""
    return coordinator.get_findings(run_id, agent_filter=agent)


@router.get("/runs/{run_id}/recommendations", summary="Get aggregated prioritized recommendations")
async def get_run_recommendations(
    run_id: str,
    priority: Optional[str] = Query(None, description="Filter by priority (p1, p2, p3)"),
    coordinator: AnalysisCoordinator = Depends(get_coordinator),
):
    """Retrieve all prioritized recommendations across analyzed stages."""
    return coordinator.get_recommendations(run_id, priority_filter=priority)


# --- 7. Reports ---


@router.get("/runs/{run_id}/ai-automation", summary="Get AI & Automation Analysis Report")
async def get_run_ai_automation(
    run_id: str,
    coordinator: AnalysisCoordinator = Depends(get_coordinator),
):
    """Retrieve dedicated AI & Automation presence detection, maturity score, and tailored blueprint."""
    from site_dna.analysis.ai_automation.analyzer import AIAutomationAnalyzer
    analyzer = AIAutomationAnalyzer(base_dir=coordinator.base_dir)
    return analyzer.analyze_run(run_id)


@router.get("/runs/{run_id}/reports/{stage_id}", summary="Get Markdown or JSON report content")
async def get_run_report(
    run_id: str,
    stage_id: str,
    format: str = Query("markdown", pattern="^(markdown|json)$"),
    coordinator: AnalysisCoordinator = Depends(get_coordinator),
):
    """Retrieve the generated analysis report text in Markdown or JSON format."""
    return coordinator.get_report(run_id, stage_id, format_type=format)
