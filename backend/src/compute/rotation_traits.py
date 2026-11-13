"""Sequence-derived rotation characteristics and a transparent exploration order.

Everything here is computed from the crop sequence itself (crop family, season,
general water-use class) or from historical NASA POWER rainfall replayed on the
published calendars. None of it is a measured yield, soil, profit or water
outcome. The order is lexicographic on the farmer's chosen priorities, so a
person can reproduce it by hand from the listed values.
"""
from __future__ import annotations

import math
import re
from datetime import date

# Botanical families (fact). Unknown crops are reported as unknown, never guessed.
CROP_FAMILY = {
    'rice': 'Poaceae', 'wheat': 'Poaceae', 'maize': 'Poaceae', 'sugarcane': 'Poaceae',
    'chickpea': 'Fabaceae', 'lentil': 'Fabaceae', 'mungbean': 'Fabaceae', 'blackgram': 'Fabaceae',
    'grasspea': 'Fabaceae', 'sesbania_rostrata': 'Fabaceae', 'soybean': 'Fabaceae', 'groundnut': 'Fabaceae',
    'potato': 'Solanaceae', 'tomato': 'Solanaceae', 'brinjal': 'Solanaceae',
    'mustard': 'Brassicaceae', 'jute': 'Malvaceae', 'onion': 'Amaryllidaceae', 'garlic': 'Amaryllidaceae',
}
LEGUMES = {crop for crop, family in CROP_FAMILY.items() if family == 'Fabaceae'}

# General dry-season irrigation class (general agronomy, pending local review).
# 'high': Boro rice (dry-season irrigated rice); 'moderate': irrigated rabi field crops;
# 'low': pulses/oilseeds on residual moisture, monsoon or green-manure crops.
_MODERATE_RABI = {'wheat', 'maize', 'potato', 'onion', 'garlic', 'tomato', 'brinjal'}
_LOW = {'chickpea', 'lentil', 'grasspea', 'mustard', 'sesbania_rostrata', 'mungbean', 'blackgram', 'jute'}

ALIASES = {
    'paddy': 'rice', 'dhan': 'rice', 'boro': 'rice', 'aman': 'rice', 'aus': 'rice', 'chola': 'chickpea',
    'gram': 'chickpea', 'masur': 'lentil', 'musur': 'lentil', 'sorisha': 'mustard', 'alu': 'potato',
    'gom': 'wheat', 'bhutta': 'maize', 'corn': 'maize', 'pat': 'jute', 'dhaincha': 'sesbania_rostrata',
    'sesbania': 'sesbania_rostrata', 'khesari': 'grasspea', 'mung': 'mungbean',
}


def normalize_crop(value: str | None) -> str | None:
    """Map free-text crop names to a catalog code; return None when not recognizable."""
    if not value:
        return None
    key = re.sub(r'[^a-z_ ]', '', value.casefold()).strip().replace(' ', '_')
    for word in [key, *key.split('_')]:
        if word in CROP_FAMILY:
            return word
        if word in ALIASES:
            return ALIASES[word]
    return key or None


def season_from_date(start: date | None) -> str | None:
    """Bangladesh rice/field seasons by planting month (Boro Nov–Feb, Aus Mar–May, Aman Jun–Sep, Rabi Oct)."""
    if start is None:
        return None
    m = start.month
    return 'boro' if m in (11, 12, 1, 2) else 'aus' if m in (3, 4, 5) else 'aman' if m in (6, 7, 8, 9) else 'rabi'


def water_class(crop: str | None, season: str | None) -> str | None:
    if crop is None:
        return None
    if crop == 'rice':
        if season == 'boro':
            return 'high'
        if season in ('aus', 'aman'):
            return 'low'
        return None  # rice with unknown season: class cannot be assigned
    if crop in _MODERATE_RABI:
        return 'moderate'
    if crop in _LOW:
        return 'low'
    return None


def sequence_traits(steps: list[dict]) -> dict:
    """steps: [{'crop_code', 'season_code', 'start_date'}] -> trait values and notes."""
    crops = [normalize_crop(s.get('crop_code')) for s in steps]
    seasons = [s.get('season_code') or season_from_date(s.get('start_date')) for s in steps]
    families = [CROP_FAMILY.get(c) if c else None for c in crops]
    classes = [water_class(c, s) for c, s in zip(crops, seasons)]
    known_families = {f for f in families if f}
    return {
        'step_count': len(steps),
        'crops': crops,
        'seasons': seasons,
        'families': families,
        'family_count': len(known_families),
        'unknown_family_steps': sum(1 for f in families if f is None),
        'legume_steps': sum(1 for c in crops if c in LEGUMES),
        'non_rice_steps': sum(1 for c in crops if c and c != 'rice'),
        'water_classes': classes,
        'irrigated_dry_season_steps': sum(1 for k in classes if k in ('high', 'moderate')),
        'high_water_steps': sum(1 for k in classes if k == 'high'),
        'unknown_water_steps': sum(1 for k in classes if k is None),
    }


# Priority -> (metric_id, direction). direction -1 means a higher value comes first.
PRIORITY_METRICS = {
    'water': ('irrigated_dry_season_steps', 1),
    'rainfall': ('dry_spell_exposure_days', 1),
    'diversity': ('crop_family_count', -1),
    'calendar': ('calendar_coverage_share', -1),
    'income': ('market_income_evidence', -1),
}


def exploration_order(options: list[dict], priorities: list[str]) -> dict:
    """Order options for discussion by the farmer's priorities.

    options: [{'option_id', 'eligibility', 'metrics': {metric_id: value|None}}]
    Options outside documented conditions, or missing the first priority's value,
    are listed as unranked with a reason instead of being given an invented score.
    """
    ranked, unranked = [], []
    first_metric = PRIORITY_METRICS[priorities[0]][0] if priorities else None
    for o in options:
        if o['eligibility'] == 'ineligible':
            unranked.append({'option_id': o['option_id'], 'reason': 'outside_documented_conditions'})
            continue
        v = o['metrics'].get(first_metric) if first_metric else None
        if v is None or not math.isfinite(v):
            unranked.append({'option_id': o['option_id'], 'reason': f'missing_{first_metric}'})
            continue
        ranked.append(o)

    def key(o):
        parts = []
        for p in priorities:
            metric, direction = PRIORITY_METRICS[p]
            v = o['metrics'].get(metric)
            # A missing secondary value sorts after known values on that criterion.
            parts.append((1, 0.0) if v is None or not math.isfinite(v) else (0, v * direction))
        return tuple(parts)

    ranked.sort(key=lambda o: (key(o), o['option_id']))
    order, position, previous = [], 0, None
    for index, o in enumerate(ranked):
        k = key(o)
        if k != previous:
            position = index + 1
            previous = k
        basis = [{'priority': p, 'metric_id': PRIORITY_METRICS[p][0], 'value': o['metrics'].get(PRIORITY_METRICS[p][0])}
                 for p in priorities]
        order.append({'option_id': o['option_id'], 'position': position, 'basis': basis})
    positions = [e['position'] for e in order]
    status = ('insufficient_evidence' if len(order) < 2 else
              'tied' if len(set(positions)) == 1 else 'ordered')
    return {'status': status, 'order': order, 'unranked': unranked}
