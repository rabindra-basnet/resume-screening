"""Abstract base class for all LLM agents.

Defines a common contract consisting of a system prompt, an execution entry
point, and structured JSON parsing. Concrete agents implement the prompt and
return validated Pydantic models.
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ValidationError

from .llm_client import LLMClient

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class StructuredOutputError(Exception):
    """Raised when the LLM returns output that is not valid structured JSON.

    Args:
        message: Description of the parsing/validation failure.
    """

    def __init__(self, message: str) -> None:
        """Initialize the exception with the given message."""
        super().__init__(message)
        self.message = message


class BaseAgent(Generic[T], ABC):
    """Abstract agent that runs an LLM prompt and parses JSON into a model.

    Args:
        client: The underlying LLM client. Defaults to a new client instance.
    """

    system_prompt: str = "You are a helpful resume screening assistant."
    response_model: type[BaseModel] = BaseModel

    def __init__(self, client: LLMClient | None = None) -> None:
        """Initialize the agent with an optional LLM client."""
        self.client = client or LLMClient()

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> T:
        """Execute the agent task and return a validated Pydantic model.

        Args:
            *args: Positional arguments specific to the agent.
            **kwargs: Keyword arguments specific to the agent.

        Returns:
            An instance of the agent's configured response model.
        """

    def _complete_and_parse(self, user_prompt: str, **overrides: Any) -> T:
        """Send a user prompt and parse the response into the response model.

        Args:
            user_prompt: The prompt content to send to the LLM.
            **overrides: Optional completion overrides (e.g. model, temperature).

        Returns:
            A validated instance of :attr:`response_model`.

        Raises:
            StructuredOutputError: If the response is not valid JSON or fails
                Pydantic validation.
        """
        raw = self.client.complete(self.system_prompt, user_prompt, **overrides)
        return self.parse_response(raw)

    def parse_response(self, raw: str) -> T:
        """Parse a raw LLM JSON string into the configured response model.

        Args:
            raw: The raw JSON string returned by the LLM.

        Returns:
            A validated instance of :attr:`response_model`.

        Raises:
            StructuredOutputError: If the content is not valid JSON or fails
                model validation.
        """
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise StructuredOutputError(f"LLM returned invalid JSON: {raw[:200]!r}") from exc
        try:
            return self.response_model.model_validate(data)  # type: ignore[return-value]
        except ValidationError as exc:
            raise StructuredOutputError(f"LLM JSON failed validation: {exc}") from exc
