"""FastAPI application factory and assembly.

Builds the ASGI application with routers, middleware, and lifecycle hooks.
Exposes both an ``app`` instance for ASGI servers (uVicorn / Vercel) and a CLI
entry point for local development.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1 import (
    external_jobs_router,
    health_router,
    jd_router,
    learning_router,
    providers_router,
    screening_router,
)
from app.config.constants import API_V1_PREFIX
from app.config.settings import get_settings
from app.database import get_database

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle.

    Args:
        app: The FastAPI application instance.

    Yields:
        Control back to the ASGI server while the app is running.
    """
    settings = get_settings()
    logger.info("Starting %s (%s)", settings.app_name, settings.app_env)
    yield
    db = get_database()
    await db.dispose()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        A fully wired :class:`FastAPI` instance.
    """
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        description="Agentic resume screening and matching API",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router, prefix=API_V1_PREFIX)
    app.include_router(jd_router, prefix=API_V1_PREFIX)
    app.include_router(screening_router, prefix=API_V1_PREFIX)
    app.include_router(providers_router, prefix=API_V1_PREFIX)
    app.include_router(learning_router, prefix=API_V1_PREFIX)
    app.include_router(external_jobs_router, prefix=API_V1_PREFIX)

    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    @app.get("/")
    async def index(request: Request):
        return templates.TemplateResponse(request, "index.html")

    @app.get("/jobs")
    async def jobs_page(request: Request):
        return templates.TemplateResponse(request, "jobs.html")

    @app.get("/screen")
    async def screen_page(request: Request):
        return templates.TemplateResponse(request, "screen.html")

    @app.get("/admin/learning")
    async def admin_learning_page(request: Request):
        return templates.TemplateResponse(request, "admin_learning.html")

    # ── AetherGate Gateway UI ──────────────────────────────────────────
    @app.get("/gateway/providers")
    async def gateway_providers(request: Request):
        return templates.TemplateResponse(
            request, "aether/providers.html", {"active_page": "providers"}
        )

    @app.get("/gateway/providers/{provider_id}")
    async def gateway_provider_detail(request: Request, provider_id: str):
        return templates.TemplateResponse(
            request,
            "aether/provider_detail.html",
            {"active_page": "providers", "provider_id": provider_id},
        )

    @app.get("/gateway/routing")
    async def gateway_routing(request: Request):
        return templates.TemplateResponse(
            request, "aether/routing.html", {"active_page": "routing"}
        )

    @app.get("/gateway/vault")
    async def gateway_vault(request: Request):
        return templates.TemplateResponse(
            request, "aether/vault.html", {"active_page": "vault"}
        )

    return app


app = create_app()


def cli_entry() -> None:
    """Run the application locally via uvicorn."""
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104 - local dev only


if __name__ == "__main__":
    cli_entry()
