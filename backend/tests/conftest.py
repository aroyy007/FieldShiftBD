"""SQLite compatibility for the PostgreSQL JSONB models used in API tests."""

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles


@compiles(JSONB, "sqlite")
def compile_jsonb_for_sqlite(type_, compiler, **kwargs):
    """Use SQLite's JSON storage when compiling PostgreSQL JSONB in tests."""
    return "JSON"
