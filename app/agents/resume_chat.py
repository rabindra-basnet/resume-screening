"""Agent that runs an interactive, multi-turn resume-review chat.

Maintains a full-resolution snapshot of the resume (line-numbered) as context
and returns both a conversational reply and any concrete document edits the
user should consider applying.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

from app.models.resume_chat import ChatProposedEdit, ChatReply
from app.models.resume_workspace import ChatMessage
from app.prompts.resume_chat import RESUME_CHAT, build_lined_resume

from .base import BaseAgent, StructuredOutputError

logger = logging.getLogger(__name__)


class ResumeChatAgent(BaseAgent[ChatReply]):
    """Multi-turn conversational resume review and editing agent.

    Holds the current resume text and message history as context and produces
    structured replies plus proposed line-based edits.
    """

    response_model = ChatReply

    def run(
        self,
        resume_text: str,
        history: list[ChatMessage],
        *,
        industry: str = "",
        job_description: str = "",
        company_names: list[str] | None = None,
        web_job_hints: str = "",
        **kwargs: Any,
    ) -> ChatReply:
        """Process a single chat turn.

        Args:
            resume_text: Current full resume text (line-based).
            history: Prior conversation messages (system, user, assistant).
            industry: Optional target industry context.
            job_description: Optional job description being targeted.
            company_names: Optional target companies.
            web_job_hints: Optional live web snippets about the target role.
            **kwargs: Optional completion overrides.

        Returns:
            A validated :class:`ChatReply`.
        """
        context_block = self._build_context_block(
            industry=industry,
            job_description=job_description,
            company_names=company_names,
            web_job_hints=web_job_hints,
        )
        lined = build_lined_resume(resume_text)
        history_block = self._format_history(history)

        system_prompt = (
            f"{RESUME_CHAT}\n\n"
            f"--- Chat history ---\n{history_block}"
        )
        user_prompt = (
            f"{context_block}\n\n"
            f"{lined}\n\n"
            f"User's latest message: {self._last_user_message(history)}"
        )
        raw = self.client.complete(system_prompt, user_prompt, **kwargs)
        return self._parse_chat_reply(raw)

    def _parse_chat_reply(self, raw: str) -> ChatReply:
        """Parse the raw LLM response into a :class:`ChatReply`.

        Args:
            raw: The raw JSON string from the LLM.

        Returns:
            A validated :class:`ChatReply`.

        Raises:
            StructuredOutputError: If the content is not valid JSON or fails
                validation, matching the behaviour of other agents.
        """
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise StructuredOutputError(
                f"Chat agent returned invalid JSON: {raw[:200]!r}"
            ) from exc
        try:
            proposed = [ChatProposedEdit(**e) for e in data.get("proposed_edits", [])]
        except (TypeError, ValidationError) as exc:
            raise StructuredOutputError(f"Chat agent returned invalid edits: {exc}") from exc
        return ChatReply(
            reply=data.get("reply", ""),
            proposed_edits=proposed,
            edits_summary=data.get("edits_summary", ""),
            needs_more_info=data.get("needs_more_info", ""),
        )

    @staticmethod
    def _format_history(history: list[ChatMessage]) -> str:
        """Format the chat history for inclusion in the prompt.

        Args:
            history: Prior messages.

        Returns:
            A compact string representation of the conversation.
        """
        lines = []
        for msg in history[-20:]:  # keep a bounded window
            role = msg.role
            content = msg.content.replace("\n", " ")[:500]
            lines.append(f"{role}: {content}")
        return "\n".join(lines) if lines else "(no prior messages)"

    @staticmethod
    def _last_user_message(history: list[ChatMessage]) -> str:
        """Return the most recent user message.

        Args:
            history: The message history.

        Returns:
            The last user message text, or empty string.
        """
        for msg in reversed(history):
            if msg.role == "user":
                return msg.content
        return ""

    @staticmethod
    def _build_context_block(
        *,
        industry: str,
        job_description: str,
        company_names: list[str] | None,
        web_job_hints: str = "",
    ) -> str:
        """Build the context block describing the user's goals.

        Args:
            industry: Target industry.
            job_description: Target job description.
            company_names: Target companies.
            web_job_hints: Optional live web snippets about the target role.

        Returns:
            A formatted context block string.
        """
        parts = []
        if industry:
            parts.append(f"Target industry: {industry}")
        if job_description:
            parts.append(f"Target job description:\n{job_description}")
        if company_names:
            parts.append(f"Target companies: {', '.join(company_names)}")
        if web_job_hints:
            parts.append(f"Live market context about the role:\n{web_job_hints}")
        if not parts:
            parts.append(
                "No special targeting provided — give general resume improvement advice."
            )
        return "\n".join(parts)
