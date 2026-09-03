"""Tests for Google OAuth flow error handling and success path."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest
from app.api.deps import get_session
from app.api.v1 import auth as auth_mod
from app.database.connection import Database
from app.main import create_app
from authlib.integrations.base_client.errors import OAuthError
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
async def test_oauth_invalid_grant_returns_400(db):
    """A rejected/expired OAuth code maps to a 400 with an actionable message."""
    err = OAuthError(error="invalid_grant", description="Bad Request")
    fake = _fake_oauth_google(side_effect=err)

    async for client in _make_client(db):
        with patch.object(auth_mod, "_get_oauth", return_value=fake):
            response = await client.get(
                "/api/v1/auth/callback/google?state=x&code=spent"
            )
        assert response.status_code == 400
        assert "bad request" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_oauth_db_failure_returns_500(db):
    """A database failure after token exchange maps to a clean 500 JSON error."""
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
                "/api/v1/auth/callback/google?state=x&code=ok"
            )
        assert response.status_code == 500
        assert "could not save" in response.json()["detail"].lower()
