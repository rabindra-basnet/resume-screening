"""Repository for persisting and retrieving job descriptions."""

from __future__ import annotations

import hashlib
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schema import JobDescriptionModel
from app.models.job_description import JobDescription

logger = logging.getLogger(__name__)


class JDRepository:
    """Data access for :class:`JobDescriptionModel` rows.

    Provides an in-process cache keyed by the SHA-256 hash of the raw text to
    avoid repeated LLM extraction of the same job description on serverless
    instances.
    """

    _cache: dict[str, JobDescriptionModel] = {}
    _CACHE_MAX: int = 64

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async session."""
        self.session = session

    @staticmethod
    def _digest(text: str) -> str:
        """Return the SHA-256 hexdigest of the given text.

        Args:
            text: The raw job description text.

        Returns:
            A 64-character hexadecimal digest.
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @staticmethod
    def _from_model(model: JobDescriptionModel) -> JobDescription:
        """Convert an ORM row into a :class:`JobDescription`.

        Args:
            model: The ORM job description row.

        Returns:
            The corresponding Pydantic job description.
        """
        return JobDescription(
            id=model.id,
            title=model.title,
            raw_text=model.raw_text,
            min_work_experience=model.min_experience_years,
            max_work_experience=model.max_experience_years,
            skills=list(model.extracted_skills or []),
            created_at=model.created_at,
        )

    async def get(self, jd_id: str) -> JobDescriptionModel | None:
        """Fetch a job description by id.

        Args:
            jd_id: The job description primary key.

        Returns:
            The matching ORM row or ``None`` if not found.
        """
        return await self.session.get(JobDescriptionModel, jd_id)

    async def find_by_text(self, raw_text: str) -> JobDescription | None:
        """Look up a job description by its raw text hash.

        Checks the in-process cache first, then queries the database.

        Args:
            raw_text: The raw job description text.

        Returns:
            The matching :class:`JobDescription` if found, else ``None``.
        """
        digest = self._digest(raw_text)
        cached = self._cache.get(digest)
        if cached is not None:
            return self._from_model(cached)

        stmt = select(JobDescriptionModel).where(JobDescriptionModel.raw_text == raw_text)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is not None:
            self._cache_row(digest, row)
        return self._from_model(row) if row is not None else None

    def _cache_row(self, digest: str, row: JobDescriptionModel) -> None:
        """Insert a row into the bounded LRU-like in-process cache.

        Args:
            digest: The text hash used as the cache key.
            row: The ORM row to cache.
        """
        if len(self._cache) >= self._CACHE_MAX:
            # Drop the oldest entry (rough approximation of LRU).
            self._cache.pop(next(iter(self._cache)))
        self._cache[digest] = row

    async def upsert(self, job: JobDescription) -> JobDescriptionModel:
        """Create or update a job description row.

        If a row already exists for the raw text, its fields are updated;
        otherwise a new row is inserted.

        Args:
            job: The structured job description to persist.

        Returns:
            The persisted ORM row.
        """
        row = await self.find_by_text(job.raw_text)
        if row is not None:
            model = await self.session.get(JobDescriptionModel, row.id)
        else:
            model = JobDescriptionModel(raw_text=job.raw_text)

        if model is None:  # pragma: no cover - defensive; find_by_text returned id
            model = JobDescriptionModel(raw_text=job.raw_text)

        model.title = job.title
        model.extracted_skills = job.skills
        model.min_experience_years = job.min_work_experience
        model.max_experience_years = job.max_work_experience

        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        self._cache_row(self._digest(job.raw_text), model)
        return model
