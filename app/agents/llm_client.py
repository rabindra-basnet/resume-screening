"""Thin wrapper around the LiteLLM OpenAI-compatible client.

Centralizes provider configuration, retry logic, timeout handling, and error
normalization so agents remain provider-agnostic. Switching between OpenAI,
Anthropic, or a local OpenAI-compatible endpoint requires only environment
variables, not code changes.
"""

from __future__ import annotations

import logging

import litellm

from app.config.constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
)
from app.config.settings import LLMProviderConfig

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Base exception for LLM request failures."""

    def __init__(self, message: str) -> None:
        """Initialize the exception with the given message."""
        super().__init__(message)
        self.message = message


class LLMTimeoutError(LLMError):
    """Raised when an LLM request exceeds the configured timeout."""


class LLMClient:
    """Provides retrying, timed LLM completion calls via LiteLLM.

    Args:
        config: The LLM provider configuration. Defaults to reading from the
            environment.
    """

    def __init__(self, config: LLMProviderConfig | None = None) -> None:
        """Initialize the client with provider configuration."""
        self.config = config or LLMProviderConfig()

    def _resolve_model(self, model: str) -> str:
        """Resolve a model name that LiteLLM can route to.

        When a custom ``api_base`` is configured, the model must be scoped to
        the ``openai`` provider (``openai/<model>``) so LiteLLM routes to the
        OpenAI-compatible endpoint instead of failing to infer a provider.

        Args:
            model: The raw model name from config or an override.

        Returns:
            The model string to pass to LiteLLM.
        """
        if not self.config.llm_api_base:
            return model
        if model.startswith("openai/"):
            return model
        return f"openai/{model}"

    def _api_params(self) -> dict:
        """Build the provider-specific API keyword arguments.

        When a custom ``api_base`` is configured without an API key (e.g. the
        OpenCode Zen free tier), the OpenAI SDK still demands a key. A dummy
        key plus an empty ``Authorization`` header lets keyless endpoints
        accept the request while any real key is forwarded untouched.

        Returns:
            A dict with ``api_key`` and ``api_base`` populated only when set,
            preserving OpenRouter/local-proxy compatibility.
        """
        params: dict = {}
        if self.config.llm_api_key:
            params["api_key"] = self.config.llm_api_key
        elif self.config.llm_api_base:
            params["api_key"] = "dummy"
            params["extra_headers"] = {"Authorization": ""}
        if self.config.llm_api_base:
            params["api_base"] = self.config.llm_api_base
        return params

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        """Run an LLM completion and return the assistant message content.

        Args:
            system_prompt: System-level instructions establishing the assistant role.
            user_prompt: The user-provided input for the request.
            model: Optional model override; defaults to configured model.
            temperature: Optional temperature override.
            max_tokens: Optional max output token override.

        Returns:
            The assistant's text response.

        Raises:
            LLMTimeoutError: If the call exceeds the configured timeout.
            LLMError: For any other non-retriable completion failure.
        """
        resolved_model = self._resolve_model(model or self.config.llm_model)
        resolved_temperature = self.config.llm_temperature if temperature is None else temperature
        resolved_max_tokens = self.config.llm_max_tokens if max_tokens is None else max_tokens
        timeout = self.config.llm_timeout_seconds or DEFAULT_TIMEOUT_SECONDS
        retries = self.config.llm_max_retries or DEFAULT_MAX_RETRIES

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        for attempt in range(1, retries + 1):
            try:
                response = litellm.completion(
                    model=resolved_model,
                    messages=messages,
                    temperature=resolved_temperature,
                    max_tokens=resolved_max_tokens,
                    timeout=timeout,
                    **self._api_params(),
                )
                content = response.choices[0].message.content
                if content is None:
                    raise LLMError("LLM returned an empty response")
                return content
            except LLMError:
                raise
            except Exception as exc:  # noqa: BLE001 - normalize provider errors
                logger.warning("LLM call attempt %d/%d failed: %s", attempt, retries, exc)
                if attempt == retries:
                    raise LLMError(f"LLM request failed after {retries} attempts: {exc}") from exc

        raise LLMError("Reached unreachable code path in retry loop")  # pragma: no cover
