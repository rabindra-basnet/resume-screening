"""Unit tests for the learning service and resource library."""

from __future__ import annotations

import pytest

from app.services.learning_service import LearningService
from app.services.resource_library import curated_resources_for_skill, has_curated_resources


def test_has_curated_resources_for_known_skill() -> None:
    """Known skills return curated resources."""
    assert has_curated_resources("Python")


def test_curated_resources_for_known_skill() -> None:
    """Curated resources carry the expected metadata for a known skill."""
    resources = curated_resources_for_skill("Python")
    assert resources
    assert all(r.skill == "Python" for r in resources)
    assert all(r.url for r in resources)
    assert all(r.title for r in resources)


def test_curated_resources_unknown_skill_empty() -> None:
    """Unknown skills return no curated resources."""
    assert curated_resources_for_skill("extreme-quantum-flux-weaving") == []


async def test_build_plan_groups_gaps_and_persists_resources(db) -> None:
    """A learning plan aggregates gaps and attaches curated resources."""
    session = db.session()
    service = LearningService(session, resource_agent=None)
    plan = await service.build_plan(
        screening_id="abc-123",
        candidate_name="Jane Doe",
        missing_skills=["Python", "Kubernetes", "UnknownSkillXYZ"],
        weak_skills=["Docker"],
    )
    # Missing skill -> severity high; weak skill -> severity medium.
    severities = {g.skill: g.severity for g in plan.skill_gaps}
    assert severities["Python"] == "high"
    assert severities["Docker"] == "medium"

    # Curated resources attached for known skills (Python, Kubernetes, Docker).
    curated_skills = {r.skill for r in plan.resources}
    assert "Python" in curated_skills
    assert "Kubernetes" in curated_skills
    assert "Docker" in curated_skills

    # All persisted resources reference the screening id.
    assert all(r.screening_id == "abc-123" for r in plan.resources)

    # LLM disabled => unknown skills contribute no resources, but plan completes.
    assert isinstance(plan.total_estimated_hours, float)

    await session.close()
