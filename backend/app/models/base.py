"""Shared SQLAlchemy declarative base.

All ORM models across every module inherit from this single ``Base`` so that
Alembic's ``--autogenerate`` sees one unified ``MetaData``. Keeping it in its
own module (rather than inside any one module's model file) avoids import
cycles and matches the folder layout described in ``backend/guide.md``.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Project-wide declarative base for all ORM models."""

    pass
