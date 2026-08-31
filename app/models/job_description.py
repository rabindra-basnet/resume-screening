"""Job description data models."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    """A parsed job description with extracted requirements.

    Attributes:
        id: Unique identifier for the job description (empty for new items).
        title: Job title of the posting.
        raw_text: The original untruncated job description text.
        min_work_experience: Minimum required years of experience, if stated.
        max_work_experience: Maximum expected years of experience, if stated.
        skills: List of skills required by the job.
        created_at: Timestamp when the job description was created.
    """

    id: str | None = None
    title: str | None = None
    raw_text: str
    min_work_experience: float | None = None
    max_work_experience: float | None = None
    skills: list[str] = Field(default_factory=list)
    created_at: datetime | None = None


class JobDescriptionCreate(BaseModel):
    """Request payload for creating a new job description.

    Attributes:
        title: Job title of the posting.
        raw_text: The raw text content of the job description.
    """

    title: str
    raw_text: str
