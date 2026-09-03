import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.database.schema import Base
from app.config.settings import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def _normalize_database_url(url: str) -> str:
    """Normalize the database URL for async drivers.

    Mirrors the logic in ``app.database.connection.Database`` so Alembic
    uses the same driver as the application runtime.  Strips query params
    that are psycopg2-specific (e.g. ``sslmode``, ``channel_binding``)
    and translates ``sslmode=require`` into asyncpg's ``ssl=require``.
    """
    if url.startswith("sqlite://"):
        url = url.replace("sqlite:///", "sqlite+aiosqlite:///")
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql+asyncpg://", 1)

    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    parsed = urlparse(url)
    if parsed.query:
        params = parse_qs(parsed.query)
        needs_ssl = "require" in params.pop("sslmode", [])
        for key in ("channel_binding", "ssrootcert", "sslcert", "sslkey"):
            params.pop(key, None)
        if needs_ssl:
            params["ssl"] = ["require"]
        new_query = urlencode(params, doseq=True)
        url = urlunparse(parsed._replace(query=new_query))

    return url


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with an async engine."""
    settings = get_settings()
    url = _normalize_database_url(settings.database_url)
    config.set_main_option("sqlalchemy.url", url)

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
