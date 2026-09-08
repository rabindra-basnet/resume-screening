"""Tests for the LLM client auth handling, env fallback, and live API flow.

The completion tests hit the real OpenCode Zen endpoint directly (no mocks)
so they exercise the genuine :class:`LLMClient`/OpenAI SDK request path against
an actual provider. They are gated on reachability so an offline environment
(CI, no network) skips rather than fails. Pure auth-header construction is
asserted locally (no network needed).
"""

from __future__ import annotations

import os

import pytest
from app.agents.llm_client import PLACEHOLDER_API_KEY, LLMClient
from app.config.settings import LLMProviderConfig, get_settings

# Model used for the live endpoint test; configurable so teams can point it at
# a model their OpenCode tenant actually allows. Defaults to a free content
# model so the test passes against the public free tier.
LIVE_MODEL = os.getenv("LLM_TEST_MODEL", "big-pickle")
LIVE_BASE = os.getenv("LLM_API_BASE", "https://opencode.ai/zen/v1")

# Set LLM_TEST_SKIP_LIVE=1 (or run offline) to skip the live-network test.
_SKIP_LIVE = os.getenv("LLM_TEST_SKIP_LIVE", "") in ("1", "true", "yes")

_live_cfg = LLMProviderConfig(
    llm_model=LIVE_MODEL,
    llm_api_key=PLACEHOLDER_API_KEY,
    llm_api_base=LIVE_BASE,
    llm_max_retries=1,
)


def _built(cfg: LLMProviderConfig):
    """Return the constructed OpenAI client for the given config."""
    return LLMClient(config=cfg)._build_client()


def test_placeholder_key_sends_empty_authorization() -> None:
    """The placeholder key keeps the client constructible but blanks auth."""
    client = _built(
        LLMProviderConfig(
            llm_api_key=PLACEHOLDER_API_KEY,
            llm_api_base="https://example.com/v1",
        )
    )
    assert client.api_key == PLACEHOLDER_API_KEY
    assert client._custom_headers.get("Authorization") == ""
    assert str(client.base_url) == "https://example.com/v1/"


def test_real_key_is_used_as_bearer() -> None:
    """A real key is passed through with no empty-auth override."""
    client = _built(
        LLMProviderConfig(
            llm_api_key="sk-real-secret",
            llm_api_base="https://example.com/v1",
        )
    )
    assert client.api_key == "sk-real-secret"
    assert client._custom_headers.get("Authorization") != ""


def test_zen_client_injects_session_headers() -> None:
    """The OpenCode Zen path adds a session id and attribution headers."""
    client = _built(
        LLMProviderConfig(
            llm_api_key=PLACEHOLDER_API_KEY,
            llm_api_base="https://opencode.ai/zen/v1",
        )
    )
    headers = client._custom_headers
    assert headers.get("x-opencode-client") == "cli"
    assert headers.get("Authorization") == ""
    assert headers.get("x-opencode-session", "").startswith("ses_")


def test_default_client_reads_settings_from_env(monkeypatch) -> None:
    """LLMClient() without a config honours environment LLM_* values."""
    # get_settings() is an lru_cache singleton, so clear it before + after to
    # ensure the injected env vars are actually re-read regardless of the order
    # this test runs relative to other tests.
    get_settings.cache_clear()
    monkeypatch.setenv("LLM_MODEL", "env-model-1")
    monkeypatch.setenv("LLM_API_BASE", "https://env.example.com/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-env-key")
    try:
        client = LLMClient()
        assert client.config.llm_model == "env-model-1"
        assert client.config.llm_api_base == "https://env.example.com/v1"
        assert client.config.llm_api_key == "sk-env-key"
    finally:
        get_settings.cache_clear()


def test_pinned_session_id_from_env(monkeypatch) -> None:
    """OPENCODE_SESSION_ID pins the session used for the Zen gateway."""
    monkeypatch.setenv("OPENCODE_SESSION_ID", "ses_pinned-user-abc")
    client = LLMClient(config=_live_cfg)
    assert client.session_id == "ses_pinned-user-abc"[:64]


@pytest.mark.skipif(_SKIP_LIVE, reason="live API test disabled via LLM_TEST_SKIP_LIVE")
def test_live_complete_content_model() -> None:
    """Real completion returns non-empty text from the live endpoint."""
    client = LLMClient(config=_live_cfg)
    reply = client.complete(
        "You are a resume reviewer.",
        "Reply with exactly: WORKS",
        max_tokens=200,
        temperature=0,
    )
    assert isinstance(reply, str) and reply.strip()
