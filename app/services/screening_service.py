"""Application service orchestrating the end-to-end screening workflow.

Coordinates PDF parsing, job-description resolution/caching, agent execution,
and persistence of results. This is the primary business-logic entry point used
by the API layer.
"""

from __future__ import annotations

import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AgentOrchestrator, LearningResourceAgent
from app.agents.llm_client import LLMClient
from app.config.settings import LLMProviderConfig, get_settings
from app.database.repositories.jd_repository import JDRepository
from app.database.repositories.resume_repository import ResumeRepository
from app.models.job_description import JobDescription
from app.tools import DocumentParser

from .learning_service import LearningService

logger = logging.getLogger(__name__)


class ScreeningService:
    """High-level screening workflow orchestrator.

    When the user has configured an active AI provider (BYOK), its credentials
    are used for all LLM calls. Otherwise the system-level default provider is
    used.

    Args:
        session: An async SQLAlchemy session for persistence.
        orchestrator: The agent pipeline. Defaults to a new orchestrator.
        jd_repo: Repository for job-description persistence/caching.
        resume_repo: Repository for screening-result persistence.
        provider_repo: Repository for AI provider (BYOK) configurations.
        document_parser: Document text extraction utility (PDF/DOCX).
        learning_service: Service that builds learning plans from skill gaps.
    """

    def __init__(
        self,
        session: AsyncSession,
        orchestrator: AgentOrchestrator | None = None,
        jd_repo: JDRepository | None = None,
        resume_repo: ResumeRepository | None = None,
        provider_repo: object | None = None,
        document_parser: DocumentParser | None = None,
        learning_service: LearningService | None = None,
    ) -> None:
        """Initialize the screening service with its dependencies."""
        self.session = session
        self.orchestrator = orchestrator or AgentOrchestrator()
        self.jd_repo = jd_repo or JDRepository(session)
        self.resume_repo = resume_repo or ResumeRepository(session)
        self._provider_repo = provider_repo
        self.document_parser = document_parser or DocumentParser()
        self.learning_service = learning_service or LearningService(
            session, resource_agent=LearningResourceAgent()
        )

    @property
    def provider_repo(self):
        """Lazy provider repository to avoid circular imports."""
        if self._provider_repo is None:
            from app.database.repositories.provider_repository import ProviderRepository
            self._provider_repo = ProviderRepository(self.session)
        return self._provider_repo

    async def run_screening(
        self,
        resume_bytes: bytes,
        *,
        resume_filename: str = "resume.pdf",
        job_description: str | None = None,
        jd_id: str | None = None,
        model_override: str | None = None,
    ) -> dict:
        """Run a full screening for a resume against a job description.

        Args:
            resume_bytes: The raw resume document bytes (PDF or DOCX).
            resume_filename: Original filename of the uploaded resume (used to
                determine the document format).
            job_description: Optional inline job-description raw text. When
                omitted, the JD is loaded from storage via ``jd_id``.
            jd_id: Optional id of a stored job description to load.
            model_override: Optional LLM model override for the pipeline.

        Returns:
            A serializable dict containing the candidate, job, evaluation,
            screening id, model used, and processing time.

        Raises:
            DocumentParsingError: If the resume document cannot be parsed.
            RuntimeError: If no job description can be resolved.
        """
        started = time.monotonic()

        referenced_jd_id = jd_id
        resume_text = self.document_parser.extract_text(resume_bytes, resume_filename)

        # Resolve the orchestrator — uses user's BYOK provider if configured.
        orchestrator = await self._build_orchestrator_for_request()

        if job_description is not None:
            # Extract structured JD from inline text and persist for reuse.
            job = await self._build_job(orchestrator, resume_text, job_description, model_override)
            persisted = await self.jd_repo.upsert(job)
            referenced_jd_id = persisted.id
        elif jd_id:
            model = await self.jd_repo.get(jd_id)
            if model is None:
                raise RuntimeError(f"Job description {jd_id} not found")
            job = JDRepository._from_model(model)
        else:
            raise RuntimeError("A persisted jd_id or job description text is required")

        candidate, parsed_job, evaluation = orchestrator.screen(resume_text, job.raw_text)

        elapsed_ms = int((time.monotonic() - started) * 1000)
        row = await self.resume_repo.create(
            resume_filename=resume_filename,
            resume_text=resume_text,
            candidate=candidate,
            evaluation=evaluation,
            status=evaluation.candidate_status,
            skill_match_percentage=evaluation.skill_match_percentage,
            llm_model_used=self._resolved_model(model_override),
            processing_time_ms=elapsed_ms,
            jd_id=referenced_jd_id,
        )

        # Build and persist a learning plan from any skill gaps identified.
        learning_plan = await self.learning_service.build_plan(
            screening_id=row.id,
            candidate_name=candidate.name or "Candidate",
            missing_skills=evaluation.missing_skills,
            weak_skills=evaluation.weak_skills,
            model_override=model_override,
        )

        logger.info(
            "Screening %s persisted with status %s in %dms",
            row.id,
            evaluation.candidate_status,
            elapsed_ms,
        )
        return {
            "screening_id": row.id,
            "candidate": candidate.model_dump(mode="json"),
            "evaluation": evaluation.model_dump(mode="json"),
            "jd": parsed_job.model_dump(mode="json"),
            "learning_plan": learning_plan.model_dump(mode="json"),
            "model_used": self._resolved_model(model_override),
            "processing_time_ms": elapsed_ms,
        }

    async def _build_job(
        self,
        orchestrator: AgentOrchestrator,
        resume_text: str,
        job_description: str,
        model_override: str | None,
    ) -> JobDescription:
        """Extract structured JD data for inline job-description text.

        Unused ``resume_text`` is kept for API symmetry but not referenced.

        Args:
            orchestrator: The agent orchestrator (with user provider if set).
            resume_text: Resume text (unused, retained for symmetry).
            job_description: Raw inline job-description text.
            model_override: Optional LLM model override.

        Returns:
            A structured :class:`JobDescription`.
        """
        kwargs: dict = {}
        if model_override:
            kwargs["model"] = model_override
        return orchestrator.jd_extractor.run(job_description, **kwargs)

    @staticmethod
    def _resolved_model(model_override: str | None) -> str:
        """Resolve the effective LLM model name.

        Args:
            model_override: Optional user-provided model override.

        Returns:
            The override if provided, otherwise the configured default model.
        """
        if model_override:
            return model_override
        return get_settings().llm.llm_model

    async def _resolve_provider_config(self) -> LLMProviderConfig | None:
        """Check for an active user-configured provider (BYOK).

        Returns:
            An :class:`LLMProviderConfig` built from the active provider's
            decrypted credentials, or ``None`` if no active provider exists.
        """
        active = await self.provider_repo.get_active()
        if active is None or not active.is_validated:
            return None
        try:
            from app.services.encryption import decrypt_api_key
            api_key = decrypt_api_key(active.api_key_encrypted)
        except Exception:  # noqa: BLE001
            logger.warning("Failed to decrypt API key for provider %s", active.id)
            return None
        return LLMProviderConfig(
            llm_provider=active.provider,
            llm_model=active.model,
            llm_api_key=api_key,
            llm_api_base=active.api_base,
            llm_max_tokens=active.max_tokens,
            llm_temperature=active.temperature,
        )

    async def _build_orchestrator_for_request(self) -> AgentOrchestrator:
        """Build an orchestrator using the user's active provider if available.

        When a user has configured and validated an AI provider, all agents
        in the pipeline use that provider's API key. Otherwise the system
        default (env-based) provider is used.
        """
        provider_config = await self._resolve_provider_config()
        if provider_config is None:
            return self.orchestrator
        client = LLMClient(config=provider_config)
        from app.agents.evaluator import EvaluatorAgent
        from app.agents.jd_extractor import JDGeneratorAgent
        from app.agents.resume_extractor import ResumeExtractorAgent

        return AgentOrchestrator(
            resume_extractor=ResumeExtractorAgent(client=client),
            jd_extractor=JDGeneratorAgent(client=client),
            evaluator=EvaluatorAgent(client=client),
        )
