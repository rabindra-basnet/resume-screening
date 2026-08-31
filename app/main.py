"""FastAPI application factory and assembly.

Builds the ASGI application with routers, middleware, and lifecycle hooks.
Exposes both an ``app`` instance for ASGI servers (uVicorn / Vercel) and a CLI
entry point for local development.
"""

from __future__ import annotations

import logging
from asyncio import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health_router, jd_router, screening_router
from app.config.constants import API_V1_PREFIX
from app.config.settings import get_settings
from app.database import get_database

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

    return app


app = create_app()


def cli_entry() -> None:
    """Run the application locally via uvicorn."""
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)  # nosec B104 - local dev only


if __name__ == "__main__":
    cli_entry()
