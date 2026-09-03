"""Agent that recommends learning resources for a skill gap."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.models.learning import LearningResource
from app.prompts import LEARNING_RESOURCES

from .base import BaseAgent


class LearningResourcesResponse(BaseModel):
    """LLM response wrapper containing a list of recommended resources.

    Attributes:
        resources: The recommended learning resources.
    """

    resources: list[LearningResource] = Field(default_factory=list)


class LearningResourceAgent(BaseAgent[LearningResourcesResponse]):
    """Recommend learning resources for a given skill gap.

    Asks the LLM to curate high-quality resources a candidate can use to
    become proficient in a skill they are missing or weak in.
    """

    response_model = LearningResourcesResponse

    def run(self, skill: str, **kwargs: str) -> LearningResourcesResponse:
        """Recommend resources for the given skill.

        Args:
            skill: The skill the candidate needs to learn or strengthen.
            **kwargs: Optional completion overrides (e.g. model, temperature).

        Returns:
            A :class:`LearningResourcesResponse` wrapping the recommended
            :class:`LearningResource` objects.
        """
        user_prompt = LEARNING_RESOURCES.format(skill=skill)
        return self._complete_and_parse(user_prompt, **kwargs)
