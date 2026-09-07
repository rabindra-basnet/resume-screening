"""Tests for Google OAuth flow error handling and success path."""

from __future__ import annotations

import base64
import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from app.api.deps import get_session
from app.api.v1 import auth as auth_mod
from app.database.connection import Database
from app.main import create_app
from authlib.integrations.base_client.errors import OAuthError
from fastapi.responses import RedirectResponse
from sqlalchemy.exc import OperationalError


def _fake_oauth_google(side_effect=None, token=None) -> object:
    """Build a fake ``oauth.google`` object returning ``token`` or raising."""
    google = AsyncMock()
    if side_effect:
        google.authorize_access_token = AsyncMock(side_effect=side_effect)
    else:
        google.authorize_access_token = AsyncMock(return_value=token or {})
    return type("FakeOAuth", (), {"google": google})()


async def _make_client(db: Database):
    app = create_app()
    app.dependency_overrides[get_session] = lambda: db.session()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_oauth_invalid_grant_redirects_to_error(db):
    """A rejected/expired OAuth code redirects to the login page with the error."""
    err = OAuthError(error="invalid_grant", description="Bad Request")
    fake = _fake_oauth_google(side_effect=err)

    async for client in _make_client(db):
        with patch.object(auth_mod, "_get_oauth", return_value=fake):
            response = await client.get(
                "/api/v1/auth/callback/google?state=x&code=spent",
                follow_redirects=False,
            )
        assert response.status_code in (302, 307)
        assert "/login?error=" in response.headers["location"]


@pytest.mark.asyncio
async def test_oauth_db_failure_redirects_to_error(db):
    """A database failure after token exchange redirects to an error page."""
    fake = _fake_oauth_google(
        token={
            "userinfo": {
                "sub": "g-1",
                "email": "u@example.com",
                "name": "User",
            }
        }
    )
    async for client in _make_client(db):
        with (
            patch.object(auth_mod, "_get_oauth", return_value=fake),
            patch.object(
                auth_mod.UserRepository,
                "upsert_from_google",
                side_effect=OperationalError("stmt", {}, Exception("db down")),
            ),
        ):
            response = await client.get(
                "/api/v1/auth/callback/google?state=x&code=ok",
                follow_redirects=False,
            )
        assert response.status_code in (302, 307)
        assert "/login?error=" in response.headers["location"]


@pytest.mark.asyncio
async def test_oauth_success_sets_auth_cookie_that_survives(db):
    """A successful Google callback leaves a working auth cookie.

    Regression test: Starlette's ``SessionMiddleware`` (which carries the OAuth
    ``state`` between the two legs) used the same cookie name as the signed
    auth cookie set by the callback, so the middleware's session-clear response
    header deleted the freshly issued auth cookie and /auth/me stayed 401.
    """

    class FakeGoogle:
        """Model the real authlib flow: persist state, then clear it."""

        async def authorize_redirect(self, request, redirect_uri):
            request.session["_state_google_fake"] = {
                "data": {"redirect_uri": redirect_uri},
                "exp": 2_000_000_000,
            }
            return RedirectResponse(
                "https://accounts.google.com/o/oauth2/auth?state=fake"
            )

        async def authorize_access_token(self, request):
            # authlib's clear_state_data() pops the state key out of the session.
            for key in [
                k for k in list(request.session) if k.startswith("_state_google_")
            ]:
                request.session.pop(key)
            payload = base64.urlsafe_b64encode(
                json.dumps({"exp": 4_102_444_800}).encode()
            ).decode().rstrip("=")
            return {
                "id_token": f"header.{payload}.signature",
                "userinfo": {
                    "sub": "g-1",
                    "email": "u@example.com",
                    "name": "User",
                },
            }

    fake = type("FakeOAuth", (), {"google": FakeGoogle()})()

    async for client in _make_client(db):
        with patch.object(auth_mod, "_get_oauth", return_value=fake):
            # 1) Start the flow: state is persisted into the session cookie.
            start = await client.get(
                "/api/v1/auth/login/google", follow_redirects=False
            )
            assert start.status_code in (302, 307)
            assert start.headers["location"].startswith("https://accounts.google.com")

            # 2) Google redirects back with the code; the callback issues the
            #    auth cookie and clears the one-time OAuth state.
            callback = await client.get(
                "/api/v1/auth/callback/google?state=fake&code=ok",
                follow_redirects=False,
            )
            assert callback.status_code in (302, 307)

            # 3) Exactly one Set-Cookie may target the auth cookie, and it must
            #    be the signed session (not a session-clearing "=null" header).
            #    Historically the OAuth-state middleware shared the cookie name
            #    and emitted a second, overriding header that deleted it.
            auth_sets = [
                value
                for name, value in callback.headers.multi_items()
                if name.lower() == "set-cookie"
                and value.split(";", 1)[0].startswith("aether_session=")
            ]
            assert len(auth_sets) == 1
            assert "=null" not in auth_sets[0]
            assert "expires=" not in auth_sets[0]

            # 4) The auth cookie from step 2 must still authenticate us.
            me = await client.get("/api/v1/auth/me")
            assert me.status_code == 200
            assert me.json()["email"] == "u@example.com"

            # 5) Logout revokes the server-side session: the cookie no longer
            #    authenticates afterwards (no replay possible).
            out = await client.post("/api/v1/auth/logout")
            assert out.status_code in (302, 307)
            gone = await client.get("/api/v1/auth/me")
            assert gone.status_code == 401


def test_jwt_expiry_parser():
    """``_jwt_expiry`` decodes the ``exp`` claim; garbage yields ``None``."""
    payload = (
        base64.urlsafe_b64encode(json.dumps({"exp": 4_102_444_800}).encode())
        .decode()
        .rstrip("=")
    )
    exp = auth_mod._jwt_expiry(f"header.{payload}.signature")
    assert exp is not None
    assert exp.year == 2100
    assert auth_mod._jwt_expiry("") is None
    assert auth_mod._jwt_expiry("not-a-jwt") is None


@pytest.mark.asyncio
async def test_expired_db_session_is_rejected(db):
    """A session row past ``expires_at`` must not authenticate."""
    from datetime import UTC, datetime, timedelta

    from app.config.settings import get_settings
    from app.database.repositories.session_repository import SessionRepository
    from app.database.repositories.user_repository import UserRepository

    async for client in _make_client(db):
        async with db.session() as db_session:
            user = await UserRepository(db_session).create(
                email="expired@example.com", name="Expired", google_id="g-expired"
            )
            auth_session = await SessionRepository(db_session).create(
                user_id=user.id,
                google_id_token="some-jwt",
                expires_at=datetime.now(UTC) - timedelta(seconds=1),
            )
            session_id = auth_session.id

        settings = get_settings()
        me = await client.get(
            "/api/v1/auth/me",
            cookies={settings.session_cookie_name: session_id},
        )
        assert me.status_code == 401
