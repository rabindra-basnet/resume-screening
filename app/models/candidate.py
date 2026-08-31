"""Candidate-related data models representing an extracted resume profile."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Education(BaseModel):
    """A single education entry extracted from a resume.

    Attributes:
        degree: The degree or qualification obtained.
        institution: The school or university attended.
        field_of_study: The subject area or major.
    """

    degree: str | None = None
    institution: str | None = None
    field_of_study: str | None = None


class WorkExperience(BaseModel):
    """A single work experience entry extracted from a resume.

    Attributes:
        company: The employer name.
        title: The job title held.
        years: Total years in this role.
    """

    company: str | None = None
    title: str | None = None
    years: float | None = None


class CandidateProfile(BaseModel):
    """Structured profile of a candidate parsed from raw resume text.

    Attributes:
        name: The candidate's full name.
        email: The candidate's email address.
        phone: The candidate's phone number.
        education: List of education entries.
        work_experience_years: Total years of professional experience.
        skills: List of skills mentioned in the resume.
        certifications: List of professional certifications.
        work_history: Optional list of individual work experience entries.
        raw_summary: Optional free-text summary of the resume.
    """

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    education: list[Education] = Field(default_factory=list)
    work_experience_years: float | None = None
    skills: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    work_history: list[WorkExperience] = Field(default_factory=list)
    raw_summary: str | None = None
