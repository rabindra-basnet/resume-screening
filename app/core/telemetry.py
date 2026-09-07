"""Application telemetry: Sentry error tracking and tracing.

Keeps Sentry behind an env gate: if ``SENTRY_DSN`` is empty (default, e.g.
local dev), nothing is initialized and the app logs purely to stdout — which
is free on the hosting platform (Vercel console). When ``SENTRY_DSN`` is set,
the error handler and ``configure_sentry`` attach crashes + (optionally)
performance traces to the project. Genuinely free for small teams on Sentry's
Developer plan (5k errors/mo, 90-day retention) — see https://sentry.io/pricing.

Why Sentry: a standard-library logging handler only ships text lines to a
vendor; it does not capture stack traces, breadcrumbs, or release/commit
context. Sentry's FastAPI integration does all of that out of the box, which
is the high-value piece for an agent-heavy app where exceptions happen inside
long LLM/async chains.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_sentry_initialized = False


def configure_sentry(
    *,
    dsn: str,
    environment: str,
    traces_sample_rate: float = 0.0,
    send_default_pii: bool = False,
) -> bool:
    """Initialize Sentry if a DSN is configured.

    Args:
        dsn: Sentry project DSN. Empty string disables Sentry entirely.
        environment: App environment tag (development/production/...).
        traces_sample_rate: 0.0 disables performance tracing; 1.0 samples all.
        send_default_pii: When True, Sentry may attach the authenticated
            user id/email (from ``request.user``) to events.

    Returns:
        True if Sentry was initialized, False if it was a no-op (no DSN).
    """
    global _sentry_initialized
    if not dsn:
        return False
    if _sentry_initialized:
        return True

    try:
        import sentry_sdk
        from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            traces_sample_rate=traces_sample_rate,
            send_default_pii=send_default_pii,
            integrations=[
                FastApiIntegration(),
                SentryAsgiMiddleware(),
            ],
        )
        _sentry_initialized = True
        logger.info(
            "Sentry error tracking enabled (env=%s, traces=%s)",
            environment,
            traces_sample_rate,
        )
    except Exception:  # pragma: no cover - defensive; never crash the app
        logger.exception("Failed to initialize Sentry")
        return False
    return True