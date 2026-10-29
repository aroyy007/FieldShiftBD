from datetime import datetime, timedelta, timezone

from app.core.time_utils import to_utc


def test_to_utc_interprets_naive_datetime_as_utc():
    value = datetime(2026, 10, 29, 12, 30)

    assert to_utc(value) == value.replace(tzinfo=timezone.utc)


def test_to_utc_converts_offset_aware_datetime():
    value = datetime(2026, 10, 29, 18, 30, tzinfo=timezone(timedelta(hours=6)))

    assert to_utc(value) == datetime(2026, 10, 29, 12, 30, tzinfo=timezone.utc)


def test_to_utc_is_idempotent_for_utc_datetime():
    value = datetime(2026, 10, 29, 12, 30, tzinfo=timezone.utc)

    assert to_utc(value) is value
