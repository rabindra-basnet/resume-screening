"""Database persistence layer.

Provides async SQLAlchemy setup (working with SQLite in development and
PostgreSQL/Neon in production), schema definitions, and repository classes
that encapsulate data access.
"""

from .connection import Database, get_database
from .schema import Base

__all__ = ["Database", "get_database", "Base"]
