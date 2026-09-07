"""Unit tests for the resume review agents and the edit/undo service."""

from __future__ import annotations

import pytest
from app.agents.resume_review import (
    ATSOptimizerAgent,
    BrutalReviewAgent,
    BulletPointTransformerAgent,
    FinalPolishAgent,
    IndustryToneMatchAgent,
)
from app.models.resume_review import ATSOptimizationResult, BrutalReviewResult
from app.models.resume_workspace import ResumeEditAction
from app.services.resume_edit_service import EditConflictError, ResumeEditService


class _FakeClient:
    """A minimal fake LLM client returning canned responses."""

    def __init__(self, response: str) -> None:
        """Store the canned response."""
        self.response = response

    def complete(self, system_prompt: str, user_prompt: str, **kwargs: str) -> str:
        """Return the canned response, ignoring the prompts."""
        return self.response


def test_brutal_review_parses_model(sample_candidate) -> None:
    """Brutal review parses the LLM response into the result model."""
    response = (
        '{"overall_assessment": "Has potential but lacks results", '
        '"weak_areas": ["No metrics"], "missing_elements": ["Certifications"], '
        '"immediate_rejections": ["Typos"], "strengths": ["Clear skills list"], '
        '"actionable_fixes": ["Add numbers"]}'
    )
    agent = BrutalReviewAgent(client=_FakeClient(response))
    result = agent.run(candidate=sample_candidate)
    assert isinstance(result, BrutalReviewResult)
    assert "metrics" in result.weak_areas[0].lower()
    assert result.actionable_fixes == ["Add numbers"]


def test_ats_optimizer_parses_model(sample_candidate) -> None:
    """ATS optimizer parses the LLM response into the result model."""
    response = (
        '{"missing_keywords": ["gRPC"], "skills_to_highlight": ["PostgreSQL"], '
        '"bullet_restructurings": [{"original": "x", "suggested": "y", "reason": "z"}], '
        '"ats_score_estimate": 64, "summary": "Needs keyword work"}'
    )
    agent = ATSOptimizerAgent(client=_FakeClient(response))
    result = agent.run(candidate=sample_candidate, job_description="Needs gRPC")
    assert isinstance(result, ATSOptimizationResult)
    assert result.missing_keywords == ["gRPC"]
    assert result.ats_score_estimate == 64.0
    assert len(result.bullet_restructurings) == 1


def test_bullet_transformer_parses_model() -> None:
    """Bullet transformer parses nested transform objects."""
    response = (
        '{"original_bullets": ["Did stuff"], '
        '"transformed_bullets": [{"original": "Did stuff", "transformed": "Boosted X by 40%", '
        '"action_verb": "Boosted", "task": "X", "result": "40% uplift"}], '
        '"questions_for_user": ["How many users?"]}'
    )
    agent = BulletPointTransformerAgent(client=_FakeClient(response))
    result = agent.run("Did stuff\nDid more")
    assert result.original_bullets == ["Did stuff"]
    assert result.transformed_bullets[0].action_verb == "Boosted"
    assert result.questions_for_user == ["How many users?"]


def test_industry_tone_parses_model(sample_candidate) -> None:
    """Industry tone agent parses the response into its model."""
    response = (
        '{"original_summary": "Hardworking engineer", '
        '"rewritten_summary": "Scalable systems engineer", '
        '"original_skills": ["Python"], '
        '"rewritten_skills": ["Python, distributed systems"], '
        '"tone_analysis": "More specific", "industry_alignment_score": 88}'
    )
    agent = IndustryToneMatchAgent(client=_FakeClient(response))
    result = agent.run(candidate=sample_candidate, industry="fintech")
    assert result.rewritten_summary == "Scalable systems engineer"
    assert result.industry_alignment_score == 88.0


def test_final_polish_parses_model(sample_candidate) -> None:
    """Final polish agent parses the response into its model."""
    response = (
        '{"tense_issues": [{"section": "Exp", "original": "manage", "fixed": "managed"}], '
        '"cliche_replacements": [{"original": "team player", '
        '"replacement": "cross-functional lead", "reason": "specific"}], '
        '"generic_to_specific": [], '
        '"overall_quality_score": 75, "final_summary": "Good"}'
    )
    agent = FinalPolishAgent(client=_FakeClient(response))
    result = agent.run(candidate=sample_candidate)
    assert result.cliche_replacements[0].original == "team player"
    assert result.overall_quality_score == 75.0


@pytest.mark.anyio
async def test_edit_service_apply_undo_redo(db) -> None:
    """Edit service applies a replace, then undo, then redo correctly."""
    session = db.session_factory()
    try:
        document_id = await ResumeEditService(session).create_session(
            resume_text="line0\nline1\nline2", user_id=None
        )
        service = ResumeEditService(session)

        applied = await service.apply_edit(
            document_id,
            ResumeEditAction(
                action_type="replace",
                start_line=1,
                end_line=2,
                text="NEW LINE",
                previous_text="line1",
            ),
        )
        assert applied.content == "line0\nNEW LINE\nline2"
        assert applied.undo_available is True
        assert applied.redo_available is False

        undone = await service.undo(document_id)
        assert undone.content == "line0\nline1\nline2"
        assert undone.undo_available is False
        assert undone.redo_available is True

        redone = await service.redo(document_id)
        assert redone.content == "line0\nNEW LINE\nline2"
        assert redone.undo_available is True
        assert redone.redo_available is False
    finally:
        await session.close()


@pytest.mark.anyio
async def test_edit_service_text_anchor_survives_drift(db) -> None:
    """A text-anchored edit resolves correctly even after a prior insert shifts
    line indices (the core drift-fix scenario)."""
    session = db.session_factory()
    try:
        document_id = await ResumeEditService(session).create_session(
            resume_text="summary\nrole A\nrole B", user_id=None
        )
        service = ResumeEditService(session)

        # Client snapshot shows role A at index 1. Before applying, an insert
        # at the top shifts role A to index 2. Index-based apply would corrupt
        # role B; text-anchored apply must still target role A.
        await service.apply_edit(
            document_id,
            ResumeEditAction(
                action_type="insert",
                start_line=0,
                end_line=0,
                text="NEW HEADER",
            ),
        )

        revised = await service.apply_edit(
            document_id,
            ResumeEditAction(
                action_type="replace",
                start_line=1,  # stale - role A is now at index 2
                end_line=2,
                text="REWRITTEN ROLE A",
                previous_text="role A",  # authoritative anchor
            ),
        )
        assert revised.content == "NEW HEADER\nsummary\nREWRITTEN ROLE A\nrole B"

        # Undo must reverse the replace back to the correct line.
        undone = await service.undo(document_id)
        assert undone.content == "NEW HEADER\nsummary\nrole A\nrole B"
    finally:
        await session.close()


@pytest.mark.anyio
async def test_edit_service_raises_conflict_when_anchor_missing(db) -> None:
    """Applying an edit whose anchor is absent from the current content raises
    a conflict error instead of silently editing the wrong text."""
    session = db.session_factory()
    try:
        document_id = await ResumeEditService(session).create_session(
            resume_text="alpha\nbeta\ngamma", user_id=None
        )
        service = ResumeEditService(session)

        with pytest.raises(EditConflictError):
            await service.apply_edit(
                document_id,
                ResumeEditAction(
                    action_type="replace",
                    start_line=1,
                    end_line=2,
                    text="REPLACED",
                    previous_text="delta-departed",  # not in current content
                ),
            )
    finally:
        await session.close()


@pytest.mark.anyio
async def test_edit_service_apply_anchor_present_succeeds(db) -> None:
    """An edit whose anchor is present in the current content applies at the
    anchored location regardless of the stale line index."""
    session = db.session_factory()
    try:
        document_id = await ResumeEditService(session).create_session(
            resume_text="alpha\nbeta\ngamma", user_id=None
        )
        service = ResumeEditService(session)

        applied = await service.apply_edit(
            document_id,
            ResumeEditAction(
                action_type="replace",
                start_line=0,
                end_line=1,
                text="BETA!",
                previous_text="beta",
            ),
        )
        assert applied.content == "alpha\nBETA!\ngamma"
    finally:
        await session.close()


@pytest.mark.anyio
async def test_edit_service_apply_rejects_stale_index_without_anchor(db) -> None:
    """When no anchor is supplied and the provided index is stale (points past
    the real content), the edit still applies at the clamped index."""
    session = db.session_factory()
    try:
        document_id = await ResumeEditService(session).create_session(
            resume_text="one\ntwo", user_id=None
        )
        service = ResumeEditService(session)

        applied = await service.apply_edit(
            document_id,
            ResumeEditAction(
                action_type="replace", start_line=1, end_line=2, text="two!"
            ),
        )
        assert applied.content == "one\ntwo!"
    finally:
        await session.close()
