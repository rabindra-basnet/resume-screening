"""Web-enrichment service for jobs and learning, safe for serverless use.

Loosely follows a tool-calling pattern: the orchestrator decides a tool call is
needed (e.g. "we lack a JD, let me find what a Senior Backend Engineer needs"),
calls the :mod:`app.tools.web_search` tool, and feeds the compact result back
into the prompt. This avoids asking the LLM to hallucinate job/learning facts
from memory, which both improves accuracy and reduces prompt tokens.
"""

from __future__ import annotations

import logging

from app.tools.web_search import (
    search_job_hints,
    search_learning_path,
)

logger = logging.getLogger(__name__)


class EnrichmentService:
    """Provide live web context for jobs and learning paths.

    All methods are best-effort: on any failure they return empty results so
    the calling pipeline never blocks. Kept dependency-light for cold starts
    on Vercel Fluid Compute.
    """

    async def job_hints(self, job_title: str, *, max_hints: int = 3) -> list[str]:
        """Fetch canonical skill hints for a job title.

        Args:
            job_title: The job title to look up.
            max_hints: Maximum number of snippets to return.

        Returns:
            A list of short snippets, empty if none found.
        """
        if not job_title.strip():
            return []
        return await search_job_hints(job_title.strip(), max_results=max_hints)

    async def learning_path(self, skill: str, *, max_hints: int = 3) -> list[str]:
        """Fetch learning-path snippets for a single skill.

        Args:
            skill: The skill to find a learning path for.
            max_hints: Maximum number of snippets to return.

        Returns:
            A list of short snippets, empty if none found.
        """
        if not skill.strip():
            return []
        return await search_learning_path(skill.strip(), max_results=max_hints)
