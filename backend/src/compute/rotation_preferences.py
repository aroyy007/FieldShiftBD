"""Explicit preference ordering; no fabricated utility score for missing evidence."""
import math

# Lower water/rain-exposure is preferable; higher buffer/diversity/income is preferable.
DIRECTIONS = {'water': 1, 'rainfall': 1, 'calendar': -1, 'diversity': -1, 'income': -1}


def compare_options(options: list[dict], priorities: list[str]) -> dict:
    eligible = [o for o in options if o['eligibility'] == 'eligible']
    missing = {'ordering_status': 'insufficient_evidence', 'preferred_option_ids': []}
    if len(eligible) < 2 or not priorities or any(p not in DIRECTIONS for p in priorities):
        return missing
    if any(o['metrics'].get(p) is None or not math.isfinite(o['metrics'][p]) for o in eligible for p in priorities):
        return missing
    def key(o):
        return tuple(o['metrics'][p]*DIRECTIONS[p] for p in priorities)
    # A lexicographic optimum cannot be dominated on the requested dimensions.
    best = min(key(o) for o in eligible)
    ids = sorted(o['option_id'] for o in eligible if key(o) == best)
    return {'ordering_status': 'tied' if len(ids) > 1 else 'ordered', 'preferred_option_ids': ids}
