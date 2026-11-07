"""Deterministic date-window checks; absence of reviewed rules stays unknown."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.services.rotation.catalog import RotationCandidate, ReviewedRuleSet


@dataclass(frozen=True)
class CalendarWindowResult:
    crop_code: str
    start_date: date
    end_date: date
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class CalendarFeasibility:
    status: str
    windows: tuple[CalendarWindowResult, ...] = ()
    minimum_buffer_days: int | None = None
    evidence_ids: tuple[str, ...] = ()
    gdd_summary: None = None
    reason: str = ""


def _window_dates(candidate_step, year: int) -> tuple[date, date] | None:
    if candidate_step.start_date is not None or candidate_step.end_date is not None:
        if candidate_step.start_date is None or candidate_step.end_date is None:
            return None
        return candidate_step.start_date, candidate_step.end_date
    window = candidate_step.window
    if window is None or not candidate_step.source_ids:
        return None
    try:
        month, day = (int(value) for value in window.start.split("-"))
        end_month, end_day = (int(value) for value in window.end.split("-"))
        start = date(year, month, day)
        end_year = year + (1 if (end_month, end_day) < (month, day) else 0)
        end = date(end_year, end_month, end_day)
    except (TypeError, ValueError):
        return None
    return start, end


def evaluate_calendar(
    candidate: RotationCandidate,
    planning_year: int,
    rules: ReviewedRuleSet | None,
) -> CalendarFeasibility:
    """Check sourced date windows for overlap and only apply a reviewed gap rule.

    This is calendar consistency only. GDD, yield and other crop-response
    metrics are deliberately not inferred here.
    """
    if not 1900 <= planning_year <= 9997:
        raise ValueError("planning_year must be between 1900 and 9997")
    if not candidate.steps:
        return CalendarFeasibility("insufficient_dates", reason="No dated crop steps are available.")

    windows: list[CalendarWindowResult] = []
    for step in candidate.steps:
        dates = _window_dates(step, planning_year)
        if dates is None:
            return CalendarFeasibility(
                "insufficient_dates", windows=tuple(windows),
                evidence_ids=tuple(dict.fromkeys(source for item in candidate.steps for source in item.source_ids)),
                reason="Every step needs a complete date interval and source reference.",
            )
        start, end = dates
        if end < start:
            return CalendarFeasibility("invalid_dates", windows=tuple(windows), reason="A crop interval ends before it starts.")

        # Month/day windows repeat each season. Place each subsequent sequence
        # step in the next occurrence only when its first date has already passed.
        if step.window is not None and windows:
            # Sequence order chooses the next occurrence of the season's
            # start window. Overlap is evaluated afterwards; shifting against
            # the prior harvest would hide genuinely incompatible durations.
            while start <= windows[-1].start_date:
                try:
                    start = start.replace(year=start.year + 1)
                    end = end.replace(year=end.year + 1)
                except ValueError:
                    return CalendarFeasibility("insufficient_dates", windows=tuple(windows), reason="A leap-day window cannot be aligned to this planning year.")
        windows.append(CalendarWindowResult(step.crop_code, start, end, step.source_ids))

    gaps = [(right.start_date - left.end_date).days - 1 for left, right in zip(windows, windows[1:])]
    evidence_ids = tuple(dict.fromkeys(
        [source for window in windows for source in window.source_ids]
        + (list(rules.source_ids) if rules else [])
    ))
    if any(gap < 0 for gap in gaps):
        return CalendarFeasibility("overlap", tuple(windows), min(gaps), evidence_ids,
            reason="Sourced date intervals overlap; confirm the crop dates and sequence.")
    minimum_buffer = min(gaps) if gaps else None
    if gaps:
        if rules is None or rules.review_status != "reviewed" or not rules.source_ids:
            return CalendarFeasibility("needs_turnaround_rule", tuple(windows), minimum_buffer,
                evidence_ids, reason="A source-backed reviewed turnaround requirement is not available.")
        if minimum_buffer < rules.minimum_turnaround_days:
            return CalendarFeasibility("insufficient_turnaround", tuple(windows), minimum_buffer,
                evidence_ids, reason="The available gap is shorter than the reviewed turnaround rule.")
    return CalendarFeasibility("feasible", tuple(windows), minimum_buffer, evidence_ids,
        reason="Date windows satisfy the sourced interval and reviewed turnaround checks.")
