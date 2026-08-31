"""Skill matching and scoring helpers.

Provides deterministic functions for comparing a candidate's skills against a
job description's required skills. Matching is case-insensitive and performs
both exact and fuzzy token-level matching to catch near-synonyms.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher

FUZZY_THRESHOLD: float = 0.85


def _normalize(skill: str) -> str:
    """Lowercase a skill and collapse internal whitespace.

    Args:
        skill: Raw skill string to normalize.

    Returns:
        A normalized lowercase string with trimmed whitespace.
    """
    return re.sub(r"\s+", " ", skill.strip().lower())


def _fuzzy_match(a: str, b: str) -> bool:
    """Return whether two strings match exactly or within a fuzzy threshold.

    Args:
        a: First normalized string.
        b: Second normalized string.

    Returns:
        ``True`` if the strings are equal or sufficiently similar.
    """
    return a == b or SequenceMatcher(None, a, b).ratio() >= FUZZY_THRESHOLD


def match_skills(candidate_skills: list[str], required_skills: list[str]) -> list[str]:
    """Determine which required skills are satisfied by the candidate.

    Each required skill is considered matched if it fuzzy-matches any candidate
    skill (either the exact token or any comma-separated part of it).

    Args:
        candidate_skills: Skills found in the candidate's profile.
        required_skills: Skills required by the job description.

    Returns:
        A list of required skills that the candidate matches.
    """
    normalized_candidate = [_normalize(s) for s in candidate_skills if s]
    matched: list[str] = []

    for required in required_skills:
        normalized_required = _normalize(required)
        parts = [p for p in re.split(r"[/,]| and ", normalized_required) if p]
        hit = False
        for cand in normalized_candidate:
            if any(_fuzzy_match(cand, part) for part in parts) or _fuzzy_match(
                cand, normalized_required
            ):
                hit = True
                break
        if hit:
            matched.append(required)

    return matched


def calculate_skill_match(
    candidate_skills: list[str], required_skills: list[str]
) -> tuple[list[str], list[str], float]:
    """Compute matched, missing skills and the overall match percentage.

    Args:
        candidate_skills: Skills found in the candidate's profile.
        required_skills: Skills required by the job description.

    Returns:
        A tuple of ``(matched_skills, missing_skills, match_percentage)``.
        The percentage is ``0.0`` when no required skills are provided to
        avoid a division by zero.
    """
    if not required_skills:
        return [], list(required_skills), 0.0

    matched_skills = match_skills(candidate_skills, required_skills)
    missing_skills = [s for s in required_skills if s not in matched_skills]
    percentage = round(len(matched_skills) / len(required_skills) * 100, 2)
    return matched_skills, missing_skills, percentage
