"""Repository for persisting and retrieving resume review results."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schema import ResumeReviewModel

logger = logging.getLogger(__name__)


class ResumeReviewRepository:
    """Data access for :class:`ResumeReviewModel` rows.

    Args:
        session: An async SQLAlchemy session to operate on.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async session."""
        self.session = session

    async def create(
        self,
        *,
        resume_text: str,
        review_type: str,
        review_result: dict,
        resume_filename: str | None = None,
        jd_text: str | None = None,
        industry: str | None = None,
        llm_model_used: str | None = None,
        processing_time_ms: int | None = None,
        user_id: str | None = None,
    ) -> ResumeReviewModel:
        """Persist a new resume review result.

        Args:
            resume_text: Extracted resume text.
            review_type: Type of review performed.
            review_result: The review output as a dict.
            resume_filename: Optional original resume filename.
            jd_text: Optional job description text.
            industry: Optional target industry.
            llm_model_used: Optional model used.
            processing_time_ms: Optional processing duration.
            user_id: Optional owner user id.

        Returns:
            The persisted :class:`ResumeReviewModel`.
        """
        row = ResumeReviewModel(
            resume_text=resume_text,
            review_type=review_type,
            review_result=review_result,
            resume_filename=resume_filename,
            jd_text=jd_text,
            industry=industry,
            llm_model_used=llm_model_used,
            processing_time_ms=processing_time_ms,
            user_id=user_id,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def get(self, review_id: str) -> ResumeReviewModel | None:
        """Fetch a single review result by id.

        Args:
            review_id: The review result primary key.

        Returns:
            The matching row or ``None`` if not found.
        """
        return await self.session.get(ResumeReviewModel, review_id)

    async def list_by_user(
        self, user_id: str, *, limit: int = 50
    ) -> list[ResumeReviewModel]:
        """Return review results owned by a specific user.

        Args:
            user_id: The owner's user ID.
            limit: Maximum number of rows to return.

        Returns:
            A list of review result rows, newest first.
        """
        stmt = (
            select(ResumeReviewModel)
            .where(ResumeReviewModel.user_id == user_id)
            .order_by(ResumeReviewModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
