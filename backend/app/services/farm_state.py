from datetime import date, datetime, time, timedelta, timezone


FARM_TIMEZONE = timezone(timedelta(hours=6), "Asia/Dhaka")


def get_task_schedule_state(
    status: str, due_at: datetime | None, as_of: datetime
) -> str:
    """Derive a task's calendar status without persisting a time-sensitive value."""
    if status != "pending":
        return status
    if due_at is None:
        return "unscheduled"

    if due_at.tzinfo is None:
        due_at = due_at.replace(tzinfo=timezone.utc)
    if as_of.tzinfo is None:
        as_of = as_of.replace(tzinfo=timezone.utc)

    if due_at <= as_of:
        return "overdue"

    due_date = due_at.astimezone(FARM_TIMEZONE).date()
    current_date = as_of.astimezone(FARM_TIMEZONE).date()
    if due_date == current_date:
        return "due"
    return "upcoming"


def get_season_progress(
    planting_date: date | None,
    expected_harvest_date: date | None,
    as_of: date,
) -> int | None:
    """Return elapsed calendar progress, clamped to the expected season window."""
    if planting_date is None or expected_harvest_date is None:
        return None
    if expected_harvest_date < planting_date:
        return None
    duration = (expected_harvest_date - planting_date).days
    if duration == 0:
        return 100 if as_of >= expected_harvest_date else 0

    elapsed = (as_of - planting_date).days
    return max(0, min(100, round(elapsed * 100 / duration)))


def schedule_task_due_at(planting_date: date, days_after_planting: int) -> datetime:
    """Set a date-only season-plan action's deadline at that day's end in UTC."""
    if days_after_planting < 0:
        raise ValueError("days_after_planting must be non-negative")

    due_date = planting_date + timedelta(days=days_after_planting)
    local_end_of_day = datetime.combine(due_date, time.max, tzinfo=FARM_TIMEZONE)
    return local_end_of_day.astimezone(timezone.utc)
