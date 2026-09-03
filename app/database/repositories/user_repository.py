"""Repository for persisting and retrieving user accounts."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schema import UserModel


class UserRepository:
    """Data access for :class:`UserModel` rows.

    Args:
        session: An async SQLAlchemy session to operate on.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_google_id(self, google_id: str) -> UserModel | None:
        """Fetch a user by their Google OAuth subject ID."""
        stmt = select(UserModel).where(UserModel.google_id == google_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> UserModel | None:
        """Fetch a user by email address."""
        stmt = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get(self, user_id: str) -> UserModel | None:
        """Fetch a user by primary key."""
        return await self.session.get(UserModel, user_id)

    async def create(
        self,
        *,
        email: str,
        name: str,
        google_id: str,
        avatar_url: str | None = None,
    ) -> UserModel:
        """Create a new user account.

        Args:
            email: User email from Google profile.
            name: Display name from Google profile.
            google_id: Google OAuth subject ID.
            avatar_url: Optional profile picture URL.

        Returns:
            The persisted :class:`UserModel`.
        """
        row = UserModel(
            email=email,
            name=name,
            google_id=google_id,
            avatar_url=avatar_url,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def upsert_from_google(
        self,
        *,
        email: str,
        name: str,
        google_id: str,
        avatar_url: str | None = None,
    ) -> UserModel:
        """Find an existing user by Google ID or create a new one.

        Args:
            email: User email from Google profile.
            name: Display name from Google profile.
            google_id: Google OAuth subject ID.
            avatar_url: Optional profile picture URL.

        Returns:
            The existing or newly created :class:`UserModel`.
        """
        existing = await self.get_by_google_id(google_id)
        if existing is not None:
            existing.email = email
            existing.name = name
            existing.avatar_url = avatar_url
            await self.session.commit()
            await self.session.refresh(existing)
            return existing
        return await self.create(
            email=email,
            name=name,
            google_id=google_id,
            avatar_url=avatar_url,
        )
