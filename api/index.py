"""Vercel serverless entry point for the FastAPI application.

Vercel auto-detects this module as the Python function handler. It imports the
ASGI application and exposes it as the module-level ``app`` object that Vercel
invokes per request. On Vercel the app is mounted under the ``/api`` prefix.
"""

from __future__ import annotations

from app.main import app

# Vercel expects a module-level ASGI application named `app`.
__all__ = ["app"]
