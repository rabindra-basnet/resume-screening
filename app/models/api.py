"""API request and response models.

These models constitute the public HTTP contract of the application. Versioning
is applied at the URL level (``/api/v1``), and these schemas remain stable
within a major version.
"""

from __future__ import annotations

from pydantic import BaseModel

from .candidate import CandidateProfile
from .evaluation import EvaluationResult
from .job_description import JobDescription


class ScreeningRequest(BaseModel):
    """Request body for a resume screening operation.

    Either ``jd_id`` referencing an existing job description, or inline
    ``job_description`` text must be provided.

    Attributes:
        jd_id: Optional identifier of a stored job description.
        job_description: Optional inline job description text.
        model_override: Optional LLM model override for this screening.
    """

    jd_id: str | None = None
    job_description: str | None = None
    model_override: str | None = None


class ScreeningResponse(BaseModel):
    """Full response payload for a completed screening.

    Attributes:
        screening_id: Identifier of the persisted screening result.
        candidate: The extracted candidate profile.
        evaluation: The evaluation outcome.
        jd: The job description the candidate was screened against.
        model_used: The LLM model that produced the evaluation.
    """

    screening_id: str | None = None
    candidate: CandidateProfile
    evaluation: EvaluationResult
    jd: JobDescription | None = None
    model_used: str | None = None


class HealthResponse(BaseModel):
    """Response payload for the health check endpoint.

    Attributes:
        status: Always ``ok`` when the service is healthy.
        app: Name of the running application.
        database: Database connectivity status.
    """

    status: str = "ok"
    app: str = "agentic-resume-screening"
    database: str = "ok"
