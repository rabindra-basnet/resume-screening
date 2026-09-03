"""AI provider (BYOK) management endpoints for the v1 API."""

from __future__ import annotations

import logging
import time
from typing import Annotated

import litellm
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import get_provider_repo
from app.database.repositories import ProviderRepository
from app.database.schema import AIProviderModel
from app.models.provider import (
    ProviderActivateResponse,
    ProviderCreate,
    ProviderRead,
    ProviderUpdate,
    ProviderValidateResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/providers", tags=["providers"])


def _to_read(row: AIProviderModel) -> ProviderRead:
    """Convert an ORM provider row into a :class:`ProviderRead`.

    Args:
        row: The ORM provider row.

    Returns:
        The corresponding Pydantic provider read model.
    """
    return ProviderRead(
        id=row.id,
        name=row.name,
        provider=row.provider,
        model=row.model,
        api_base=row.api_base,
        max_tokens=row.max_tokens,
        temperature=row.temperature,
        is_active=row.is_active,
        is_validated=row.is_validated,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _validate_litellm(provider: AIProviderModel, api_key: str) -> tuple[bool, str]:
    """Attempt a minimal LiteLLM completion and report success or failure.

    Args:
        provider: The provider row holding model and endpoint details.
        api_key: The decrypted plaintext API key.

    Returns:
        A tuple of ``(bool, message)`` where the bool indicates success.
    """
    params: dict = {"api_key": api_key}
    model = provider.model
    if provider.api_base:
        params["api_base"] = provider.api_base
        if not model.startswith("openai/"):
            model = f"openai/{model}"
    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
            timeout=10,
            **params,
        )
        _ = response.choices[0].message.content
        return True, "API key validated successfully"
    except Exception as exc:  # noqa: BLE001 - normalize all provider errors
        logger.warning("Provider validation failed for %s: %s", provider.name, exc)
        return False, f"Validation failed: {exc}"


@router.post(
    "",
    response_model=ProviderRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create an AI provider",
)
async def create_provider(
    payload: ProviderCreate,
    repo: Annotated[ProviderRepository, Depends(get_provider_repo)],
) -> ProviderRead:
    """Create and persist a new AI provider configuration.

    Args:
        payload: The provider name, slug, model, and API key.
        repo: The injected provider repository.

    Returns:
        The persisted :class:`ProviderRead`.
    """
    row = await repo.create(
        name=payload.name,
        provider=payload.provider,
        model=payload.model,
        api_key=payload.api_key,
        api_base=payload.api_base,
        max_tokens=payload.max_tokens,
        temperature=payload.temperature,
    )
    return _to_read(row)


@router.get("", response_model=list[ProviderRead], summary="List all AI providers")
async def list_providers(
    repo: Annotated[ProviderRepository, Depends(get_provider_repo)],
) -> list[ProviderRead]:
    """Return all configured AI providers.

    Args:
        repo: The injected provider repository.

    Returns:
        A list of :class:`ProviderRead`.
    """
    rows = await repo.list_all()
    return [_to_read(row) for row in rows]


@router.get("/{provider_id}", response_model=ProviderRead, summary="Get an AI provider")
async def get_provider(
    provider_id: str,
    repo: Annotated[ProviderRepository, Depends(get_provider_repo)],
) -> ProviderRead:
    """Fetch a single AI provider by id.

    Args:
        provider_id: The provider primary key.
        repo: The injected provider repository.

    Returns:
        The matching :class:`ProviderRead`.

    Raises:
        HTTPException: If the provider is not found.
    """
    row = await repo.get(provider_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    return _to_read(row)


@router.get("/{provider_id}/key", summary="Get the decrypted API key for a provider")
async def get_provider_key(
    provider_id: str,
    repo: Annotated[ProviderRepository, Depends(get_provider_repo)],
    reveal: bool = Query(default=False, description="Return the full plaintext key"),
) -> dict:
    """Decrypt and return the API key for a provider.

    By default the key is masked. Pass ``?reveal=true`` to return the full key.

    Args:
        provider_id: The provider primary key.
        repo: The injected provider repository.
        reveal: Whether to return the full plaintext key.

    Returns:
        A dict with the masked (or full) key.

    Raises:
        HTTPException: If the provider is not found.
    """
    row = await repo.get(provider_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    key = repo.decrypt_key(row)
    if reveal:
        return {"id": row.id, "api_key": key}
    masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "****"
    return {"id": row.id, "api_key": masked}


@router.put("/{provider_id}", response_model=ProviderRead, summary="Update an AI provider")
async def update_provider(
    provider_id: str,
    payload: ProviderUpdate,
    repo: Annotated[ProviderRepository, Depends(get_provider_repo)],
) -> ProviderRead:
    """Update fields on an existing AI provider.

    Args:
        provider_id: The provider primary key.
        payload: The fields to update.
        repo: The injected provider repository.

    Returns:
        The updated :class:`ProviderRead`.

    Raises:
        HTTPException: If the provider is not found.
    """
    try:
        row = await repo.update(
            provider_id,
            name=payload.name,
            provider=payload.provider,
            model=payload.model,
            api_key=payload.api_key,
            api_base=payload.api_base,
            max_tokens=payload.max_tokens,
            temperature=payload.temperature,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _to_read(row)


@router.delete(
    "/{provider_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an AI provider",
)
async def delete_provider(
    provider_id: str,
    repo: Annotated[ProviderRepository, Depends(get_provider_repo)],
) -> None:
    """Delete an AI provider by id.

    Args:
        provider_id: The provider primary key.
        repo: The injected provider repository.

    Raises:
        HTTPException: If the provider is not found.
    """
    deleted = await repo.delete(provider_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Provider not found")


@router.post(
    "/{provider_id}/activate",
    response_model=ProviderActivateResponse,
    summary="Activate an AI provider",
)
async def activate_provider(
    provider_id: str,
    repo: Annotated[ProviderRepository, Depends(get_provider_repo)],
) -> ProviderActivateResponse:
    """Set a provider as the single active provider for screenings.

    Args:
        provider_id: The provider primary key.
        repo: The injected provider repository.

    Returns:
        The activation confirmation.

    Raises:
        HTTPException: If the provider is not found.
    """
    try:
        row = await repo.set_active(provider_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ProviderActivateResponse(id=row.id, name=row.name)


@router.post(
    "/{provider_id}/validate",
    response_model=ProviderValidateResponse,
    summary="Validate an AI provider API key",
)
async def validate_provider(
    provider_id: str,
    repo: Annotated[ProviderRepository, Depends(get_provider_repo)],
) -> ProviderValidateResponse:
    """Test the provider's API key with a minimal LiteLLM completion.

    Args:
        provider_id: The provider primary key.
        repo: The injected provider repository.

    Returns:
        The validation result including success status and latency.

    Raises:
        HTTPException: If the provider is not found.
    """
    row = await repo.get(provider_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Provider not found")

    start = time.monotonic()
    success, message = _validate_litellm(row, repo.decrypt_key(row))
    latency_ms = int((time.monotonic() - start) * 1000)

    await repo.update(provider_id, is_validated=success)

    return ProviderValidateResponse(
        id=row.id,
        success=success,
        message=message,
        latency_ms=latency_ms,
    )
