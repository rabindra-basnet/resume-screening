"""Data models for the interactive resume editing and job application chat."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ── Chat / Iterative Review ──────────────────────────────────────────────


class ChatMessage(BaseModel):
    """A single message in the resume-review chat.

    Attributes:
        id: Optional message id (set when persisted).
        role: ``user``, ``assistant``, or ``system``.
        content: Message body text.
        created_at: Optional timestamp.
    """

    id: str | None = None
    role: Literal["user", "assistant", "system"] = "user"
    content: str = ""
    created_at: datetime | None = None


class ResumeChatCreate(BaseModel):
    """Payload to create a new resume review chat session.

    Attributes:
        resume_text: The current full resume text.
        resume_id: Optional id of the source resume/review.
    """

    resume_text: str
    resume_id: str | None = None


class ResumeChatRequest(BaseModel):
    """Payload to send a message in an existing chat session.

    Attributes:
        content: The user's message.
    """

    content: str


class ChatContext(BaseModel):
    """Seed context given to the chat agent on the first turn.

    Attributes:
        resume_text: The resume to review.
        industry: Optional target industry.
        job_description: Optional job description being applied for.
        company_names: Optional target companies.
    """

    resume_text: str
    industry: str = ""
    job_description: str = ""
    company_names: list[str] = Field(default_factory=list)


# ── Editing (undo/redo) ─────────────────────────────────────────────────


class EditDelta(BaseModel):
    """A single line-delta edit to the resume text.

    Attributes:
        original_line: The line of text being replaced (or empty to insert).
        new_line: The replacement line (or empty to delete).
        section: Optional section label (e.g. ``summary``, ``experience``).
    """

    original_line: str = ""
    new_line: str = ""
    section: str = ""


class ResumeEditAction(BaseModel):
    """A single cumulative edit operation in an editing session.

    Attributes:
        action_type: ``insert``, ``replace``, or ``delete``.
        start_line: 0-based line index where the edit begins.
        end_line: 0-based line index where the edit ends (exclusive for replace).
        text: The replacement text (for insert/replace).
        previous_text: Optional prior content for deterministic undo/redo.
        timestamp: When the edit was recorded.
    """

    action_type: Literal["insert", "replace", "delete"]
    start_line: int = 0
    end_line: int = 0
    text: str = ""
    previous_text: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ResumeEditingState(BaseModel):
    """Complete editing state supporting undo/redo.

    Attributes:
        document_id: Unique id for the edit session.
        content: Current full resume text.
        undo_stack: Stack of applied edits (for undo).
        redo_stack: Stack of undone edits (for redo).
        saved_revision: Revision index of the last persisted content.
    """

    document_id: str = ""
    content: str = ""
    undo_stack: list[ResumeEditAction] = Field(default_factory=list)
    redo_stack: list[ResumeEditAction] = Field(default_factory=list)
    saved_revision: int = 0


class ResumeEditApplyRequest(BaseModel):
    """Payload for applying an edit to a resume document.

    Attributes:
        document_id: The editing session id.
        action: The edit action to apply.
    """

    document_id: str
    action: ResumeEditAction


class ResumeEditApplyResponse(BaseModel):
    """Response after applying an edit.

    Attributes:
        document_id: The editing session id.
        content: Updated resume content.
        undo_available: Whether an undo is possible.
        redo_available: Whether a redo is possible.
        revision: The current revision number.
    """

    document_id: str
    content: str
    undo_available: bool = False
    redo_available: bool = False
    revision: int = 0


class ResumeEditUndoResponse(BaseModel):
    """Response after an undo/redo operation.

    Attributes:
        document_id: The editing session id.
        content: Updated resume content.
        undo_available: Whether an undo is possible.
        redo_available: Whether a redo is possible.
        revision: The current revision number.
    """

    document_id: str
    content: str
    undo_available: bool = False
    redo_available: bool = False
    revision: int = 0


# ── Job Application ─────────────────────────────────────────────────────


class JobApplicationPayload(BaseModel):
    """Payload to apply for a job after chat review.

    Attributes:
        edit_session_id: Id of the editing session holding the final resume.
        screening_id: Id of the screening event this application relates to.
        job_id: The external or stored job id.
        resume_text: The final (edited) resume text.
        cover_letter: Optional generated cover letter.
        notes: Optional application notes.
    """

    edit_session_id: str | None = None
    screening_id: str | None = None
    job_id: str | None = None
    resume_text: str = ""
    cover_letter: str = ""
    notes: str = ""


class JobApplicationResult(BaseModel):
    """Response after submitting a job application.

    Attributes:
        application_id: Unique application id.
        status: Submission status.
        message: Human-readable confirmation.
        submitted_at: When the application was submitted.
    """

    application_id: str = ""
    status: Literal["submitted", "queued", "failed"] = "submitted"
    message: str = ""
    submitted_at: datetime = Field(default_factory=datetime.utcnow)


class ApplyDecision(BaseModel):
    """Decision output of the apply-agent after chat.

    Attributes:
        ready: Whether the resume is ready to apply.
        application_status: ``ready``, ``needs_review``, or ``not_ready``.
        summary: Explanation of the decision.
    """

    ready: bool = False
    application_status: Literal["ready", "needs_review", "not_ready"] = "not_ready"
    summary: str = ""
