"""External job posting models for future scraper integration."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ExternalJobPosting(BaseModel):
    """A job posting sourced from an external platform (LinkedIn, Indeed, etc.).

    Designed for future job scraper tools that will collect listings from
    external platforms and store them for direct application flow.

    Attributes:
        id: Unique identifier (empty for new items).
        platform: Source platform (linkedin, indeed, glassdoor, etc.).
        external_id: Platform-specific job ID for deduplication.
        title: Job title.
        company: Company name.
        location: Job location (city, state, country).
        remote: Remote work policy.
        url: Direct link to the original posting.
        description: Full job description text.
        salary_min: Minimum salary if listed.
        salary_max: Maximum salary if listed.
        currency: Salary currency code.
        skills: Extracted required skills.
        posted_at: When the job was posted on the platform.
        scraped_at: When we collected this listing.
        applied: Whether the user has applied through our system.
    """

    id: str | None = None
    platform: Literal["linkedin", "indeed", "glassdoor", "other"] = "linkedin"
    external_id: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    remote: bool | None = None
    url: str = ""
    description: str = ""
    salary_min: float | None = None
    salary_max: float | None = None
    currency: str = "USD"
    skills: list[str] = Field(default_factory=list)
    posted_at: datetime | None = None
    scraped_at: datetime | None = None
    applied: bool = False
