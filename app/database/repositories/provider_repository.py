"""Repository for AI provider CRUD with encrypted API key storage."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schema import AIProviderModel
from app.services.encryption import decrypt_api_key, encrypt_api_key


class ProviderRepository:
    """Data-access layer for :class:`AIProviderModel` rows."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        name: str,
        provider: str,
        model: str,
        api_key: str,
        api_base: str | None = None,
        max_tokens: int = 2000,
        temperature: float = 0.1,
        is_active: bool = False,
        is_validated: bool = False,
    ) -> AIProviderModel:
        """Encrypt the API key and persist a new provider configuration."""
        row = AIProviderModel(
            name=name,
            provider=provider,
            model=model,
            api_key_encrypted=encrypt_api_key(api_key),
            api_base=api_base,
            max_tokens=max_tokens,
            temperature=temperature,
            is_active=is_active,
            is_validated=is_validated,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def get(self, provider_id: str) -> AIProviderModel | None:
        """Return a provider row by id, or ``None``."""
        return await self.session.get(AIProviderModel, provider_id)

    async def list_all(self) -> list[AIProviderModel]:
        """Return all provider configurations."""
        stmt = select(AIProviderModel).order_by(AIProviderModel.created_at)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_active(self) -> AIProviderModel | None:
        """Return the single active provider, or ``None``."""
        result = await self.session.execute(
            select(AIProviderModel).where(AIProviderModel.is_active.is_(True))
        )
        return result.scalars().first()

    async def set_active(self, provider_id: str) -> AIProviderModel:
        """Deactivate all providers and activate the given one.

        Args:
            provider_id: The provider to activate.

        Returns:
            The activated provider row.

        Raises:
            ValueError: If the provider does not exist.
        """
        provider = await self.get(provider_id)
        if provider is None:
            raise ValueError(f"Provider {provider_id} not found")

        # Deactivate all
        all_providers = await self.list_all()
        for p in all_providers:
            p.is_active = False
        provider.is_active = True
        await self.session.commit()
        await self.session.refresh(provider)
        return provider

    async def update(
        self,
        provider_id: str,
        *,
        name: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        api_base: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        is_validated: bool | None = None,
    ) -> AIProviderModel:
        """Update fields on an existing provider.

        If ``api_key`` is provided, it is re-encrypted before storage.
        """
        row = await self.get(provider_id)
        if row is None:
            raise ValueError(f"Provider {provider_id} not found")

        if name is not None:
            row.name = name
        if provider is not None:
            row.provider = provider
        if model is not None:
            row.model = model
        if api_key is not None:
            row.api_key_encrypted = encrypt_api_key(api_key)
        if api_base is not None:
            row.api_base = api_base
        if max_tokens is not None:
            row.max_tokens = max_tokens
        if temperature is not None:
            row.temperature = temperature
        if is_validated is not None:
            row.is_validated = is_validated

        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def delete(self, provider_id: str) -> bool:
        """Delete a provider. Returns True if deleted."""
        row = await self.get(provider_id)
        if row is None:
            return False
        await self.session.delete(row)
        await self.session.commit()
        return True

    def decrypt_key(self, row: AIProviderModel) -> str:
        """Decrypt the stored API key for the given provider row."""
        return decrypt_api_key(row.api_key_encrypted)
