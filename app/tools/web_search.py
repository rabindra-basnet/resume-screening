"""Lightweight, serverless-safe web search and fetch utilities.

Uses only ``httpx`` (already a project dependency). No API keys required for
the default instant-answer endpoint, so it works identically on Vercel Fluid
Compute and local dev. Used to enrich job-description context and to discover
learning resources without relying on the LLM's internal knowledge (which
saves tokens by keeping prompts lean).
"""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

DUCKDUCKGO_INSTANT_ANSWER = "https://api.duckduckgo.com/"
TIMEOUT_SECONDS = 8.0
MAX_HTTP_CONNECTIONS = 8


def _client() -> httpx.AsyncClient:
    """Build a bounded async client suitable for serverless cold starts.

    Returns:
        A configured :class:`httpx.AsyncClient`.
    """
    return httpx.AsyncClient(
        timeout=TIMEOUT_SECONDS,
        limits=httpx.Limits(
            max_connections=MAX_HTTP_CONNECTIONS,
            max_keepalive_connections=MAX_HTTP_CONNECTIONS,
        ),
        headers={
            "User-Agent": "agentic-resume-screening/0.1",
            "Accept": "application/json",
        },
    )


async def instant_answer(query: str, *, max_results: int = 5) -> list[str]:
    """Return a compact list of snippets for an instant-answer search.

    This hits DuckDuckGo's no-key Instant Answer API. It returns structured
    results including abstract text and related topics — enough for job hints
    or a single learning-topic pointer without burning LLM tokens.

    Args:
        query: The search query.
        max_results: Maximum number of result rows to collect.

    Returns:
        A list of short text snippets (abstracts + topic names), up to
        ``max_results`` entries. Empty on any error.
    """
    try:
        async with _client() as client:
            resp = await client.get(
                DUCKDUCKGO_INSTANT_ANSWER,
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception:  # noqa: BLE001 - search is best-effort, never block the pipe
        logger.warning("Instant-answer search failed for %r", query, exc_info=True)
        return []

    snippets: list[str] = []
    abstract = (data.get("AbstractText") or "").strip()
    if abstract:
        snippets.append(abstract[:400])

    for topic in data.get("RelatedTopics") or []:
        if len(snippets) >= max_results:
            break
        text = (topic.get("Text") or "").strip()
        if not text and "Topics" in topic:
            for sub in topic["Topics"]:
                if len(snippets) >= max_results:
                    break
                st = (sub.get("Text") or "").strip()
                if st:
                    snippets.append(st[:300])
        elif text:
            snippets.append(text[:300])

    if not snippets:
        # Fall back to the "Definition" / "Heading" fields for sparse queries.
        heading = (data.get("Heading") or "").strip()
        definition = (data.get("Definition") or "").strip()
        for part in (heading, definition):
            if part and len(snippets) < max_results:
                snippets.append(part[:300])

    return snippets[:max_results]


async def fetch_text(url: str, *, max_chars: int = 4000) -> str:
    """Fetch and return trimmed plain text from a URL.

    Args:
        url: The page URL to fetch.
        max_chars: Maximum characters to retain.

    Returns:
        The trimmed text, or an empty string on failure.
    """
    try:
        async with _client() as client:
            resp = await client.get(url, follow_redirects=True)
            resp.raise_for_status()
            text = resp.text
    except Exception:  # noqa: BLE001 - best-effort helper
        logger.warning("Fetch failed for %s", url, exc_info=True)
        return ""
    # Strip HTML-ish tags crudely; good enough for context snippets.
    import re

    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


async def search_job_hints(title: str, *, max_results: int = 3) -> list[str]:
    """Search for canonical details about a job title.

    Args:
        title: A job title (e.g. ``Senior Backend Engineer``).
        max_results: Maximum number of snippets to return.

    Returns:
        Up to ``max_results`` short snippets describing the role's skills.
    """
    return await instant_answer(
        f"{title} job responsibilities required skills", max_results=max_results
    )


async def search_learning_path(skill: str, *, max_results: int = 3) -> list[str]:
    """Search for a curated learning path for a single skill.

    Args:
        skill: A skill name (e.g. ``Kubernetes``).
        max_results: Maximum number of snippets to return.

    Returns:
        Up to ``max_results`` short snippets pointing at learning resources.
    """
    return await instant_answer(
        f"learn {skill} roadmap tutorial", max_results=max_results
    )
