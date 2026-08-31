"""FastAPI dependency-injection helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_database
from app.services import ScreeningService

_db = get_database()


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session and close it after the request.

    Yields:
        An :class:`AsyncSession` scoped to the current request.
    """
    async with _db.session() as session:
        yield session


async def get_screening_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ScreeningService:
    """Construct a :class:`ScreeningService` bound to the request session.

    Args:
        session: The async session provided by :func:`get_session`.

    Returns:
        A configured screening service.
    """
    return ScreeningService(session=session)
