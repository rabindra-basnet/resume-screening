"""Application service orchestrating the end-to-end screening workflow.

Coordinates PDF parsing, job-description resolution/caching, agent execution,
and persistence of results. This is the primary business-logic entry point used
by the API layer.
"""

from __future__ import annotations

import logging
import time

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents import AgentOrchestrator
from app.config.settings import get_settings
from app.database.repositories import JDRepository, ResumeRepository
from app.models.job_description import JobDescription
from app.tools import PDFParser

logger = logging.getLogger(__name__)


class ScreeningService:
    """High-level screening workflow orchestrator.

    Args:
        session: An async SQLAlchemy session for persistence.
        orchestrator: The agent pipeline. Defaults to a new orchestrator.
        jd_repo: Repository for job-description persistence/caching.
        resume_repo: Repository for screening-result persistence.
        pdf_parser: PDF text extraction utility.
    """

    def __init__(
        self,
        session: AsyncSession,
        orchestrator: AgentOrchestrator | None = None,
        jd_repo: JDRepository | None = None,
        resume_repo: ResumeRepository | None = None,
        pdf_parser: PDFParser | None = None,
    ) -> None:
        """Initialize the screening service with its dependencies."""
        self.session = session
        self.orchestrator = orchestrator or AgentOrchestrator()
        self.jd_repo = jd_repo or JDRepository(session)
        self.resume_repo = resume_repo or ResumeRepository(session)
        self.pdf_parser = pdf_parser or PDFParser()

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
            resume_bytes: The raw resume PDF bytes.
            resume_filename: Original filename of the uploaded resume.
            job_description: Optional inline job-description raw text. When
                omitted, the JD is loaded from storage via ``jd_id``.
            jd_id: Optional id of a stored job description to load.
            model_override: Optional LLM model override for the pipeline.

        Returns:
            A serializable dict containing the candidate, job, evaluation,
            screening id, model used, and processing time.

        Raises:
            PDFParsingError: If the resume PDF cannot be parsed.
            RuntimeError: If no job description can be resolved.
        """
        started = time.monotonic()

        referenced_jd_id = jd_id
        resume_text = self.pdf_parser.extract_text(resume_bytes)

        if job_description is not None:
            # Extract structured JD from inline text and persist for reuse.
            job = await self._build_job(resume_text, job_description, model_override)
            persisted = await self.jd_repo.upsert(job)
            referenced_jd_id = persisted.id
        elif jd_id:
            model = await self.jd_repo.get(jd_id)
            if model is None:
                raise RuntimeError(f"Job description {jd_id} not found")
            job = JDRepository._from_model(model)
        else:
            raise RuntimeError("A persisted jd_id or job description text is required")

        candidate, parsed_job, evaluation = self.orchestrator.screen(resume_text, job.raw_text)

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
            "model_used": self._resolved_model(model_override),
            "processing_time_ms": elapsed_ms,
        }

    async def _build_job(
        self,
        resume_text: str,
        job_description: str,
        model_override: str | None,
    ) -> JobDescription:
        """Extract structured JD data for inline job-description text.

        Unused ``resume_text`` is kept for API symmetry but not referenced.

        Args:
            resume_text: Resume text (unused, retained for symmetry).
            job_description: Raw inline job-description text.
            model_override: Optional LLM model override.

        Returns:
            A structured :class:`JobDescription`.
        """
        kwargs: dict = {}
        if model_override:
            kwargs["model"] = model_override
        return self.orchestrator.jd_extractor.run(job_description, **kwargs)

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
