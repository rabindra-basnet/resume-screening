"""Google OAuth routes for authentication.

Provides ``/auth/login/google`` (redirect to Google) and
``/auth/callback/google`` (exchange code, create/find user, set session).
"""

from __future__ import annotations

import logging

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.config.settings import get_settings
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

    Exchanges the authorization code for tokens, fetches user info,
    creates or updates the user record, and sets a signed session cookie.
    """
    try:
        oauth = _get_oauth()
        token = await oauth.google.authorize_access_token(request)
    except Exception:
        logger.exception("Google OAuth token exchange failed")
        raise HTTPException(status_code=401, detail="Google authentication failed") from None

    userinfo = token.get("userinfo") or {}
    google_id = userinfo.get("sub")
    email = userinfo.get("email")
    name = userinfo.get("name") or email or "User"
    avatar = userinfo.get("picture")

    if not google_id or not email:
        raise HTTPException(status_code=401, detail="Google profile missing required fields")

    repo = UserRepository(session)
    user = await repo.upsert_from_google(
        email=email,
        name=name,
        google_id=google_id,
        avatar_url=avatar,
    )

    from itsdangerous import URLSafeTimedSerializer

    settings = get_settings()
    signer = URLSafeTimedSerializer(settings.session_secret)
    session_token = signer.dumps({"user_id": user.id})

    origin = settings.app_origin
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
