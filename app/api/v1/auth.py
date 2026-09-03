"""Google OAuth routes for authentication.

Provides ``/auth/login/google`` (redirect to Google) and
``/auth/callback/google`` (exchange code, create/find user, set session).
The callback distinguishes between OAuth provider failures (``400``) and
database persistence failures (``500``) so the caller sees an actionable
error instead of an opaque one.
"""

from __future__ import annotations

import logging
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
from app.database.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

_oauth: OAuth | None = None


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
    origin = get_settings().app_origin
    redirect_uri = f"{origin}/api/v1/auth/callback/google"
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
    origin = get_settings().app_origin
    oauth = _get_oauth()

    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as exc:
        logger.warning(
            "Google OAuth token exchange rejected [%s] error=%r description=%r uri=%r",
            request_id,
            getattr(exc, "error", None),
            getattr(exc, "error_description", None) or getattr(exc, "description", None),
            getattr(exc, "error_uri", None),
        )
        description = (
            getattr(exc, "error_description", None)
            or getattr(exc, "description", None)
            or (
                "The authorization code is invalid or was already used. "
                "Please sign in again."
            )
        )
        raise HTTPException(
            status_code=400,
            detail=(
                f"Google authentication failed: {description}"
            ),
        ) from None
    except Exception as exc:  # pragma: no cover - defensive
        logger.exception("Unexpected error exchanging Google token [%s]", request_id)
        raise HTTPException(
            status_code=502,
            detail="Could not reach Google OAuth. Please try again.",
        ) from exc

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
        raise HTTPException(
            status_code=400,
            detail="Google profile missing required fields.",
        )

    try:
        repo = UserRepository(session)
        user = await repo.upsert_from_google(
            email=email,
            name=info["name"] or email or "User",
            google_id=google_id,
            avatar_url=info["picture"],
        )
    except SQLAlchemyError as exc:
        logger.exception(
            "Failed to persist Google user [%s] email=%s", request_id, email
        )
        raise HTTPException(
            status_code=500,
            detail="Could not save user account. Please try again later.",
        ) from exc

    from itsdangerous import URLSafeTimedSerializer

    settings = get_settings()
    signer = URLSafeTimedSerializer(settings.session_secret)
    session_token = signer.dumps({"user_id": user.id})

    logger.info("Authenticated user [%s] email=%s user_id=%s", request_id, email, user.id)
    response = RedirectResponse(url=f"{origin}/account")
    response.set_cookie(
        key=settings.session_cookie_name,
        value=session_token,
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
async def auth_logout(request: Request) -> RedirectResponse:
    """Clear the session cookie and redirect to the landing page."""
    settings = get_settings()
    response = RedirectResponse(url=settings.app_origin)
    response.delete_cookie(
        key=settings.session_cookie_name,
        httponly=True,
        samesite="lax",
        secure=settings.app_env == "production",
    )
    return response
