"""Pydantic models for AI provider configuration contracts."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ProviderCreate(BaseModel):
    """Request body for creating a new AI provider configuration.

    Attributes:
        name: Human-readable label for this provider configuration.
        provider: Provider slug (``openai``, ``anthropic``, ``azure``, etc.).
        model: The model identifier to use.
        api_key: The plaintext API key, encrypted before persistence.
        api_base: Optional base URL override for OpenAI-compatible endpoints.
        max_tokens: Max output tokens for this provider.
        temperature: Sampling temperature.
    """

    name: str
    provider: str
    model: str
    api_key: str
    api_base: str | None = None
    max_tokens: int = Field(default=2000, ge=1)
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)


class ProviderUpdate(BaseModel):
    """Request body for updating a subset of provider fields.

    Attributes:
        name: Optional human-readable label.
        provider: Optional provider slug.
        model: Optional model identifier.
        api_key: Optional plaintext API key to re-encrypt and store.
        api_base: Optional base URL override.
        max_tokens: Optional max output tokens.
        temperature: Optional sampling temperature.
    """

    name: str | None = None
    provider: str | None = None
    model: str | None = None
    api_key: str | None = None
    api_base: str | None = None
    max_tokens: int | None = Field(default=None, ge=1)
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)


class ProviderRead(BaseModel):
    """Response model for a stored AI provider configuration.

    Never includes the API key ciphertext; the key is only exposed through the
    dedicated key endpoint.

    Attributes:
        id: Primary key (UUID string).
        name: Human-readable label.
        provider: Provider slug.
        model: Model identifier.
        api_base: Optional base URL override.
        max_tokens: Max output tokens.
        temperature: Sampling temperature.
        is_active: Whether this is the active provider.
        is_validated: Whether the key has been validated successfully.
        created_at: Row creation timestamp.
        updated_at: Row last-update timestamp.
    """

    id: str
    name: str
    provider: str
    model: str
    api_base: str | None = None
    max_tokens: int = 2000
    temperature: float = 0.1
    is_active: bool = False
    is_validated: bool = False
    created_at: datetime
    updated_at: datetime


class ProviderActivateResponse(BaseModel):
    """Response model for the activate endpoint.

    Attributes:
        id: The activated provider's id.
        name: The activated provider's name.
        is_active: Always ``True`` for the newly activated provider.
    """

    id: str
    name: str
    is_active: bool = True


class ProviderValidateResponse(BaseModel):
    """Response model for the validate endpoint.

    Attributes:
        id: The validated provider's id.
        success: Whether the API key produced a successful completion.
        message: Human-readable result message.
        latency_ms: Time taken for the completion attempt in milliseconds.
    """

    id: str
    success: bool
    message: str
    latency_ms: int | None = None
