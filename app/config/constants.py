"""Application-wide constants and hard limits.

Centralizes magic numbers and configuration limits so they are defined once and
referenced throughout the codebase rather than duplicated inline.
"""

from __future__ import annotations

# ===== File upload limits =====
MAX_UPLOAD_MB: int = 10
MAX_UPLOAD_BYTES: int = MAX_UPLOAD_MB * 1024 * 1024
ALLOWED_CONTENT_TYPES: tuple[str, ...] = ("application/pdf",)
ALLOWED_EXTENSIONS: tuple[str, ...] = (".pdf", ".docx")

# ===== Screening / evaluation =====
SKILL_MATCH_THRESHOLD_PERCENT: float = 50.0
EXPERIENCE_TOLERANCE_YEARS: int = 2

# ===== LLM defaults =====
DEFAULT_LLM_MODEL: str = "gpt-4o-mini"
DEFAULT_MAX_TOKENS: int = 2000
DEFAULT_TEMPERATURE: float = 0.1
DEFAULT_TIMEOUT_SECONDS: int = 60
DEFAULT_MAX_RETRIES: int = 3

# ===== Database =====
SQLITE_FILENAME: str = "screening.db"

# ===== API =====
API_V1_PREFIX: str = "/api/v1"
