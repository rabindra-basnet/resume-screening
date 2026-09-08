"""Pydantic settings models for application configuration.

Provides type-safe access to environment variables via ``pydantic-settings``.
All config is flat at the top level with runtime validation that checks
required env vars based on which features are enabled.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderConfig(BaseModel):
    """Plain data object for LLM provider credentials.

    Used as a transfer type when resolving BYOK provider configs —
    not a settings reader.
    """

    llm_provider: str = "openai"
    # 'big-pickle' is a verified working free model on the OpenCode Zen gateway
    # (returns content directly). Override via LLM_MODEL when moving providers.
    llm_model: str = "big-pickle"
    # Placeholder key so the OpenAI-compatible client always sees an api_key.
    # Swap it via LLM_API_KEY when moving to a paid provider; the dummy value
    # only matters to satisfy client construction for keyless/self-hosted
    # OpenAI-compatible endpoints.
    llm_api_key: str = Field(default="sk-dummy")
    llm_api_base: str | None = None
    llm_max_tokens: int = 2000
    llm_temperature: float = 0.1
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 3

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings — flat, with runtime validation.

    Validates required env vars at startup based on which features are
    enabled (e.g. ``GOOGLE_CLIENT_ID`` is required when auth is used,
    ``AWS_*`` vars are required when ``STORAGE_BACKEND=s3``).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── General ────────────────────────────────────────────────────────
    app_name: str = "agentic-resume-screening"
    app_env: Literal["development", "production", "staging"] = "development"
    debug: bool = True
    database_url: str = "sqlite:///./screening.db"
    # Public origin (e.g. https://ats.saastralabs.com). Leave empty to derive
    # it from each request instead (see app.api.v1.auth._public_origin); set it
    # explicitly when the app runs behind a proxy that rewrites the origin.
    app_origin: str = ""

    # ── LLM provider ──────────────────────────────────────────────────
    llm_provider: str = "openai"
    # 'big-pickle' is a verified working free model on the OpenCode Zen gateway.
    llm_model: str = "big-pickle"
    # Placeholder key (see LLMProviderConfig): keeps the OpenAI-compatible
    # client constructible while ''LLM_API_KEY'' is unset; replace on Vercel
    # when moving to a paid provider.
    llm_api_key: str = Field(default="sk-dummy", description="API key for primary provider")
    llm_api_base: str | None = None
    llm_fallback_model: str | None = None
    llm_fallback_api_key: str | None = None
    llm_fallback_api_base: str | None = None
    llm_max_tokens: int = 2000
    llm_temperature: float = 0.1
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 3

    # ── Google OAuth ───────────────────────────────────────────────────
    google_client_id: str = ""
    google_client_secret: str = ""

    # ── Session ────────────────────────────────────────────────────────
    # Signs Starlette's OAuth ``state`` cookie (see oauth_state_cookie_name).
    session_secret: str = Field(default="", alias="session_secret")  # noqa: S105
    # Cookie that holds the opaque id of the user's row in the ``sessions``
    # table (created at Google login, storing the validated Google JWT).
    session_cookie_name: str = "aether_session"
    # Separate cookie for Starlette's SessionMiddleware, which only carries the
    # short-lived OAuth ``state`` between the /login/google and /callback/google
    # requests. It MUST NOT share a name with the auth cookie above — if it did,
    # the middleware would overwrite (and on callback, clear) the auth cookie.
    oauth_state_cookie_name: str = "aether_oauth_state"
    session_cookie_max_age: int = 7 * 24 * 60 * 60  # 7 days

    # ── Storage (switchable) ───────────────────────────────────────────
    storage_backend: Literal["", "blob", "s3"] = ""

    # Vercel Blob
    blob_read_write_token: str = ""

    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_s3_bucket: str = ""
    aws_region: str = "us-east-1"
    aws_endpoint_url: str | None = None

    # ── Runtime validation ─────────────────────────────────────────────
    @model_validator(mode="after")
    def _validate_required_vars(self) -> Settings:
        """Check that required env vars are present based on feature flags."""
        errors: list[str] = []

        if not self.google_client_id or not self.google_client_secret:
            logger.warning(
                "GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not set — "
                "Google OAuth will be unavailable"
            )

        if self.storage_backend == "blob" and not self.blob_read_write_token:
            errors.append(
                "BLOB_READ_WRITE_TOKEN is required when STORAGE_BACKEND=blob"
            )

        if self.storage_backend == "s3":
            missing = [
                name
                for name in ("aws_access_key_id", "aws_secret_access_key", "aws_s3_bucket")
                if not getattr(self, name)
            ]
            if missing:
                errors.append(
                    f"Missing S3 env vars: {', '.join(missing)} "
                    "(required when STORAGE_BACKEND=s3)"
                )

        if not self.session_secret:
            if self.google_client_secret:
                import hashlib
                self.session_secret = hashlib.sha256(self.google_client_secret.encode()).hexdigest()
            else:
                self.session_secret = "talentpulse_default_session_secret_key_2026"  # noqa: S105

        if errors:
            raise ValueError("Configuration error: " + "; ".join(errors))

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton instance of :class:`Settings`.

    Caching avoids repeatedly re-parsing environment variables on every
    request, which is important for reducing cold-start overhead on serverless
    deployment targets (Vercel Fluid Compute).

    Returns:
        The application settings singleton.
    """
    return Settings()
