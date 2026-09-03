"""FastAPI dependency-injection helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_database
from app.database.repositories import LearningRepository, ProviderRepository
from app.services import ScreeningService


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session and close it after the request.

    Yields:
        An :class:`AsyncSession` scoped to the current request.
    """
    db = get_database()
    async with db.session() as session:
        yield session


async def get_screening_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScreeningService:
    """Construct a :class:`ScreeningService` bound to the request session.

    Injects the provider repository so the service can resolve user-configured
    BYOK providers for per-request LLM routing.

    Args:
        session: The async session provided by :func:`get_session`.

    Returns:
        A configured screening service.
    """
    return ScreeningService(
        session=session,
        provider_repo=ProviderRepository(session),
    )


async def get_provider_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProviderRepository:
    """Construct a :class:`ProviderRepository` bound to the request session.

    Args:
        session: The async session provided by :func:`get_session`.

    Returns:
        A configured provider repository.
    """
    return ProviderRepository(session)


async def get_learning_repo(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> LearningRepository:
    """Construct a :class:`LearningRepository` bound to the request session.

    Args:
        session: The async session provided by :func:`get_session`.

    Returns:
        A configured learning repository.
    """
    return LearningRepository(session)
