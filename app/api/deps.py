"""FastAPI dependency-injection helpers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_database
from app.database.repositories import LearningRepository, ProviderRepository
from app.database.schema import UserModel
from app.services import ScreeningService


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session and close it after the request.

    Yields:
        An :class:`AsyncSession` scoped to the current request.
    """
    db = get_database()
    async with db.session() as session:
        yield session


async def _decode_session_user(request: Request, session: AsyncSession) -> UserModel | None:
    """Decode the signed session cookie and return the user, or ``None``."""
    from app.config.settings import get_settings

    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        return None
    try:
        from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

        signer = URLSafeTimedSerializer(settings.session_secret)
        data = signer.loads(token, max_age=settings.session_cookie_max_age)
        user_id = data.get("user_id")
        if not user_id:
            return None
        return await session.get(UserModel, user_id)
    except (BadSignature, SignatureExpired):
        return None


async def get_current_user(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserModel:
    """FastAPI dependency that returns the authenticated user or raises 401.

    Raises:
        HTTPException: 401 if the session cookie is missing or invalid.
    """
    from fastapi import HTTPException

    user = await _decode_session_user(request, session)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_current_user_or_none(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserModel | None:
    """FastAPI dependency that returns the user or ``None`` (no 401)."""
    return await _decode_session_user(request, session)


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
