"""Learning resource data models for skill gap remediation."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class SkillGap(BaseModel):
    """A single skill gap identified during screening.

    Attributes:
        skill: The required skill the candidate is missing.
        severity: How critical the gap is (high/medium/low).
        reason: Why this skill matters for the role.
    """

    skill: str
    severity: Literal["high", "medium", "low"] = "medium"
    reason: str = ""


class LearningResource(BaseModel):
    """A recommended resource for closing a specific skill gap.

    Attributes:
        id: Unique identifier (empty for new items).
        skill: The skill this resource covers.
        title: Resource title (course, article, etc.).
        url: Link to the resource.
        resource_type: Type of resource (course, article, video, book, practice).
        provider: Who provides the resource (Coursera, YouTube, etc.).
        description: Brief summary of what the resource covers.
        estimated_hours: Approximate time to complete.
        screening_id: The screening result that surfaced this gap.
    """

    id: str | None = None
    skill: str = ""
    title: str = ""
    url: str = ""
    resource_type: Literal["course", "article", "video", "book", "practice", "other"] = "other"
    provider: str = ""
    description: str = ""
    estimated_hours: float | None = None
    screening_id: str | None = None


class LearningPlan(BaseModel):
    """A curated learning plan for a candidate based on their skill gaps.

    Attributes:
        screening_id: The screening result this plan is based on.
        candidate_name: Name of the candidate.
        skill_gaps: List of identified skill gaps.
        resources: Recommended resources mapped to gaps.
        total_estimated_hours: Sum of all resource time estimates.
    """

    screening_id: str = ""
    candidate_name: str = ""
    skill_gaps: list[SkillGap] = Field(default_factory=list)
    resources: list[LearningResource] = Field(default_factory=list)
    total_estimated_hours: float = 0.0
