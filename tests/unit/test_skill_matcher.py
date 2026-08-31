"""Unit tests for the skill-matching helpers."""

from __future__ import annotations

from app.tools.skill_matcher import calculate_skill_match, match_skills


def test_match_skills_exact() -> None:
    """Exact skill matches are detected regardless of case."""
    matched = match_skills(["Python", "SQL"], ["python", "sql"])
    assert len(matched) == 2


def test_match_partial_overlap() -> None:
    """Only the overlapping skills are returned as matched."""
    matched = match_skills(["Python", "Java"], ["Python", "Go"])
    assert matched == ["Python"]


def test_calculate_percentage() -> None:
    """Percentage is computed from matched-over-required ratio."""
    matched, missing, pct = calculate_skill_match(["Python", "SQL", "Docker"], ["Python", "SQL"])
    assert len(matched) == 2
    assert missing == []
    assert pct == 100.0


def test_calculate_percentage_no_required() -> None:
    """No required skills yields zero percent without division error."""
    matched, missing, pct = calculate_skill_match(["Python"], [])
    assert matched == []
    assert missing == []
    assert pct == 0.0


def test_calculate_missing_skills() -> None:
    """Skills not possessed are returned in the missing list."""
    matched, missing, pct = calculate_skill_match(["Python"], ["Python", "Kubernetes"])
    assert matched == ["Python"]
    assert missing == ["Kubernetes"]
    assert pct == 50.0
