"""Data models for the interactive resume-review chat agent output."""

from __future__ import annotations

from pydantic import BaseModel, Field

from .resume_workspace import ResumeEditAction


class ChatProposedEdit(BaseModel):
    """A single edit the chat agent proposes for the resume document.

    Attributes:
        action_type: ``insert``, ``replace``, or ``delete``.
        start_line: 0-based line index where the edit starts.
        end_line: 0-based line index where the edit ends (exclusive).
        text: Replacement text (for insert/replace).
    """

    action_type: str = "replace"
    start_line: int = 0
    end_line: int = 0
    text: str = ""


class ChatReply(BaseModel):
    """Structured output of the chat agent for a single turn.

    Attributes:
        reply: The conversational response to the user.
        proposed_edits: Zero-or-more concrete document edits to suggest.
        edits_summary: Brief note about what the edits change.
        needs_more_info: Questions answered by the user before proceeding.
    """

    reply: str = ""
    proposed_edits: list[ChatProposedEdit] = Field(default_factory=list)
    edits_summary: str = ""
    needs_more_info: str = ""


class ChatTurn(BaseModel):
    """The async result of processing one user message.

    Attributes:
        reply: The agent's conversational response.
        proposed_edits: Edits the agent suggests applying.
        edits_summary: Description of the proposed edits.
        needs_more_info: Clarifying questions for the user.
    """

    reply: str = ""
    proposed_edits: list[ChatProposedEdit] = Field(default_factory=list)
    edits_summary: str = ""
    needs_more_info: str = ""


def to_edit_action(edit: ChatProposedEdit) -> ResumeEditAction:
    """Convert a chat proposal into a persistent edit action.

    Args:
        edit: The chat-proposed edit.

    Returns:
        The equivalent :class:`ResumeEditAction`.
    """
    return ResumeEditAction(
        action_type=edit.action_type,  # type: ignore[arg-type]
        start_line=edit.start_line,
        end_line=edit.end_line,
        text=edit.text,
    )
