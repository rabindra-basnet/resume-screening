"""Repository for persisting and retrieving job applications."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schema import JobApplicationModel
from app.models.resume_workspace import JobApplicationPayload

logger = logging.getLogger(__name__)


class JobApplicationRepository:
    """Data access for :class:`JobApplicationModel` rows.

    Args:
        session: An async SQLAlchemy session to operate on.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async session."""
        self.session = session

    async def create(
        self,
        payload: JobApplicationPayload,
        *,
        user_id: str | None,
        edit_session_id: str | None = None,
    ) -> JobApplicationModel:
        """Create a new job application record.

        Args:
            payload: The application payload (final resume, cover letter, refs).
            user_id: Owning user.
            edit_session_id: Optional linked editing session.

        Returns:
            The persisted :class:`JobApplicationModel`.
        """
        row = JobApplicationModel(
            user_id=user_id,
            edit_session_id=edit_session_id,
            screening_id=payload.screening_id,
            job_id=payload.job_id,
            final_resume_text=payload.resume_text,
            cover_letter=payload.cover_letter,
            notes=payload.notes,
            status="submitted",
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def get(self, application_id: str) -> JobApplicationModel | None:
        """Fetch an application by id.

        Args:
            application_id: The application primary key.

        Returns:
            The matching row or ``None``.
        """
        return await self.session.get(JobApplicationModel, application_id)

    async def list_by_user(
        self, user_id: str, *, limit: int = 50
    ) -> list[JobApplicationModel]:
        """Return applications owned by a specific user.

        Args:
            user_id: The owner's user ID.
            limit: Maximum rows to return.

        Returns:
            A list of application rows, newest first.
        """
        stmt = (
            select(JobApplicationModel)
            .where(JobApplicationModel.user_id == user_id)
            .order_by(JobApplicationModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
