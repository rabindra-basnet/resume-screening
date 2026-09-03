"""Async database engine and session management.

Encapsulates SQLAlchemy async setup and provides a lightweight dependency for
FastAPI. For SQLite it uses ``aiosqlite``; for PostgreSQL (production) it uses
``asyncpg``. Connection pooling parameters are conservative for serverless
environments to avoid resource exhaustion.
"""

from __future__ import annotations

import logging
import re
from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

_POSTGRES_SCHEME_RE = re.compile(r"^postgres(ql)?$")
_SSL_QUERY_KEYS = {"sslmode", "channel_binding"}


def _normalize_postgres_url(url: str) -> tuple[str, dict]:
    """Convert a ``postgres(ql)://`` URL to asyncpg and pull out SSL settings.

    asyncpg does not accept ``sslmode``/``channel_binding`` query parameters the
    way psycopg does; it configures SSL via a runtime ``ssl`` connect argument.
    This helper strips those params and returns the normalized asyncpg URL plus
    the SSL kwargs an asyncpg connection should use.

    Args:
        url: The original SQLAlchemy database URL.

    Returns:
        A ``(normalized_url, asyncpg_connect_kwargs)`` tuple.
    """
    scheme = urlsplit(url).scheme
    if not _POSTGRES_SCHEME_RE.match(scheme):
        return url, {}

    # Normalize to the asyncpg driver.
    rest = url[len(scheme):]
    url = f"postgresql+asyncpg{rest}"

    parts = urlsplit(url)
    query = parse_qsl(parts.query, keep_blank_values=True)
    connect_kwargs: dict = {}
    keep: list[tuple[str, str]] = []
    for key, value in query:
        if key in _SSL_QUERY_KEYS:
            if key == "sslmode" and value in {"require", "verify-ca", "verify-full"}:
                connect_kwargs.setdefault("ssl", True)
            elif key == "sslmode" and value in {"disable", "allow", "prefer"}:
                connect_kwargs["ssl"] = False
            continue
        keep.append((key, value))

    parts = parts._replace(query=urlencode(keep))
    return urlunsplit(parts), connect_kwargs


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
        # Postgres needs an async driver (asyncpg) and SSL handling.
        if _POSTGRES_SCHEME_RE.match(urlsplit(url).scheme):
            url, ssl_kwargs = _normalize_postgres_url(url)
        else:
            ssl_kwargs = {}

        connect_args: dict = {}
        if "sqlite" in url:
            connect_args = {"check_same_thread": False}
        else:
            connect_args.update(ssl_kwargs)

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
