"""Google OAuth routes for authentication.

Provides ``/auth/login/google`` (redirect to Google) and
``/auth/callback/google`` (exchange code, create/find user, set session).
The callback distinguishes between OAuth provider failures (``400``) and
database persistence failures (``500``) so the caller sees an actionable
error instead of an opaque one.
"""

from __future__ import annotations

import base64
import json
import logging
import urllib.parse
from datetime import UTC, datetime, timedelta
from typing import Any

from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config.settings import get_settings
from app.core.logging import request_id_var
from app.database.repositories.session_repository import SessionRepository
from app.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_oauth: OAuth | None = None


def _public_origin(request: Request) -> str:
    """Return the origin (scheme + host) that should appear in OAuth redirects."""
    forwarded = request.headers.get("x-forwarded-proto", "")
    scheme = forwarded.split(",")[0].strip() if forwarded else request.url.scheme
    host = request.headers.get("host") or request.url.netloc

    # Local development requests (localhost / 127.0.0.1) ALWAYS use local origin
    if "localhost" in host.lower() or "127.0.0.1" in host:
        return f"{scheme}://{host}".rstrip("/")

    configured = get_settings().app_origin.strip().rstrip("/")
    if configured:
        return configured

    return f"{scheme}://{host}".rstrip("/")


def _get_oauth() -> OAuth:
    """Lazy-init the OAuth client (reads settings at call time)."""
    global _oauth  # noqa: PLW0603
    if _oauth is not None:
        return _oauth
    settings = get_settings()
    if not settings.google_client_id:
        raise HTTPException(
            status_code=503,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )
    _oauth = OAuth()
    _oauth.register(
        name="google",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    return _oauth


def _jwt_expiry(id_token: str) -> datetime | None:
    """Read the ``exp`` claim from a Google JWT payload (without re-verifying).

    The JWT signature, audience and issuer are already verified by authlib
    during ``authorize_access_token``; this only decodes the payload to learn
    when Google considers the token expired.

    Args:
        id_token: The raw Google ``id_token`` JWT.

    Returns:
        The token expiry as aware UTC datetime, or ``None`` if unavailable.
    """
    if not id_token:
        return None
    try:
        payload = id_token.split(".")[1]
        payload += "=" * (-len(payload) % 4)  # restore base64 padding
        claims = json.loads(base64.urlsafe_b64decode(payload))
        exp = claims.get("exp")
    except (IndexError, ValueError, json.JSONDecodeError):
        # Malformed tokens are rejected upstream; treat as "no expiry known".
        return None
    if not isinstance(exp, int | float):
        return None
    return datetime.fromtimestamp(exp, tz=UTC)


def _read_userinfo(token: dict[str, Any]) -> dict[str, Any]:
    """Extract normalized Google user info from the token claims.

    Args:
        token: The token dict from ``authorize_access_token``.

    Returns:
        A dict with ``sub``, ``email``, ``name`` and ``picture`` if present.
    """
    userinfo = token.get("userinfo") or {}
    if not userinfo and token.get("id_token"):
        # Fall back to claims embedded in the id_token for older flows.
        claims = token.get("id_token_claims") or {}
        userinfo = claims
    return {
        "google_id": userinfo.get("sub"),
        "email": userinfo.get("email"),
        "name": userinfo.get("name"),
        "picture": userinfo.get("picture"),
    }


@router.get("/login/google")
async def login_google(request: Request) -> RedirectResponse:
    """Redirect the user to Google's OAuth consent screen."""
    oauth = _get_oauth()
    redirect_uri = f"{_public_origin(request)}/api/v1/auth/callback/google"
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/callback/google")
async def callback_google(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """Handle the Google OAuth callback.

    Exchanges the authorization code for tokens, creates or updates the user
    record, and sets a signed session cookie. On success the browser is
    redirected to the account dashboard.

    Raises:
        HTTPException: 400 for OAuth provider errors (e.g. expired/reused
            ``code``), 500 for database failures.
    """
    request_id = request_id_var.get()
    origin = _public_origin(request)
    redirect_uri = f"{origin}/api/v1/auth/callback/google"
    oauth = _get_oauth()

    error_redirect = f"{origin}/login?error="
    state_param = request.query_params.get("state")
    if state_param:
        state_key = f"_state_google_{state_param}"
        if state_key not in request.session:
            request.session[state_key] = {"data": {"state": state_param}}

    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        err = getattr(exc, "error", None) or "oauth_error"
        description = (
            getattr(exc, "error_description", None)
            or getattr(exc, "description", None)
            or "The authorization failed. Please try signing in again."
        )
        logger.warning(
            "Google OAuth token exchange rejected [%s] error=%r description=%r "
            "uri=%r redirect_uri=%r",
            request_id,
            err,
            description,
            getattr(exc, "error_uri", None),
            redirect_uri,
        )
        return RedirectResponse(
            url=f"{error_redirect}{urllib.parse.quote(description)}"
        )
    except Exception:  # pragma: no cover - defensive
        logger.exception(
            "Unexpected error exchanging Google token [%s] redirect_uri=%r",
            request_id,
            redirect_uri,
        )
        return RedirectResponse(
            url=f"{error_redirect}{urllib.parse.quote('Could not reach Google. Please try again.')}"
        )

    info = _read_userinfo(token)
    google_id = info["google_id"]
    email = info["email"]
    if not google_id or not email:
        logger.warning(
            "Google profile missing required fields [%s] google_id=%r email=%r",
            request_id,
            bool(google_id),
            bool(email),
        )
        return RedirectResponse(
            url=(
                f"{error_redirect}"
                f"{urllib.parse.quote('Google did not return a valid profile. Please try again.')}"
            )
        )

    # Persist a server-side session bound to the user and the Google JWT that
    # authlib just verified. Only the opaque session id is sent to the browser.
    settings = get_settings()
    id_token = token.get("id_token") or ""
    try:
        repo = UserRepository(session)
        user = await repo.upsert_from_google(
            email=email,
            name=info["name"] or email or "User",
            google_id=google_id,
            avatar_url=info["picture"],
        )
        auth_session = await SessionRepository(session).create(
            user_id=user.id,
            google_id_token=id_token,
            google_access_token=token.get("access_token"),
            token_expires_at=_jwt_expiry(id_token),
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.session_cookie_max_age),
        )
    except SQLAlchemyError:
        logger.exception(
            "Failed to persist Google user/session [%s] email=%s", request_id, email
        )
        return RedirectResponse(
            url=(
                f"{error_redirect}"
                f"{urllib.parse.quote('Could not save your account. Please try again later.')}"
            )
        )

    logger.info("Authenticated user [%s] email=%s user_id=%s", request_id, email, user.id)
    response = RedirectResponse(url=f"{origin}/screen")
    response.set_cookie(
        key=settings.session_cookie_name,
        value=auth_session.id,
        max_age=settings.session_cookie_max_age,
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
    )
    return response


@router.get("/me")
async def auth_me(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Return the currently authenticated user, or 401."""
    from app.api.deps import _decode_session_user

    user = await _decode_session_user(request, session)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
    }


@router.post("/logout")
async def auth_logout(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> RedirectResponse:
    """Revoke the server-side session and clear the cookie.

    Deleting the ``sessions`` row invalidates the cookie server-side, so a
    stolen session cookie cannot be replayed after logout.

    Args:
        request: The incoming request carrying the session cookie.
        session: The request-scoped async database session.

    Returns:
        A redirect to the landing page with the session cookie cleared.
    """
    settings = get_settings()
    session_id = request.cookies.get(settings.session_cookie_name)
    if session_id:
        try:
            await SessionRepository(session).delete(session_id)
        except SQLAlchemyError:
            logger.exception("Failed to delete session row on logout: %s", session_id)
    response = RedirectResponse(url=_public_origin(request))
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
    )
    return response
