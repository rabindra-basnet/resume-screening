"""Service handling the interactive resume-review chat and application flow.

The chat agent produces replies and proposed edits. The service persists the
conversation, applies accepted edits to the linked editing session (undo/redo),
and coordinates the final application submission with the readiness agent.
"""

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.apply_readiness import ApplyReadinessAgent
from app.agents.llm_client import LLMClient
from app.agents.resume_chat import ResumeChatAgent
from app.config.settings import LLMProviderConfig
from app.database.repositories.job_application_repository import JobApplicationRepository
from app.database.repositories.resume_chat_session_repository import (
    ResumeChatSessionRepository,
)
from app.models.resume_chat import ChatReply
from app.models.resume_workspace import (
    ApplyDecision,
    ChatContext,
    ChatMessage,
    JobApplicationPayload,
    JobApplicationResult,
    ResumeEditAction,
    ResumeEditApplyResponse,
)

from .enrichment_service import EnrichmentService
from .resume_edit_service import ResumeEditService

logger = logging.getLogger(__name__)


def _derive_job_title(jd_text: str) -> str:
    """Derive a coarse job title from the first line of a job description.

    Args:
        jd_text: The raw job description text.

    Returns:
        The first non-empty line (truncated), or an empty string.
    """
    for line in (jd_text or "").splitlines():
        line = line.strip()
        if line:
            return line[:80]
    return ""


class ResumeChatService:
    """Coordinates multi-turn chat, edit application, and job submission.

    Args:
        session: An async SQLAlchemy session.
        chat_repo: Repository for chat sessions.
        edit_service: Editing service for apply/undo/redo.
        application_repo: Repository for job applications.
        provider_repo: Repository for AI provider (BYOK) configurations.
    """

    def __init__(
        self,
        session: AsyncSession,
        chat_repo: ResumeChatSessionRepository | None = None,
        edit_service: ResumeEditService | None = None,
        application_repo: JobApplicationRepository | None = None,
        provider_repo: object | None = None,
    ) -> None:
        """Initialize the chat service with its dependencies."""
        self.session = session
        self.chat_repo = chat_repo or ResumeChatSessionRepository(session)
        self.edit_service = edit_service or ResumeEditService(session)
        self.application_repo = application_repo or JobApplicationRepository(session)
        self._provider_repo = provider_repo

    @property
    def provider_repo(self):
        """Lazy provider repository to avoid circular imports."""
        if self._provider_repo is None:
            from app.database.repositories import ProviderRepository
            self._provider_repo = ProviderRepository(self.session)
        return self._provider_repo

    async def _build_agent(self, model_override: str | None = None) -> ResumeChatAgent:
        """Build a chat agent using the user's active provider if available.

        Args:
            model_override: Optional LLM model override.

        Returns:
            A :class:`ResumeChatAgent`.
        """
        active = await self.provider_repo.get_active()
        agent: ResumeChatAgent
        if active is not None and active.is_validated:
            try:
                from app.services.encryption import decrypt_api_key
                api_key = decrypt_api_key(active.api_key_encrypted)
            except Exception:  # noqa: BLE001
                logger.warning("Failed to decrypt API key for provider %s", active.id)
                api_key = None
            config = LLMProviderConfig(
                llm_provider=active.provider,
                llm_model=active.model,
                llm_api_key=api_key or "",
                llm_api_base=active.api_base,
                llm_max_tokens=active.max_tokens,
                llm_temperature=active.temperature,
            )
            agent = ResumeChatAgent(client=LLMClient(config=config))
        else:
            agent = ResumeChatAgent()
        return agent

    async def start_chat(
        self,
        *,
        user_id: str | None,
        context: ChatContext,
        edit_session_id: str | None = None,
        screening_id: str | None = None,
    ) -> dict:
        """Create a new chat session seeded with resume context.

        Args:
            user_id: Owning user.
            context: The resume + targeting context.
            edit_session_id: Optional linked editing session.
            screening_id: Optional linked screening.

        Returns:
            A dict with the chat session id and an initial greeting.
        """
        row = await self.chat_repo.create(
            user_id=user_id,
            resume_text=context.resume_text,
            industry=context.industry or None,
            jd_text=context.job_description or None,
            edit_session_id=edit_session_id,
            screening_id=screening_id,
        )
        initial = ChatMessage(
            role="assistant",
            content=(
                "I'm ready to help you improve your resume. "
                "Tell me what you'd like to focus on, or ask me to rewrite "
                "a specific section."
            ),
        )
        history = [initial.model_dump(mode="json")]
        await self.chat_repo.update_history(row.id, history)
        return {"chat_id": row.id, "history": history}

    async def send_message(
        self,
        *,
        chat_id: str,
        user_id: str | None,
        content: str,
        model_override: str | None = None,
    ) -> dict:
        """Send a message and get the agent's reply with proposed edits.

        Args:
            chat_id: The chat session id.
            user_id: Owning user.
            content: The user's message.
            model_override: Optional LLM model override.

        Returns:
            A dict with the assistant reply, proposed edits, and updated history.

        Raises:
            KeyError: If the chat session does not exist or is not owned by user.
        """
        row = await self.chat_repo.get(chat_id)
        if row is None or (row.user_id and user_id and row.user_id != user_id):
            raise KeyError(f"Chat session {chat_id} not found")

        history = [ChatMessage(**m) for m in (row.history or [])]
        history.append(ChatMessage(role="user", content=content))

        agent = await self._build_agent(model_override)
        kwargs: dict = {}
        if model_override:
            kwargs["model"] = model_override

        # Enrich with live job hints when a JD is present, to keep prompts lean
        # and grounded in real market expectations (serverless-safe best-effort).
        enrichment = EnrichmentService()
        job_hints: list[str] = []
        if row.jd_text:
            hints = await enrichment.job_hints(_derive_job_title(row.jd_text))
            if hints:
                job_hints = hints

        reply: ChatReply = agent.run(
            row.resume_text,
            history,
            industry=row.industry or "",
            job_description=row.jd_text or "",
            web_job_hints="\n".join(job_hints) if job_hints else "",
            **kwargs,
        )

        proposed_edits = [e.model_dump(mode="json") for e in reply.proposed_edits]
        history.append(ChatMessage(role="assistant", content=reply.reply))
        await self.chat_repo.update_history(
            chat_id, [m.model_dump(mode="json") for m in history]
        )

        return {
            "reply": reply.reply,
            "proposed_edits": proposed_edits,
            "edits_summary": reply.edits_summary,
            "needs_more_info": reply.needs_more_info,
            "history": [m.model_dump(mode="json") for m in history],
        }

    async def apply_edit(
        self,
        *,
        chat_id: str,
        user_id: str | None,
        edit_session_id: str,
        edit: ResumeEditAction,
    ) -> ResumeEditApplyResponse:
        """Apply a proposed edit to the linked editing session.

        Args:
            chat_id: The chat session id (for ownership checks).
            user_id: Owning user.
            edit_session_id: The editing session to mutate.
            edit: The edit action to apply.

        Returns:
            The edited document state.

        Raises:
            KeyError: If the session cannot be found.
        """
        row = await self.chat_repo.get(chat_id)
        if row is None or (row.user_id and user_id and row.user_id != user_id):
            raise KeyError(f"Chat session {chat_id} not found")
        return await self.edit_service.apply_edit(
            edit_session_id, edit, user_id=user_id
        )

    async def get_history(self, *, chat_id: str, user_id: str | None) -> list:
        """Return the message history of a chat session.

        Args:
            chat_id: The chat session id.
            user_id: Owning user.

        Returns:
            The message history.

        Raises:
            KeyError: If the chat session is not found or not owned.
        """
        row = await self.chat_repo.get(chat_id)
        if row is None or (row.user_id and user_id and row.user_id != user_id):
            raise KeyError(f"Chat session {chat_id} not found")
        return list(row.history or [])

    async def decide_application(
        self,
        *,
        edit_session_id: str,
        job_description: str = "",
        chat_summary: str = "",
        model_override: str | None = None,
    ) -> ApplyDecision:
        """Ask the readiness agent whether the resume is ready to apply.

        Args:
            edit_session_id: The editing session holding the final resume.
            job_description: Optional target job description.
            chat_summary: Optional summary of the iterative chat.
            model_override: Optional LLM model override.

        Returns:
            An :class:`ApplyDecision`.

        Raises:
            KeyError: If the edit session does not exist.
        """
        content = await self.edit_service.get_content(edit_session_id)
        if content is None:
            raise KeyError(f"Editing session {edit_session_id} not found")
        agent = ApplyReadinessAgent()
        kwargs: dict = {}
        if model_override:
            kwargs["model"] = model_override
        return agent.run(
            content,
            job_description=job_description,
            chat_summary=chat_summary,
            **kwargs,
        )

    async def submit_application(
        self,
        *,
        user_id: str,
        edit_session_id: str,
        payload: JobApplicationPayload,
    ) -> JobApplicationResult:
        """Persist a final job application.

        Args:
            user_id: Owning user.
            edit_session_id: The editing session with the final resume.
            payload: Application details.

        Returns:
            A :class:`JobApplicationResult`.

        Raises:
            KeyError: If the edit session does not exist.
        """
        content = await self.edit_service.get_content(edit_session_id)
        if content is None:
            raise KeyError(f"Editing session {edit_session_id} not found")
        final_payload = payload.model_copy(update={"resume_text": content})
        row = await self.application_repo.create(
            payload=final_payload, user_id=user_id, edit_session_id=edit_session_id
        )
        return JobApplicationResult(
            application_id=row.id,
            status="submitted",
            message="Application submitted successfully.",
        )
