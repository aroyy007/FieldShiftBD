"""Historical exposure metrics, not crop-response or yield predictions."""
import math
from datetime import date, timedelta


def rainfall_window(rows: list[dict], start: date, end: date) -> dict:
    if end < start or (end-start).days > 550:
        raise ValueError('Invalid or unbounded season window')
    rainfall = {}
    for row in rows:
        day = row['date']
        day = date.fromisoformat(day) if isinstance(day, str) else day
        if start <= day <= end:
            if day in rainfall:
                raise ValueError('Duplicate daily observation')
            value = row.get('rainfall_mm')
            rainfall[day] = value if value is not None and math.isfinite(value) and value >= 0 else None
    days = (end-start).days+1
    valid = [v for v in rainfall.values() if v is not None]
    complete = len(valid) == days
    longest = run = 0
    if complete:
        for offset in range(days):
            run = run + 1 if rainfall[start+timedelta(days=offset)] <= 1 else 0
            longest = max(longest, run)
    return {'coverage': len(valid)/days, 'rainfall_mm': sum(valid) if complete else None,
            'longest_dry_spell_days': longest if complete else None, 'observed_days': len(valid), 'expected_days': days}


def calendar_weather_bounds(rows: list[dict], establishment: dict, harvest: dict, *, planning_year: int) -> dict:
    """Historical rainfall on shortest/longest published calendar intervals.

    These are alternative calendar-bound scenarios, not a confidence interval,
    stage model, crop-water requirement, forecast or planting recommendation.
    """
    from statistics import median
    def md(text):
        month,day = map(int,text.split('-'))
        date(2000,month,day)
        return month,day
    es,ee,hs,he = (md(v) for v in (establishment['start'],establishment['end'],harvest['start'],harvest['end']))
    def anchors(year):
        h_end = date(year,*he)
        h_start = date(year-(hs>he),*hs)
        e_end = date(h_start.year,*ee)
        if e_end > h_start:
            e_end = e_end.replace(year=e_end.year-1)
        e_start = date(e_end.year-(es>ee),*es)
        if (h_end-e_start).days > 550 or e_end > h_start:
            raise ValueError('Unsupported calendar interval')
        return e_start,e_end,h_start,h_end
    current=anchors(planning_year)
    normalized=[]
    seen=set()
    for r in rows:
        d = date.fromisoformat(r['date']) if isinstance(r['date'],str) else r['date']
        if d in seen:
            raise ValueError('Duplicate daily observation')
        seen.add(d)
        normalized.append({**r,'date':d})
    years=range(min(seen).year,max(seen).year+1) if seen else []
    short,long,short_dry,long_dry=[],[],[],[]
    for year in years:
        try:
            e_start,e_end,h_start,h_end=anchors(year)
        except ValueError:
            continue
        a=rainfall_window(normalized,e_end,h_start)
        b=rainfall_window(normalized,e_start,h_end)
        if a['rainfall_mm'] is not None and b['rainfall_mm'] is not None:
            short.append(a['rainfall_mm']);long.append(b['rainfall_mm'])
            short_dry.append(a['longest_dry_spell_days']);long_dry.append(b['longest_dry_spell_days'])
    enough=len(short)>=10
    return {'status':'available' if enough else 'insufficient_data',
            'establishment_start':str(current[0]),'establishment_end':str(current[1]),
            'harvest_start':str(current[2]),'harvest_end':str(current[3]),
            'short_interval_median_mm':median(short) if enough else None,
            'long_interval_median_mm':median(long) if enough else None,
            'short_interval_dry_spell_median_days':median(short_dry) if enough else None,
            'long_interval_dry_spell_median_days':median(long_dry) if enough else None,
            'valid_year_count':len(short),'total_year_count':len(years),
            'method_id':'complete_paired_calendar_bounds_rainfall_v1'}
