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
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = Field(default="")
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
    app_origin: str = "http://localhost:8000"

    # ── LLM provider ──────────────────────────────────────────────────
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_api_key: str = Field(default="", description="API key for primary provider")
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
    session_secret: str = Field(default="", alias="session_secret")  # noqa: S105
    session_cookie_name: str = "session"
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

        if not self.session_secret or self.session_secret == "":
            if self.app_env == "production":
                errors.append("SESSION_SECRET_KEY is required in production")

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
