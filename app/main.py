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
    resume_chat_router,
    resume_edit_router,
    resume_review_router,
    screening_router,
)
from app.config.constants import API_V1_PREFIX
from app.config.settings import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import RequestContextMiddleware
from app.core.telemetry import configure_sentry
from app.database import get_database

BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIST = BASE_DIR / "ui" / "dist"

logger = logging.getLogger(__name__)

settings = get_settings()
configure_logging(
    level=settings.log_level,
    file_path=settings.log_file or None,
    max_bytes=settings.log_file_max_bytes,
    backup_count=settings.log_file_backup_count,
    verbose=settings.app_env in ("development", "staging"),
)


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
    configure_sentry(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=settings.sentry_traces_sample_rate,
    )
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
        RequestContextMiddleware,
        log_requests=settings.log_requests,
    )

    # Restrict allowed origins for security when credentials are sent
    allowed_origins = [
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "https://ats.saastralabs.com",
    ]
    if settings.app_origin and settings.app_origin not in allowed_origins:
        allowed_origins.append(settings.app_origin.rstrip("/"))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        # Dedicated cookie for the OAuth ``state`` hand-off. Using the same name
        # as the auth cookie (session_cookie_name) makes the middleware clobber
        # the signed user session issued by /callback/google.
        session_cookie=settings.oauth_state_cookie_name,
        max_age=settings.session_cookie_max_age,
        same_site="lax",
        https_only=settings.app_env == "production",
    )

    register_exception_handlers(app)

    app.include_router(health_router, prefix=API_V1_PREFIX)
    app.include_router(auth_router, prefix=API_V1_PREFIX)
    app.include_router(account_router, prefix=API_V1_PREFIX)
    app.include_router(jd_router, prefix=API_V1_PREFIX)
    app.include_router(screening_router, prefix=API_V1_PREFIX)
    app.include_router(providers_router, prefix=API_V1_PREFIX)
    app.include_router(learning_router, prefix=API_V1_PREFIX)
    app.include_router(external_jobs_router, prefix=API_V1_PREFIX)
    app.include_router(resume_review_router, prefix=API_V1_PREFIX)
    app.include_router(resume_edit_router, prefix=API_V1_PREFIX)
    app.include_router(resume_chat_router, prefix=API_V1_PREFIX)

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
