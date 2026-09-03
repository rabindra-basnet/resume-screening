"""Fernet-based symmetric encryption for API key storage.

Uses a key derived from the ``ENCRYPTION_KEY`` environment variable.  The key
must be a URL-safe base64-encoded 32-byte Fernet key.  A new key is generated
on first run when none is configured (development convenience only — the key
is written to ``.env.local`` for persistence).
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

_ENV_KEY_NAME = "ENCRYPTION_KEY"
_LOCAL_ENV = Path(".env.local")

_fernet: Fernet | None = None


def _load_or_create_key() -> str:
    """Return the encryption key, generating one if missing."""
    key = os.getenv(_ENV_KEY_NAME)
    if key:
        return key

    key = Fernet.generate_key().decode()

    # Persist for subsequent runs (dev only — production should set the env var).
    lines: list[str] = []
    if _LOCAL_ENV.exists():
        lines = _LOCAL_ENV.read_text().splitlines()
    lines.append(f"{_ENV_KEY_NAME}={key}")
    _LOCAL_ENV.write_text("\n".join(lines) + "\n")
    logger.warning("Generated new encryption key and wrote it to %s", _LOCAL_ENV)
    return key


def get_fernet() -> Fernet:
    """Return a cached :class:`Fernet` instance."""
    global _fernet  # noqa: PLW0603
    if _fernet is None:
        _fernet = Fernet(_load_or_create_key())
    return _fernet


def encrypt_api_key(plaintext: str) -> str:
    """Encrypt a plaintext API key and return the token string."""
    return get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_api_key(token: str) -> str:
    """Decrypt an encrypted token back to the plaintext API key."""
    return get_fernet().decrypt(token.encode()).decode()


def validate_api_key_format(token: str) -> bool:
    """Return True if the token looks like a valid Fernet ciphertext."""
    try:
        return token.startswith("gAAAAA")
    except Exception:  # noqa: BLE001
        return False
