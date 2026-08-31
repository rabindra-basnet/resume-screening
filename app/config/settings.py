"""Pydantic settings models for application and LLM-provider configuration.

Provides type-safe access to environment variables via ``pydantic-settings``.
The configuration supports multiple OpenAI-compatible providers (OpenAI,
Anthropic, local proxies such as vLLM/Ollama, Azure, etc.) so the active
provider can be switched entirely through environment variables.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProviderConfig(BaseSettings):
    """Configuration for the primary and optional fallback LLM provider.

    Attributes:
        llm_provider: The active provider name (``openai``, ``anthropic``,
            ``azure``, or a custom ``openai``-compatible endpoint).
        llm_model: The model identifier used by the active provider.
        llm_api_key: API key for the primary provider.
        llm_api_base: Optional base URL override for OpenAI-compatible endpoints.
        llm_fallback_model: Optional fallback model when the primary fails.
        llm_fallback_api_key: API key for the fallback provider.
        llm_fallback_api_base: Optional base URL for the fallback provider.
        llm_max_tokens: Maximum tokens in the model response.
        llm_temperature: Sampling temperature (low for structured extraction).
        llm_timeout_seconds: Per-call timeout in seconds.
        llm_max_retries: Number of automatic retries for transient failures.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

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


class Settings(BaseSettings):
    """Top-level application settings aggregating all environment config.

    Attributes:
        app_name: Human-readable application name.
        app_env: Deployment environment (``development``, ``production``).
        debug: Enable debug-level logging and verbose error surfaces.
        database_url: SQLAlchemy database URL. Supports SQLite in development
            and PostgreSQL (e.g. Neon) in production.
        llm: Nested LLM (openai-compatible) provider configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "agentic-resume-screening"
    app_env: Literal["development", "production", "staging"] = "development"
    debug: bool = True

    database_url: str = "sqlite:///./screening.db"

    llm: LLMProviderConfig = LLMProviderConfig()


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
