"""Repository for persisting and retrieving login sessions."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schema import SessionModel, UserModel


class SessionRepository:
    """Data access for :class:`SessionModel` rows.

    Args:
        session: An async SQLAlchemy session to operate on.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: str,
        google_id_token: str,
        google_access_token: str | None = None,
        token_expires_at: datetime | None = None,
        expires_at: datetime,
    ) -> SessionModel:
        """Persist a new session bound to the user and the Google JWT.

        Args:
            user_id: Id of the authenticated user.
            google_id_token: The validated Google JWT (``id_token``).
            google_access_token: Optional Google access token.
            token_expires_at: Expiry of the Google JWT itself.
            expires_at: When this app session becomes invalid.

        Returns:
            The persisted :class:`SessionModel`.
        """
        row = SessionModel(
            user_id=user_id,
            google_id_token=google_id_token,
            google_access_token=google_access_token,
            token_expires_at=token_expires_at,
            expires_at=expires_at,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def get_with_user(self, session_id: str) -> tuple[SessionModel, UserModel] | None:
        """Fetch a session row together with its user by session id.

        Args:
            session_id: The session primary key (the cookie value).

        Returns:
            A ``(session, user)`` tuple, or ``None`` if no such session exists.
        """
        stmt = (
            select(SessionModel, UserModel)
            .join(UserModel, SessionModel.user_id == UserModel.id)
            .where(SessionModel.id == session_id)
        )
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None
        return row[0], row[1]

    async def delete(self, session_id: str) -> None:
        """Delete a session row (logout / revocation).

        Args:
            session_id: The session primary key to delete.
        """
        row = await self.session.get(SessionModel, session_id)
        if row is not None:
            await self.session.delete(row)
            await self.session.commit()
