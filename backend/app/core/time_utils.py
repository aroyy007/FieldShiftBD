"""Shared datetime normalization helpers for backend services."""

from datetime import datetime, timezone


def to_utc(value: datetime) -> datetime:
    """Return an aware UTC datetime; interpret naive values as UTC."""
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
