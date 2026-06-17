"""
SQLAlchemy Declarative Base
All ORM models import from here to share the metadata registry.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Common base class for all SentinelX ORM models."""
    pass
