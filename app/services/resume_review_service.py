"""Application service running the five resume review agents."""

from __future__ import annotations

import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AgentOrchestrator
from app.agents.llm_client import LLMClient
from app.config.settings import LLMProviderConfig, get_settings
from app.database.repositories.resume_review_repository import ResumeReviewRepository
from app.tools import DocumentParser

logger = logging.getLogger(__name__)


class ResumeReviewService:
    """Runs the five review agents (brutal, ATS, bullets, tone, polish).

    Args:
        session: An async SQLAlchemy session for persistence.
        orchestrator: The agent pipeline.
        review_repo: Repository for review results.
        document_parser: Document text extraction utility.
        provider_repo: Repository for AI provider (BYOK) configurations.
    """

    def __init__(
        self,
        session: AsyncSession,
        orchestrator: AgentOrchestrator | None = None,
        review_repo: ResumeReviewRepository | None = None,
        document_parser: DocumentParser | None = None,
        provider_repo: object | None = None,
    ) -> None:
        """Initialize the review service."""
        self.session = session
        self.orchestrator = orchestrator or AgentOrchestrator()
        self.review_repo = review_repo or ResumeReviewRepository(session)
        self.document_parser = document_parser or DocumentParser()
        self._provider_repo = provider_repo

    @property
    def provider_repo(self):
        """Lazy provider repository to avoid circular imports."""
        if self._provider_repo is None:
            from app.database.repositories.provider_repository import ProviderRepository
            self._provider_repo = ProviderRepository(self.session)
        return self._provider_repo

    async def run_review(
        self,
        resume_bytes: bytes,
        *,
        resume_filename: str = "resume.pdf",
        review_type: str = "full",
        industry: str = "",
        job_description: str = "",
        model_override: str | None = None,
        user_id: str | None = None,
    ) -> dict:
        """Run a resume review and persist the result.

        Args:
            resume_bytes: The raw resume document bytes (PDF or DOCX).
            resume_filename: Original filename of the resume.
            review_type: Which review to run (full/brutal/ats/bullets/tone/polish).
            industry: Optional free-form target industry (for tone matching).
            job_description: Optional JD text (for ATS optimisation).
            model_override: Optional LLM model override.
            user_id: Optional owner user ID.

        Returns:
            A serializable dict with the review results and metadata.

        Raises:
            DocumentParsingError: If the resume document cannot be parsed.
        """
        started = time.monotonic()

        resume_text = self.document_parser.extract_text(resume_bytes, resume_filename)

        # Build orchestrator with the user's BYOK provider if configured.
        orchestrator = await self._build_orchestrator_for_request()

        results = orchestrator.review_resume(
            resume_text,
            industry=industry,
            job_description=job_description,
            review_type=review_type,
        )

        elapsed_ms = int((time.monotonic() - started) * 1000)
        row = await self.review_repo.create(
            resume_filename=resume_filename,
            resume_text=resume_text,
            review_type=review_type,
            review_result=results,
            jd_text=job_description or None,
            industry=industry or None,
            llm_model_used=self._resolved_model(model_override),
            processing_time_ms=elapsed_ms,
            user_id=user_id,
        )

        logger.info(
            "Resume review %s persisted (type=%s) in %dms",
            row.id,
            review_type,
            elapsed_ms,
        )
        return {
            "review_id": row.id,
            "review_type": review_type,
            "results": results,
            "resume_text": resume_text,
            "model_used": self._resolved_model(model_override),
            "processing_time_ms": elapsed_ms,
        }

    @staticmethod
    def _resolved_model(model_override: str | None) -> str:
        """Resolve the effective LLM model name."""
        if model_override:
            return model_override
        return get_settings().llm_model

    async def _resolve_provider_config(self) -> LLMProviderConfig | None:
        """Check for an active user-configured provider (BYOK)."""
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
        """Build an orchestrator using the user's active provider if available."""
        provider_config = await self._resolve_provider_config()
        if provider_config is None:
            return self.orchestrator
        client = LLMClient(config=provider_config)
        from app.agents.evaluator import EvaluatorAgent
        from app.agents.jd_extractor import JDGeneratorAgent
        from app.agents.resume_extractor import ResumeExtractorAgent
        from app.agents.resume_review import (
            ATSOptimizerAgent,
            BrutalReviewAgent,
            BulletPointTransformerAgent,
            FinalPolishAgent,
            IndustryToneMatchAgent,
        )

        return AgentOrchestrator(
            resume_extractor=ResumeExtractorAgent(client=client),
            jd_extractor=JDGeneratorAgent(client=client),
            evaluator=EvaluatorAgent(client=client),
            brutal_review=BrutalReviewAgent(client=client),
            ats_optimizer=ATSOptimizerAgent(client=client),
            bullet_transformer=BulletPointTransformerAgent(client=client),
            industry_tone=IndustryToneMatchAgent(client=client),
            final_polish=FinalPolishAgent(client=client),
        )
