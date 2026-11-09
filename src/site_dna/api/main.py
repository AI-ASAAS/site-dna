"""FastAPI application initialization and lifecycle for Site DNA."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from site_dna import __version__
from site_dna.api.routes import (
    accessibility,
    competitor_intelligence,
    content_marketing,
    discovery,
    final_reports,
    health,
    runs,
    security_privacy,
    strategic_intelligence,
    technical_seo,
    ux_ui,
    visual,
    visual_identity,
)
from site_dna.core.config import get_settings
from site_dna.core.logging import get_logger, setup_logging

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context managing startup and shutdown."""
    settings = get_settings()
    setup_logging(level=settings.log_level)
    logger.info(
        "Starting Site DNA backend v%s [%s mode]",
        __version__,
        settings.app_env,
    )
    # Important: Do not make live LLM calls during startup to preserve local-first stability
    yield
    logger.info("Shutting down Site DNA backend")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Site DNA API",
        description="AI-powered website intelligence and strategic auditing platform (Phase 01)",
        version=__version__,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Local CORS middleware restricted to safe development origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:8000",
            "http://localhost:8000",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # Global safe error handler avoiding sensitive leakages
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled server exception: %s", type(exc).__name__, exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected server error occurred. Check server logs.",
            },
        )

    # Register modular routers
    app.include_router(health.router)
    app.include_router(runs.router)
    app.include_router(discovery.router)
    app.include_router(visual.router)
    app.include_router(visual_identity.router)
    app.include_router(ux_ui.router)
    app.include_router(content_marketing.router)
    app.include_router(technical_seo.router)
    app.include_router(competitor_intelligence.router)
    app.include_router(security_privacy.router)
    app.include_router(accessibility.router)
    app.include_router(strategic_intelligence.router)
    app.include_router(final_reports.router)

    # Frontend Distribution Mount & SPA Fallback
    frontend_dist = Path(__file__).resolve().parents[3] / "frontend" / "dist"
    if (frontend_dist / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(frontend_dist / "assets")), name="assets")

    # Serve public brand files (favicon, logo)
    for public_file in ("favicon.png", "logo-dark.png", "logo-light.png"):
        p_path = frontend_dist / public_file
        if p_path.exists():

            @app.get(f"/{public_file}", include_in_schema=False)
            async def get_public_file(p=p_path):
                return FileResponse(p)

    # Legacy developer dashboard
    @app.get("/dashboard/legacy", response_class=HTMLResponse, include_in_schema=False)
    async def get_legacy_dashboard():
        """Serve the developer HTML dashboard template."""
        tpl_path = Path(__file__).parent / "templates" / "dashboard.html"
        if tpl_path.exists():
            return HTMLResponse(content=tpl_path.read_text(encoding="utf-8"))
        return HTMLResponse(content="<h1>Legacy Dashboard</h1>")

    # SPA Entry & Fallback Handler
    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa_frontend(full_path: str):
        """Serve the production React + TypeScript Site DNA frontend."""
        # Never intercept API or documentation routes
        if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json"):
            return JSONResponse(status_code=404, content={"detail": "Not Found"})

        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return FileResponse(
                index_file,
                headers={
                    "Cache-Control": "no-cache, no-store, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                },
            )

        # Fallback to legacy dashboard if frontend dist is missing
        tpl_path = Path(__file__).parent / "templates" / "dashboard.html"
        if tpl_path.exists():
            return HTMLResponse(content=tpl_path.read_text(encoding="utf-8"))
        return HTMLResponse(content="<h1>Site DNA</h1><p>Frontend build missing. Run npm run build in /frontend.</p>")

    return app


app = create_app()
