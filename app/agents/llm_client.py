"""Thin wrapper around the OpenAI Python client.

Centralizes provider configuration, retry logic, timeout handling, and error
normalization so agents remain provider-agnostic. Switching between OpenAI,
Anthropic-backed OpenAI-compatible endpoints, or a local OpenAI-compatible
endpoint requires only environment variables, not code changes.
"""

from __future__ import annotations

import logging
import os
import uuid

from openai import OpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)

from app.config.constants import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
)
from app.config.settings import LLMProviderConfig, get_settings

logger = logging.getLogger(__name__)

# Placeholder api_key (also the default in app.config.settings). When the
# configured key equals this sentinel the provider is treated as keyless: the
# OpenAI client still gets a non-empty key (so it constructs) but an empty
# ``Authorization`` header is sent, which keyless OpenAI-compatible gateways
# require. Any other value is sent as a real bearer key.
PLACEHOLDER_API_KEY = "sk-dummy"

# The OpenCode Zen gateway requires its free tier to be reached the way the
# OpenCode client does: a per-conversation session id plus OpenCode attribution
# headers. Without these, free models return ``MissingSessionID``. A stable
# session id (per conversation) also unlocks prompt-cache affinity on paid
# models. These headers are only added when the target base URL is Zen.
OPENCODE_ZEN_HOST = "opencode.ai"
# Header the gateway uses to attribute a conversation. OpenCode sends a stable
# id per conversation; we default to a per-client generated id but allow a
# caller to pin one (e.g. a real end-user session) via env for cache affinity.
_SESSION_ID_MAX_LEN = 64


def _open_code_headers(session_id: str) -> dict:
    """Build the attribution/session headers OpenCode sends to its Zen gateway.

    Args:
        session_id: A stable id for the current conversation.

    Returns:
        A dict of ``x-opencode-*`` headers required by ``opencode.ai/zen``.
    """
    return {
        "User-Agent": "opencode/1.15.0 ai-sdk/provider-utils/4.0.23 runtime/python",
        "x-opencode-client": "cli",
        "x-opencode-project": "global",
        "x-opencode-request": f"msg_{uuid.uuid4().hex[:16]}",
        "x-opencode-session": session_id,
    }


def _is_open_code_zen(base_url: str | None) -> bool:
    """Return True when ``base_url`` targets the OpenCode Zen gateway."""
    if not base_url:
        return False
    return OPENCODE_ZEN_HOST in base_url.replace("https://", "").replace("http://", "")


def _is_structured_output_rejected(exc: Exception) -> bool:
    """Return True when ``exc`` indicates the provider does not support structured output.

    Gateways respond differently when they do not implement ``response_format``:
    OpenAI raises ``BadRequestError``/``UnprocessableEntityError`` with status
    400/422, while some proxies simply return a generic 404. Classify by status
    code and message hints so we only degrade to plain completions for genuine
    "unsupported param" failures and keep normal retry behaviour otherwise.

    Args:
        exc: The exception raised by the call.

    Returns:
        True when the failure is best handled by dropping ``response_format``.
    """
    status = getattr(exc, "status_code", None)
    if status in (400, 404, 422):
        return True
    text = str(exc).lower()
    return any(
        hint in text
        for hint in (
            "response_format",
            "json_schema",
            "structured output",
            "unsupported parameter",
            "not support",
        )
    )


class LLMError(Exception):
    """Base exception for LLM request failures."""

    def __init__(self, message: str) -> None:
        """Initialize the exception with the given message."""
        super().__init__(message)
        self.message = message


class LLMTimeoutError(LLMError):
    """Raised when an LLM request exceeds the configured timeout."""


class LLMClient:
    """Provides retrying, timed LLM completion calls via the OpenAI client.

    Args:
        config: The LLM provider configuration. Defaults to reading from the
            environment.
    """

    def __init__(self, config: LLMProviderConfig | None = None) -> None:
        """Initialize the client with provider configuration.

        When no explicit config is passed, it is populated from the application
        environment (``get_settings()``) so that ``LLM_API_BASE``, ``LLM_MODEL``
        and friends defined for the deployment are honoured — not just the
        hardcoded ``LLMProviderConfig`` defaults. This lets keyless
        OpenAI-compatible endpoints (e.g. a gateway with ``LLM_API_BASE`` and no
        ``LLM_API_KEY``) be used by the default agent orchestrator.

        Args:
            config: An explicit provider config, or ``None`` to read from env.
        """
        if config is None:
            settings = get_settings()
            config = LLMProviderConfig(
                llm_provider=settings.llm_provider,
                llm_model=settings.llm_model,
                llm_api_key=settings.llm_api_key,
                llm_api_base=settings.llm_api_base,
                llm_max_tokens=settings.llm_max_tokens,
                llm_temperature=settings.llm_temperature,
                llm_timeout_seconds=settings.llm_timeout_seconds,
                llm_max_retries=settings.llm_max_retries,
            )
        self.config = config
        # A stable per-client conversation id used for OpenCode Zen attribution
        # and cache affinity. Callers may pin a real user session via an env var.
        configured_session = os.getenv("OPENCODE_SESSION_ID", "").strip()
        if configured_session:
            self.session_id = configured_session[:_SESSION_ID_MAX_LEN]
        else:
            self.session_id = f"ses_{uuid.uuid4().hex}"

    def _build_client(self) -> OpenAI:
        """Build an :class:`OpenAI` client for the configured provider.

        When a custom ``api_base`` is set (OpenRouter, local proxies, etc.) the
        OpenAI client's ``base_url`` routes to that OpenAI-compatible endpoint.
        Keyless endpoints (e.g. local gateways) receive a dummy key plus an
        empty ``Authorization`` header so the request is accepted while any real
        key is forwarded untouched.

        For the OpenCode Zen gateway the request additionally carries the
        ``x-opencode-*`` headers and a session id that the OpenCode client
        normally sends — without them the free tier returns ``MissingSessionID``.
        A placeholder key is mapped to ``Bearer public`` (the keyless free tier);
        a real key keeps the bearer header as-is for paid models.

        Returns:
            A configured OpenAI client.
        """
        kwargs: dict = {"timeout": self.config.llm_timeout_seconds or DEFAULT_TIMEOUT_SECONDS}
        api_key = self.config.llm_api_key
        is_placeholder = bool(api_key) and api_key.strip() == PLACEHOLDER_API_KEY
        is_zen = _is_open_code_zen(self.config.llm_api_base)

        default_headers: dict = {}
        if is_zen:
            default_headers = _open_code_headers(self.session_id)

        if api_key and not is_placeholder:
            # A real key: send it as the bearer Authorization header.
            kwargs["api_key"] = api_key
        elif is_zen:
            # Zen free tier is keyless; OpenCode routes it via the attribution
            # headers. Leave the Authorization header empty rather than sending
            # a placeholder bearer token, which some upstream providers reject.
            kwargs["api_key"] = "public"
            default_headers["Authorization"] = ""
        else:
            # Placeholder or empty key on a generic endpoint: construct with a
            # non-empty key so the OpenAI client doesn't raise, but blank the
            # Authorization header so keyless gateways accept the request.
            kwargs["api_key"] = api_key or "dummy"
            if self.config.llm_api_base:
                default_headers["Authorization"] = ""

        if default_headers:
            kwargs["default_headers"] = default_headers
        if self.config.llm_api_base:
            kwargs["base_url"] = self.config.llm_api_base
        return OpenAI(**kwargs)

    def list_models(
        self, *, free_only: bool = False, timeout: float | None = None
    ) -> list[dict]:
        """List the models the configured gateway advertises.

        Hits the OpenAI-compatible ``/models`` endpoint so the available set is
        discovered dynamically from the live deployment rather than hardcoded.
        For the OpenCode Zen gateway the same attribution/session headers are
        sent so the keyless free tier is honoured.

        Args:
            free_only: When true, only return models usable without a paid key
                (those whose ids end with a ``-free``/``contributor-free`` marker
                on the OpenCode Zen gateway).
            timeout: Optional request timeout in seconds.

        Returns:
            A list of model dicts (``id`` and any extra gateway metadata).

        Raises:
            LLMError: If the model list cannot be fetched.
        """
        base = (self.config.llm_api_base or "").rstrip("/")
        if not base:
            raise LLMError("LLM_API_BASE is not configured; cannot list models")
        api_key = self.config.llm_api_key
        is_placeholder = bool(api_key) and api_key.strip() == PLACEHOLDER_API_KEY
        is_zen = _is_open_code_zen(self.config.llm_api_base)
        headers: dict = {}
        if is_zen:
            headers = _open_code_headers(self.session_id)
        if api_key and not is_placeholder:
            headers["Authorization"] = f"Bearer {api_key}"
        elif is_zen:
            headers["Authorization"] = ""
        timeout = timeout or self.config.llm_timeout_seconds or DEFAULT_TIMEOUT_SECONDS
        try:
            import httpx

            resp = httpx.get(
                f"{base}/models",
                headers=headers,
                timeout=timeout,
            )
            resp.raise_for_status()
            models = resp.json().get("data", []) or []
        except Exception as exc:  # noqa: BLE001 - normalize provider errors
            raise LLMError(f"Failed to list models: {exc}") from exc

        normalized: list[dict] = []
        for m in models:
            mid = str(m.get("id") or "").strip()
            if not mid:
                continue
            normalized.append({"id": mid, **{k: v for k, v in m.items() if k != "id"}})

        if free_only:
            normalized = [
                m for m in normalized if m["id"].endswith("-free")
            ]
        return normalized

    def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        *,
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
    ) -> str:
        """Run an LLM completion and return the assistant message content.

        Args:
            system_prompt: System-level instructions establishing the assistant role.
            user_prompt: The user-provided input for the request.
            model: Optional model override; defaults to configured model.
            temperature: Optional temperature override.
            max_tokens: Optional max output token override.
            response_format: Optional OpenAI-style structured-output specification
                (e.g. ``{"type": "json_object"}`` or a ``json_schema`` object).
                When the provider rejects it, the call degrades gracefully to a
                plain completion so pipelines keep working on gateways that do
                not implement structured output.

        Returns:
            The assistant's text response.

        Raises:
            LLMTimeoutError: If the call exceeds the configured timeout.
            LLMError: For any other non-retriable completion failure.
        """
        resolved_model = model or self.config.llm_model
        resolved_temperature = self.config.llm_temperature if temperature is None else temperature
        resolved_max_tokens = self.config.llm_max_tokens if max_tokens is None else max_tokens
        timeout = self.config.llm_timeout_seconds or DEFAULT_TIMEOUT_SECONDS
        retries = self.config.llm_max_retries or DEFAULT_MAX_RETRIES

        messages: list[
            ChatCompletionSystemMessageParam | ChatCompletionUserMessageParam
        ] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        attempt = 0
        while attempt < retries:
            attempt += 1
            try:
                client = self._build_client()
                kwargs: dict = {
                    "model": resolved_model,
                    "messages": messages,
                    "temperature": resolved_temperature,
                    "max_tokens": resolved_max_tokens,
                    "timeout": timeout,
                }
                if response_format is not None:
                    kwargs["response_format"] = response_format
                response = client.chat.completions.create(**kwargs)
                message = response.choices[0].message
                content = message.content
                # Some reasoning models (e.g. OpenCode Zen free reasoners) put
                # their answer in ``reasoning`` and leave ``content`` empty.
                # Fall back to the reasoning text so the call still succeeds.
                if content is None and getattr(message, "reasoning", None):
                    content = message.reasoning
                if content is None:
                    raise LLMError("LLM returned an empty response")
                return content
            except LLMError:
                raise
            except Exception as exc:  # noqa: BLE001 - normalize provider errors
                # Structured output is not implemented by every OpenAI-compatible
                # gateway. Degrade to a plain completion instead of failing the
                # whole pipeline; the base agent still extracts JSON textually.
                if response_format is not None and _is_structured_output_rejected(exc):
                    logger.warning(
                        "Provider rejected response_format=%s; retrying without "
                        "structured output. The base agent will parse JSON textually.",
                        response_format,
                    )
                    response_format = None
                    attempt -= 1
                    continue
                logger.warning("LLM call attempt %d/%d failed: %s", attempt, retries, exc)
                if attempt == retries:
                    raise LLMError(f"LLM request failed after {retries} attempts: {exc}") from exc

        raise LLMError("Reached unreachable code path in retry loop")  # pragma: no cover
