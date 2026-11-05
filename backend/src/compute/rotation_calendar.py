"""Calendar feasibility; missing dates and turnaround rules remain unknown."""
from datetime import date


def evaluate_calendar(steps: list[dict], minimum_turnaround_days: int | None = None) -> dict:
    if minimum_turnaround_days is not None and minimum_turnaround_days < 0:
        raise ValueError('Turnaround cannot be negative')
    if not steps or any(not isinstance(s.get('start_date'), date) or not isinstance(s.get('end_date'), date) for s in steps):
        return {'status': 'insufficient_dates', 'minimum_buffer_days': None}
    if any(s['end_date'] < s['start_date'] for s in steps):
        return {'status': 'invalid_dates', 'minimum_buffer_days': None}
    gaps = [(b['start_date'] - a['end_date']).days - 1 for a, b in zip(steps, steps[1:])]
    if any(g < 0 for g in gaps):
        return {'status': 'overlap', 'minimum_buffer_days': min(gaps)}
    if gaps and minimum_turnaround_days is None:
        return {'status': 'needs_turnaround_rule', 'minimum_buffer_days': min(gaps)}
    if gaps and min(gaps) < minimum_turnaround_days:
        return {'status': 'insufficient_turnaround', 'minimum_buffer_days': min(gaps)}
    return {'status': 'feasible', 'minimum_buffer_days': min(gaps) if gaps else None}
