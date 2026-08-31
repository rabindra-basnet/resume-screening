"""Repository for persisting and retrieving screening results."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schema import ScreeningResultModel
from app.models.candidate import CandidateProfile
from app.models.evaluation import EvaluationResult

logger = logging.getLogger(__name__)


class ResumeRepository:
    """Data access for :class:`ScreeningResultModel` rows.

    Args:
        session: An async SQLAlchemy session to operate on.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async session."""
        self.session = session

    async def create(
        self,
        *,
        resume_filename: str,
        resume_text: str,
        candidate: CandidateProfile,
        evaluation: EvaluationResult,
        status: str,
        skill_match_percentage: float,
        llm_model_used: str | None = None,
        processing_time_ms: int | None = None,
        jd_id: str | None = None,
    ) -> ScreeningResultModel:
        """Persist a new screening result.

        Args:
            resume_filename: Original resume file name.
            resume_text: Extracted resume text.
            candidate: The extracted candidate profile.
            evaluation: The computed evaluation result.
            status: Candidate disposition status.
            skill_match_percentage: Computed match percentage.
            llm_model_used: Optional model used for the evaluation.
            processing_time_ms: Optional end-to-end processing time.
            jd_id: Optional referenced job description id.

        Returns:
            The persisted :class:`ScreeningResultModel`.
        """
        row = ScreeningResultModel(
            resume_filename=resume_filename,
            resume_text=resume_text,
            candidate_profile=candidate.model_dump(mode="json"),
            evaluation=evaluation.model_dump(mode="json"),
            status=status,
            skill_match_percentage=skill_match_percentage,
            llm_model_used=llm_model_used,
            processing_time_ms=processing_time_ms,
            jd_id=jd_id,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def get(self, result_id: str) -> ScreeningResultModel | None:
        """Fetch a single screening result by id.

        Args:
            result_id: The screening result primary key.

        Returns:
            The matching row or ``None`` if not found.
        """
        return await self.session.get(ScreeningResultModel, result_id)

    async def list(self, limit: int = 50) -> list[ScreeningResultModel]:
        """Return the most recent screening results.

        Args:
            limit: Maximum number of rows to return.

        Returns:
            A list of screening result rows, newest first.
        """
        stmt = (
            select(ScreeningResultModel)
            .order_by(ScreeningResultModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
