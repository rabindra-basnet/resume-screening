"""Configuration and environment settings for the resume screening application.

This package centralizes all environment-variable driven configuration using
Pydantic's settings management, ensuring type safety and startup-time
validation of required values.
"""

from .settings import LLMProviderConfig, Settings

__all__ = ["Settings", "LLMProviderConfig"]
