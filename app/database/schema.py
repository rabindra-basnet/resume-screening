"""SQLAlchemy ORM schema definitions.

Defines the database tables used to persist job descriptions and screening
results. The schema maps closely to the shared Pydantic boundaries but is
independently modeled for storage concerns (e.g. JSON columns, timestamps).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Float, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


def _uuid() -> str:
    """Return a fresh UUID string for primary key defaults."""
    return str(uuid.uuid4())


class JobDescriptionModel(Base):
    """ORM model representing a stored job description.

    Attributes:
        id: Primary key (UUID string).
        title: Job title of the posting.
        raw_text: The full raw job description text.
        extracted_skills: JSON list of required skills.
        min_experience_years: Minimum required experience in years.
        max_experience_years: Maximum expected experience in years.
        created_at: Row creation timestamp.
        updated_at: Row last-update timestamp.
    """

    __tablename__ = "job_descriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_skills: Mapped[list] = mapped_column(JSON, default=list)
    min_experience_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_experience_years: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ScreeningResultModel(Base):
    """ORM model representing a completed candidate screening.

    Attributes:
        id: Primary key (UUID string).
        jd_id: Foreign key to an optional stored job description.
        resume_filename: Original name of the uploaded resume file.
        resume_text: Extracted text from the resume.
        candidate_profile: JSON blob of the extracted candidate profile.
        evaluation: JSON blob of the evaluation result.
        status: Candidate disposition string.
        skill_match_percentage: Computed skill match percentage.
        llm_model_used: The model that produced the evaluation.
        processing_time_ms: End-to-end processing time in milliseconds.
        created_at: Row creation timestamp.
    """

    __tablename__ = "screening_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    jd_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    resume_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    candidate_profile: Mapped[dict] = mapped_column(JSON, default=dict)
    evaluation: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    skill_match_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    llm_model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
