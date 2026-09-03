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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1 import (
    account_router,
    auth_router,
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
UI_DIST = BASE_DIR / "ui" / "dist"

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

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie=settings.session_cookie_name,
        max_age=settings.session_cookie_max_age,
        same_site="lax",
    )

    app.include_router(health_router, prefix=API_V1_PREFIX)
    app.include_router(auth_router, prefix=API_V1_PREFIX)
    app.include_router(account_router, prefix=API_V1_PREFIX)
    app.include_router(jd_router, prefix=API_V1_PREFIX)
    app.include_router(screening_router, prefix=API_V1_PREFIX)
    app.include_router(providers_router, prefix=API_V1_PREFIX)
    app.include_router(learning_router, prefix=API_V1_PREFIX)
    app.include_router(external_jobs_router, prefix=API_V1_PREFIX)

    # ── React SPA ──────────────────────────────────────────────────────
    # Serve the built React app (ui/dist) as a single-page application.
    # Handles static assets plus client-side routing fallback to index.html.
    if UI_DIST.exists() and (UI_DIST / "index.html").is_file():
        _index_html = (UI_DIST / "index.html").read_text(encoding="utf-8")

        @app.get("/", include_in_schema=False)
        async def spa_root() -> HTMLResponse:
            return HTMLResponse(_index_html)

        @app.get("/{spa_path:path}", include_in_schema=False, response_model=None)
        async def spa_fallback(spa_path: str):
            # Serve existing static assets (js/css/fonts/icons).
            target = UI_DIST / spa_path
            if spa_path and target.is_file():
                return FileResponse(target)
            # Anything else returns index.html for the SPA's router.
            return HTMLResponse(_index_html)
    else:
        logger.warning("React UI not built: %s. Run `npm run build` in ui/.", UI_DIST)

        @app.get("/", include_in_schema=False)
        async def placeholder_root() -> HTMLResponse:
            return HTMLResponse(
                "<h1>Resume Screening API</h1><p>React UI not built. "
                "Run <code>npm run build</code> in <code>ui/</code>.</p>"
            )

    return app


app = create_app()


def cli_entry() -> None:
    """Run the application locally via uvicorn."""
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104 - local dev only


if __name__ == "__main__":
    cli_entry()
