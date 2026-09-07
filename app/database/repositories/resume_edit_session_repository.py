"""Repository for persisting and retrieving resume editing sessions."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schema import ResumeEditSessionModel

logger = logging.getLogger(__name__)


class ResumeEditSessionRepository:
    """Data access for :class:`ResumeEditSessionModel` rows.

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
        content: str,
        resume_filename: str | None = None,
        resume_blob_url: str | None = None,
    ) -> ResumeEditSessionModel:
        """Create a new editing session seeded with initial resume content.

        Args:
            user_id: Owning user.
            content: Initial resume text (line-based).
            resume_filename: Optional original filename.
            resume_blob_url: Optional original document blob URL.

        Returns:
            The created :class:`ResumeEditSessionModel`.
        """
        row = ResumeEditSessionModel(
            user_id=user_id,
            content=content,
            resume_filename=resume_filename,
            resume_blob_url=resume_blob_url,
            undo_stack=[],
            redo_stack=[],
            revision=0,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def get(self, session_id: str) -> ResumeEditSessionModel | None:
        """Fetch a single editing session by id.

        Args:
            session_id: The editing session primary key.

        Returns:
            The matching row or ``None``.
        """
        return await self.session.get(ResumeEditSessionModel, session_id)

    async def update_content(
        self,
        session_id: str,
        *,
        content: str,
        undo_stack: list,
        redo_stack: list,
        revision: int,
    ) -> ResumeEditSessionModel | None:
        """Persist updated content and edit stacks.

        Args:
            session_id: The editing session id.
            content: The new full resume text.
            undo_stack: The updated undo stack (JSON-able).
            redo_stack: The updated redo stack (JSON-able).
            revision: The new revision number.

        Returns:
            The updated row, or ``None`` if not found.
        """
        row = await self.session.get(ResumeEditSessionModel, session_id)
        if row is None:
            return None
        row.content = content
        row.undo_stack = undo_stack
        row.redo_stack = redo_stack
        row.revision = revision
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def list_by_user(
        self, user_id: str, *, limit: int = 20
    ) -> list[ResumeEditSessionModel]:
        """Return editing sessions owned by a specific user.

        Args:
            user_id: The owner's user ID.
            limit: Maximum rows to return.

        Returns:
            A list of editing session rows, newest first.
        """
        stmt = (
            select(ResumeEditSessionModel)
            .where(ResumeEditSessionModel.user_id == user_id)
            .order_by(ResumeEditSessionModel.updated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
