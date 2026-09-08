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
from starlette.middleware.sessions import SessionMiddleware

from app.api.v1 import (
    account_router,
    auth_router,
    external_jobs_router,
    health_router,
    jd_router,
    learning_router,
    llm_router,
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
from app.database import get_database

BASE_DIR = Path(__file__).resolve().parent.parent
UI_DIST = BASE_DIR / "ui" / "dist"

logger = logging.getLogger(__name__)

settings = get_settings()
# Serverless platforms (Vercel) mount a read-only filesystem; file logging is
# a local-dev convenience only. In production, logs go to stdout (the console),
# which the platform collects.
verbose = settings.app_env in ("development", "staging")
configure_logging(
    file_path=None if settings.app_env == "production" else f"logs/{settings.app_env}.log",
    verbose=verbose,
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

    app.add_middleware(RequestContextMiddleware)

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
    app.include_router(llm_router, prefix=API_V1_PREFIX)
    app.include_router(external_jobs_router, prefix=API_V1_PREFIX)
    app.include_router(resume_review_router, prefix=API_V1_PREFIX)
    app.include_router(resume_edit_router, prefix=API_V1_PREFIX)
    app.include_router(resume_chat_router, prefix=API_V1_PREFIX)

    # ── React SPA ──────────────────────────────────────────────────────
    # Serve the built React app (ui/dist) as a single-page application using
    # FastAPI's built-in frontend feature (FastAPI 0.115+).
    # Automatically handles static assets, API route precedence, and fallback
    # to index.html for client-side routing.
    app.frontend("/", directory=UI_DIST)

    return app


app = create_app()


def cli_entry() -> None:
    """Run the application locally via uvicorn."""
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104 - local dev only


if __name__ == "__main__":
    cli_entry()
