"""SQLAlchemy ORM schema definitions.

Defines the database tables used to persist job descriptions, screening
results, and AI provider configurations (BYOK). The schema maps closely to
the shared Pydantic boundaries but is independently modeled for storage
concerns (e.g. JSON columns, timestamps, encrypted API keys).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String, Text, func
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


class UserModel(Base):
    """ORM model representing an authenticated user (Google OAuth).

    Attributes:
        id: Primary key (UUID string).
        email: User email from Google.
        name: Display name from Google.
        avatar_url: Profile picture URL from Google.
        google_id: Google OAuth subject ID.
        created_at: Row creation timestamp.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    google_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SessionModel(Base):
    """ORM model representing a server-side login session (Google JWT-backed).

    A row is created after a successful Google OAuth callback. It binds the
    authenticated user to the Google-issued JWT (``id_token``) that Google
    returned and whose signature/audience/issuer authlib already verified. The
    browser only ever receives an opaque session id in a cookie — the Google
    JWT never leaves the server — so a stolen cookie is revocable (delete the
    row) instead of being a valid bearer credential.

    Attributes:
        id: Primary key (UUID string); sent to the browser as the session cookie.
        user_id: Foreign key to the authenticated user.
        google_id_token: The validated Google JWT (``id_token``) from the flow.
        google_access_token: Google access token, kept for future API calls.
        token_expires_at: Expiry of the Google JWT (informational; the app
            session below may outlive the short-lived id_token).
        expires_at: When this app session becomes invalid.
        created_at: Row creation timestamp.
    """

    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    google_id_token: Mapped[str] = mapped_column(Text, nullable=False, default="")
    google_access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ScreeningResultModel(Base):
    """ORM model representing a completed candidate screening.

    Attributes:
        id: Primary key (UUID string).
        user_id: Owner of this screening result.
        jd_id: Foreign key to an optional stored job description.
        resume_filename: Original name of the uploaded resume file.
        resume_blob_url: Vercel Blob URL of the stored resume document.
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
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    jd_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    resume_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_blob_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    candidate_profile: Mapped[dict] = mapped_column(JSON, default=dict)
    evaluation: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    skill_match_percentage: Mapped[float] = mapped_column(Float, default=0.0)
    llm_model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIProviderModel(Base):
    """ORM model for user-configured AI provider with encrypted API key (BYOK).

    Attributes:
        id: Primary key (UUID string).
        name: Human-readable label for this provider configuration.
        provider: Provider slug (``openai``, ``anthropic``, ``azure``,
            ``google``, ``deepseek``, ``ollama``, ``openrouter``).
        model: The model identifier to use (e.g. ``gpt-4o``, ``claude-sonnet-4-20250514``).
        api_key_encrypted: Fernet-encrypted API key ciphertext.
        api_base: Optional base URL override for OpenAI-compatible endpoints.
        max_tokens: Max output tokens for this provider.
        temperature: Sampling temperature.
        is_active: Whether this is the active provider for screenings.
        is_validated: Whether the key has been validated successfully.
        created_at: Row creation timestamp.
        updated_at: Row last-update timestamp.
    """

    __tablename__ = "ai_providers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    api_base: Mapped[str | None] = mapped_column(String(512), nullable=True)
    max_tokens: Mapped[int] = mapped_column(default=2000)
    temperature: Mapped[float] = mapped_column(Float, default=0.1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    is_validated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class LearningResourceModel(Base):
    """ORM model representing a recommended learning resource for a skill gap.

    Attributes:
        id: Primary key (UUID string).
        screening_id: The screening result that surfaced this gap.
        skill: The skill this resource covers.
        title: Resource title.
        url: Link to the resource.
        resource_type: Type (course, article, video, book, practice, other).
        provider: Who provides the resource.
        description: Brief summary.
        estimated_hours: Approximate completion time.
        created_at: Row creation timestamp.
    """

    __tablename__ = "learning_resources"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    screening_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    skill: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), default="")
    resource_type: Mapped[str] = mapped_column(String(20), default="other")
    provider: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    estimated_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ResumeReviewModel(Base):
    """ORM model representing a resume review result from the review agents.

    Attributes:
        id: Primary key (UUID string).
        user_id: Owner of this review.
        resume_filename: Original name of the uploaded resume file.
        resume_text: Extracted text from the resume.
        review_type: Which review was run (full, brutal, ats, bullets, tone, polish).
        review_result: JSON blob of the review output.
        jd_text: Optional job description text (used for ATS review).
        industry: Optional target industry (used for tone matching).
        llm_model_used: The model that produced the review.
        processing_time_ms: End-to-end processing time in milliseconds.
        created_at: Row creation timestamp.
    """

    __tablename__ = "resume_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    resume_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    review_type: Mapped[str] = mapped_column(String(20), default="full")
    review_result: Mapped[dict] = mapped_column(JSON, default=dict)
    jd_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    llm_model_used: Mapped[str | None] = mapped_column(String(100), nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ResumeEditSessionModel(Base):
    """ORM model representing an active (or completed) resume editing session.

    Stores the current line-based resume content plus the undo/redo stacks so a
    user (or the chat agent) can edit the CV with full version control.

    Attributes:
        id: Primary key (UUID string).
        user_id: Owner of this editing session.
        resume_filename: Original uploaded filename.
        resume_blob_url: Optional blob URL of the original uploaded document.
        content: The current resume as a joined text (lines preserved).
        undo_stack: JSON list of :class:`ResumeEditAction` objects applied.
        redo_stack: JSON list of :class:`ResumeEditAction` objects undone.
        revision: Monotonic revision counter for the edit stack.
        created_at: Row creation timestamp.
        updated_at: Row last-update timestamp.
    """

    __tablename__ = "resume_edit_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    resume_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resume_blob_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    undo_stack: Mapped[list] = mapped_column(JSON, default=list)
    redo_stack: Mapped[list] = mapped_column(JSON, default=list)
    revision: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ResumeChatSessionModel(Base):
    """ORM model representing a resume review chat conversation.

    Attributes:
        id: Primary key (UUID string).
        user_id: Owner of this chat session.
        edit_session_id: Optional id of the associated edit session.
        screening_id: Optional id of the associated screening result.
        resume_text: Snapshot of the resume text at chat start.
        industry: Optional target industry context.
        jd_text: Optional job description text.
        history: JSON list of :class:`ChatMessage` objects.
        created_at: Row creation timestamp.
    """

    __tablename__ = "resume_chat_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    edit_session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    screening_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    resume_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True)
    jd_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    history: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class JobApplicationModel(Base):
    """ORM model representing a submitted job application.

    Attributes:
        id: Primary key (UUID string).
        user_id: Owner of the application.
        edit_session_id: Optional id of the edit session that produced the CV.
        screening_id: Optional id of the associated screening result.
        job_id: Optional external or stored job id being applied to.
        final_resume_text: The final (edited) resume text at submission time.
        cover_letter: Optional generated or user-entered cover letter.
        notes: Optional application notes.
        status: Submission status (``submitted``, ``queued``, ``failed``).
        created_at: Row creation timestamp.
    """

    __tablename__ = "job_applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    edit_session_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    screening_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    job_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    final_resume_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    cover_letter: Mapped[str] = mapped_column(Text, nullable=False, default="")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(16), default="submitted")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ExternalJobModel(Base):
    """ORM model representing a job posting collected from an external platform.

    Designed for future job scraper tools (LinkedIn, Indeed, etc.) that will
    collect listings into the database to allow direct application from the app.

    Attributes:
        id: Primary key (UUID string).
        platform: Source platform slug.
        external_id: Platform-specific job ID for deduplication.
        title: Job title.
        company: Company name.
        location: Job location.
        remote: Whether the role is remote.
        url: Original posting URL.
        description: Full job description text.
        salary_min: Minimum salary if listed.
        salary_max: Maximum salary if listed.
        currency: Salary currency code.
        skills: JSON list of extracted skills.
        posted_at: When the job was posted on the platform.
        scraped_at: When we collected the listing.
        applied: Whether the user has applied through our system.
        created_at: Row creation timestamp.
    """

    __tablename__ = "external_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    platform: Mapped[str] = mapped_column(String(20), default="linkedin")
    external_id: Mapped[str] = mapped_column(String(255), default="")
    title: Mapped[str] = mapped_column(String(255), default="")
    company: Mapped[str] = mapped_column(String(255), default="")
    location: Mapped[str] = mapped_column(String(255), default="")
    remote: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    url: Mapped[str] = mapped_column(String(1024), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    salary_min: Mapped[float | None] = mapped_column(Float, nullable=True)
    salary_max: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    skills: Mapped[list] = mapped_column(JSON, default=list)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scraped_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    applied: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
