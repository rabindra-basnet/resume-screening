"""Async database engine and session management.

Encapsulates SQLAlchemy async setup and provides a lightweight dependency for
FastAPI. For SQLite it uses ``aiosqlite``; for PostgreSQL (production) it uses
``asyncpg``. Connection pooling parameters are conservative for serverless
environments to avoid resource exhaustion.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import get_settings

logger = logging.getLogger(__name__)


class Database:
    """Holds the async engine and session factory for the application.

    Args:
        url: SQLAlchemy async database URL.
        echo: Whether to log emitted SQL statements.
    """

    def __init__(self, url: str, echo: bool = False) -> None:
        """Create the async engine and session factory for the given URL."""
        # SQLite requires aiosqlite driver; normalize the URL safely.
        if url.startswith("sqlite://"):
            url = url.replace("sqlite:///", "sqlite+aiosqlite:///")
        connect_args: dict = {}
        if "sqlite" in url:
            connect_args = {"check_same_thread": False}

        self.engine: AsyncEngine = create_async_engine(
            url,
            echo=echo,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        self.session_factory = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def dispose(self) -> None:
        """Dispose of the engine, releasing pooled connections."""
        await self.engine.dispose()

    def session(self) -> AsyncSession:
        """Return a new async session from the factory.

        Returns:
            A configured :class:`AsyncSession`.
        """
        return self.session_factory()


@lru_cache(maxsize=1)
def get_database() -> Database:
    """Return a cached singleton :class:`Database` instance.

    Returns:
        The configured database singleton.
    """
    settings = get_settings()
    return Database(url=settings.database_url, echo=settings.debug)
