"""Evaluation result data models."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SkillMatch(BaseModel):
    """A single skill match between a candidate and a job description.

    Attributes:
        skill: The skill name that was compared.
        matched: Whether the candidate possesses the skill.
    """

    skill: str
    matched: bool


CandidateStatus = Literal["selected", "rejected", "pending"]


class EvaluationResult(BaseModel):
    """Result of evaluating a candidate against a job description.

    Attributes:
        candidate_status: Final disposition (``selected``, ``rejected``,
            ``pending``).
        reason: Human-readable explanation of the decision.
        matched_skills: List of skills the candidate matched from the JD.
        missing_skills: List of required JD skills the candidate lacks.
        skill_match_percentage: Percentage of required skills matched.
        experience_years: Candidate's evaluated experience in years.
    """

    candidate_status: CandidateStatus = "pending"
    reason: str = ""
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    skill_match_percentage: float = 0.0
    experience_years: float | None = None
