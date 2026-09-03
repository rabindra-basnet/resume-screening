"""Service that builds a learning plan from a candidate's skill gaps.

Turns the missing/weak skills identified during screening into a prioritized
learning plan. For well-known skills it uses the curated resource library; for
unknown skills it optionally asks an LLM to propose resources via
:class:`LearningResourceAgent`.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import LearningResourceAgent
from app.database.repositories import LearningRepository
from app.models.learning import LearningPlan, LearningResource, SkillGap

from .resource_library import curated_resources_for_skill

logger = logging.getLogger(__name__)


class LearningService:
    """Build and persist learning plans from evaluation skill gaps.

    Args:
        session: An async SQLAlchemy session for persistence.
        repo: Repository for learning resources.
        resource_agent: Optional LLM agent for recommending resources for
            unknown skills.
    """

    def __init__(
        self,
        session: AsyncSession,
        repo: LearningRepository | None = None,
        resource_agent: LearningResourceAgent | None = None,
    ) -> None:
        """Initialize the learning service."""
        self.session = session
        self.repo = repo or LearningRepository(session)
        self.resource_agent = resource_agent

    async def build_plan(
        self,
        *,
        screening_id: str,
        candidate_name: str,
        missing_skills: list[str],
        weak_skills: list[str],
        model_override: str | None = None,
        llm_enabled: bool = True,
    ) -> LearningPlan:
        """Build a learning plan for the given skill gaps.

        Aggregates missing and weak skills into :class:`SkillGap` entries and
        recommends resources for each. Missing skills (no knowledge) are
        severity "high"; weak skills (partial knowledge) are "medium".

        Args:
            screening_id: The screening result id this plan is based on.
            candidate_name: Display name of the candidate.
            missing_skills: Skills the candidate does not possess.
            weak_skills: Skills the candidate knows only partially.
            model_override: Optional LLM model override.
            llm_enabled: Whether to allow LLM-generated resource suggestions.

        Returns:
            A populated :class:`LearningPlan`.
        """
        gaps: list[SkillGap] = []
        resources: list[LearningResource] = []

        seen: set[str] = set()
        for skill, severity, reason in [
            *(
                (s, "high", "Required skill not present in resume")
                for s in missing_skills
            ),
            *(
                (s, "medium", "Foundational knowledge only; needs strengthening")
                for s in weak_skills
            ),
        ]:
            key = skill.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            gaps.append(SkillGap(skill=skill, severity=severity, reason=reason))

            for matched in curated_resources_for_skill(skill):
                resource = matched.model_copy(update={"screening_id": screening_id})
                resources.append(resource)

            if not curated_resources_for_skill(skill) and llm_enabled:
                suggested = await self._suggest_from_llm(
                    skill, screening_id, model_override
                )
                resources.extend(suggested)

        await self.repo.create_many(resources)

        total_hours = sum(r.estimated_hours or 0.0 for r in resources)
        return LearningPlan(
            screening_id=screening_id,
            candidate_name=candidate_name,
            skill_gaps=gaps,
            resources=resources,
            total_estimated_hours=round(total_hours, 1),
        )

    async def _suggest_from_llm(
        self,
        skill: str,
        screening_id: str,
        model_override: str | None,
    ) -> list[LearningResource]:
        """Ask the LLM to recommend resources for an unknown skill.

        Args:
            skill: The skill to find resources for.
            screening_id: The screening result id.
            model_override: Optional LLM model override.

        Returns:
            A list of recommended :class:`LearningResource` objects. Returns an
            empty list on any failure so the plan still completes.
        """
        if self.resource_agent is None:
            return []
        kwargs: dict = {}
        if model_override:
            kwargs["model"] = model_override
        try:
            result = self.resource_agent.run(skill, **kwargs)
            suggested = list(result.resources)
        except Exception:  # noqa: BLE001 - never block plan generation
            logger.warning("LLM resource suggestion failed for skill %r", skill, exc_info=True)
            return []
        for resource in suggested:
            resource.screening_id = screening_id
        return suggested
