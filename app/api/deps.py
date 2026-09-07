"""FastAPI dependency-injection helpers."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_database
from app.database.repositories import LearningRepository, ProviderRepository
from app.database.schema import UserModel
from app.services import (
    ResumeChatService,
    ResumeEditService,
    ResumeReviewService,
    ScreeningService,
)

logger = logging.getLogger(__name__)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session and close it after the request.

    Yields:
        An :class:`AsyncSession` scoped to the current request.
    """
    db = get_database()
    async with db.session() as session:
        yield session


@dataclass(frozen=True)
class CurrentUser:
    """Common auth-scoped dependency: the request session and authenticated user.

    Endpoints that need both the database session and the currently
    authenticated user can declare a single ``CurrentUser`` dependency
    instead of repeating ``Depends(get_session)`` plus
    ``Depends(get_current_user)``.
    """

    session: AsyncSession
    user: UserModel

    @property
    def user_id(self) -> str:
        """The authenticated user's database id."""
        return self.user.id


async def _resolve_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[UserModel, Depends(get_current_user)],
) -> CurrentUser:
    """Bundle the session and current user into a single dependency."""
    return CurrentUser(session=session, user=current_user)


# Re-export the injected type alias for use in route signatures.
CurrentUserDep = Annotated[CurrentUser, Depends(_resolve_current_user)]


async def _decode_session_user(request: Request, session: AsyncSession) -> UserModel | None:
    """Resolve the authenticated user from the server-side session cookie.

    The cookie holds an opaque session id (no signed payload). The session row
    — created at Google OAuth login and bound to the validated Google JWT — is
    looked up in the database; expired or missing rows return ``None``.

    Args:
        request: The incoming request carrying the session cookie.
        session: The request-scoped async database session.

    Returns:
        The authenticated :class:`UserModel`, or ``None``.
    """
    from app.config.settings import get_settings
    from app.database.repositories.session_repository import SessionRepository

    settings = get_settings()
    session_id = request.cookies.get(settings.session_cookie_name)
    if not session_id:
        return None
    repo = SessionRepository(session)
    row = await repo.get_with_user(session_id)
    if row is None:
        return None
    db_session, user = row
    now = datetime.now(UTC)
    expires_at = db_session.expires_at
    if expires_at.tzinfo is None:  # SQLite stores naive datetimes (UTC wall time)
        expires_at = expires_at.replace(tzinfo=UTC)
    if expires_at <= now:
        logger.info("Expired session removed: %s", session_id)
        await repo.delete(session_id)
        return None
    return user


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


async def get_resume_review_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ResumeReviewService:
    """Construct a :class:`ResumeReviewService` bound to the request session.

    Injects the provider repository so the service can resolve user-configured
    BYOK providers for per-request LLM routing.

    Args:
        session: The async session provided by :func:`get_session`.

    Returns:
        A configured resume review service.
    """
    return ResumeReviewService(
        session=session,
        provider_repo=ProviderRepository(session),
    )


async def get_resume_edit_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ResumeEditService:
    """Construct a :class:`ResumeEditService` bound to the request session.

    Args:
        session: The async session provided by :func:`get_session`.

    Returns:
        A configured resume editing service.
    """
    return ResumeEditService(session=session)


async def get_resume_chat_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ResumeChatService:
    """Construct a :class:`ResumeChatService` bound to the request session.

    Injects the provider repository for per-request LLM routing.

    Args:
        session: The async session provided by :func:`get_session`.

    Returns:
        A configured resume chat service.
    """
    return ResumeChatService(
        session=session,
        provider_repo=ProviderRepository(session),
    )
