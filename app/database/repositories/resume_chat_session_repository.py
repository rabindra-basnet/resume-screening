"""Repository for persisting and retrieving resume chat sessions."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schema import ResumeChatSessionModel

logger = logging.getLogger(__name__)


class ResumeChatSessionRepository:
    """Data access for :class:`ResumeChatSessionModel` rows.

    Args:
        session: An async SQLAlchemy session to operate on.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async session."""
        self.session = session

    async def create(
        self,
        *,
        user_id: str | None,
        resume_text: str,
        industry: str | None = None,
        jd_text: str | None = None,
        edit_session_id: str | None = None,
        screening_id: str | None = None,
    ) -> ResumeChatSessionModel:
        """Create a new chat session.

        Args:
            user_id: Owning user.
            resume_text: Snapshot of the resume text.
            industry: Optional target industry.
            jd_text: Optional job description text.
            edit_session_id: Optional linked edit session.
            screening_id: Optional linked screening.

        Returns:
            The created :class:`ResumeChatSessionModel`.
        """
        row = ResumeChatSessionModel(
            user_id=user_id,
            resume_text=resume_text,
            industry=industry,
            jd_text=jd_text,
            edit_session_id=edit_session_id,
            screening_id=screening_id,
            history=[],
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def get(self, session_id: str) -> ResumeChatSessionModel | None:
        """Fetch a single chat session by id.

        Args:
            session_id: The chat session primary key.

        Returns:
            The matching row or ``None``.
        """
        return await self.session.get(ResumeChatSessionModel, session_id)

    async def update_history(
        self, session_id: str, history: list
    ) -> ResumeChatSessionModel | None:
        """Persist the updated message history.

        Args:
            session_id: The chat session id.
            history: The full JSON-able message history.

        Returns:
            The updated row, or ``None`` if not found.
        """
        row = await self.session.get(ResumeChatSessionModel, session_id)
        if row is None:
            return None
        row.history = history
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def list_by_user(
        self, user_id: str, *, limit: int = 20
    ) -> list[ResumeChatSessionModel]:
        """Return chat sessions owned by a specific user.

        Args:
            user_id: The owner's user ID.
            limit: Maximum rows to return.

        Returns:
            A list of chat session rows, newest first.
        """
        stmt = (
            select(ResumeChatSessionModel)
            .where(ResumeChatSessionModel.user_id == user_id)
            .order_by(ResumeChatSessionModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
