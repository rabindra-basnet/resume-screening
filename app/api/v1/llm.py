"""LLM capability endpoints for the v1 API.

Provides runtime discovery of the models the configured gateway advertises,
so the UI can offer a dynamic model picker instead of a static list.
"""

from __future__ import annotations

import time

from fastapi import APIRouter, HTTPException

from app.agents.llm_client import LLMClient, LLMError
from app.config.settings import get_settings

router = APIRouter(prefix="/llm", tags=["llm"])

_cache: dict = {"ts": 0.0, "payload": None}
_CACHE_TTL_SECONDS = 300

# Models usable on the keyless OpenCode Zen free tier that don't carry a
# ``-free`` suffix (e.g. ``big-pickle``, our working default). Kept in sync
# with the configured default so it always appears in the picker.
_EXTRA_FREE_MODELS = {"big-pickle"}


def _list_models() -> dict:
    """Return the usable model list with light caching.

    Returns:
        A dict with ``default_model`` and a ``models`` list of ``{id, is_default}``.

    Raises:
        HTTPException: If the gateway cannot be reached.
    """
    now = time.monotonic()
    if _cache["payload"] and (now - _cache["ts"]) < _CACHE_TTL_SECONDS:
        return _cache["payload"]

    settings = get_settings()
    default_model = settings.llm_model
    try:
        client = LLMClient()
        free = client.list_models(free_only=True)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    ids = [m["id"] for m in free]
    for extra in _EXTRA_FREE_MODELS:
        if extra and extra not in ids:
            ids.append(extra)
    ids.sort()

    models = [{"id": mid, "is_default": mid == default_model} for mid in ids]
    payload = {"default_model": default_model, "models": models}
    _cache["ts"] = now
    _cache["payload"] = payload
    return payload


@router.get("/models", summary="List available LLM models")
async def list_models() -> dict:
    """Return the models the configured gateway exposes for screening.

    Returns:
        A dict with the currently configured ``default_model`` and a ``models``
        list of ``{id, is_default}`` entries, discovered dynamically from the
        live gateway.
    """
    return _list_models()
