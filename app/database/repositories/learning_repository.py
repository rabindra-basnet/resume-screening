"""Repository for persisting and retrieving learning resources."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.schema import LearningResourceModel
from app.models.learning import LearningResource

logger = logging.getLogger(__name__)


class LearningRepository:
    """Data access for :class:`LearningResourceModel` rows.

    Args:
        session: An async SQLAlchemy session to operate on.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async session."""
        self.session = session

    async def create(self, resource: LearningResource) -> LearningResourceModel:
        """Persist a new learning resource.

        Args:
            resource: The learning resource to store.

        Returns:
            The persisted :class:`LearningResourceModel`.
        """
        row = LearningResourceModel(
            screening_id=resource.screening_id,
            skill=resource.skill,
            title=resource.title,
            url=resource.url,
            resource_type=resource.resource_type,
            provider=resource.provider,
            description=resource.description,
            estimated_hours=resource.estimated_hours,
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)
        return row

    async def create_many(
        self, resources: list[LearningResource]
    ) -> list[LearningResourceModel]:
        """Persist multiple learning resources in a single transaction.

        Args:
            resources: The learning resources to store.

        Returns:
            The list of persisted :class:`LearningResourceModel` rows.
        """
        rows: list[LearningResourceModel] = []
        for resource in resources:
            row = LearningResourceModel(
                screening_id=resource.screening_id,
                skill=resource.skill,
                title=resource.title,
                url=resource.url,
                resource_type=resource.resource_type,
                provider=resource.provider,
                description=resource.description,
                estimated_hours=resource.estimated_hours,
            )
            self.session.add(row)
            rows.append(row)
        await self.session.commit()
        for row in rows:
            await self.session.refresh(row)
        return rows

    async def list_by_screening(
        self, screening_id: str
    ) -> list[LearningResourceModel]:
        """Return all learning resources for a given screening.

        Args:
            screening_id: The screening result id.

        Returns:
            A list of learning resource rows for the screening.
        """
        stmt = (
            select(LearningResourceModel)
            .where(LearningResourceModel.screening_id == screening_id)
            .order_by(LearningResourceModel.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, limit: int = 100) -> list[LearningResourceModel]:
        """Return the most recent learning resources across all screenings.

        Args:
            limit: Maximum number of rows to return.

        Returns:
            A list of learning resource rows, newest first.
        """
        stmt = (
            select(LearningResourceModel)
            .order_by(LearningResourceModel.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
