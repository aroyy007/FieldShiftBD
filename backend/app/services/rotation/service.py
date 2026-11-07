"""Source-bounded v2 comparison. Unreviewed patterns never authorize plans."""
from __future__ import annotations
import hashlib
import json
from datetime import date
from pathlib import Path
from statistics import median
from app.contracts.challenge.v1 import FarmProfileSnapshot
from app.contracts.challenge.v2 import (RotationCompareRequest, RotationComparisonV2, RotationOptionV2,
    RotationStepV2, MetricEvidence, EvidenceReference)
from app.services.district_advisory import district_for_input
from app.services.earth_observation.provider import load_power_context
from app.services.earth_observation.registry import product_registry, region_registry
from app.services.rotation_comparison import CATALOG_PATH
from app.services.rotation.calendars import build_calendar_evidence
from src.compute.rotation_exposure import rainfall_window
from src.compute.rotation_preferences import compare_options


def _metric(name, detail_en, detail_bn):
    return MetricEvidence(metric_id=name, status='missing', method_id='review_required', evidence_ids=[], detail_en=detail_en, detail_bn=detail_bn)


def regional_product_state(product_id: str, power_cache_status: str, pilot: dict | None) -> str:
    """Report data availability without implying unreviewed products drive advice."""
    if product_id == 'power':
        return power_cache_status
    if product_id == 'imerg' and pilot is not None:
        return 'pilot_unreviewed'
    if product_id == 'srtm' and pilot is not None and pilot.get('terrain') is not None:
        return 'pilot_unreviewed'
    return 'not_acquired'


def _baseline(snapshot):
    steps = [RotationStepV2(crop_code=s.crop_code, start_date=s.planting_date, end_date=s.harvest_date, event_basis=s.source)
             for s in reversed(snapshot.rotation_history)]
    if snapshot.active_season:
        s = snapshot.active_season
        steps.append(RotationStepV2(crop_code=s.crop_code or 'unknown', start_date=s.planting_date,
                                    end_date=s.expected_harvest_date, event_basis='active_season_expected_harvest'))
    return steps[-12:]


def recorded_calendar_metric(steps: list[RotationStepV2]) -> MetricEvidence:
    """Check recorded date consistency, never agronomic feasibility."""
    history = [s for s in steps if s.event_basis in ('farmer_reported', 'verified', 'recorded_plan')]
    excluded = len(history) != len(steps)
    recorded = [s for s in history if s.start_date is not None and s.end_date is not None]
    missing_dates = len(recorded) != len(history)
    if len(recorded) < 2:
        if excluded:
            return _metric('recorded_calendar', 'Expected harvest dates are excluded; at least two dated completed records are needed.',
                           'সম্ভাব্য কাটার তারিখ বাদ দেওয়া হয়েছে; অন্তত দুইটি সম্পন্ন ফসলের তারিখ প্রয়োজন।')
        return _metric('recorded_calendar', 'At least two recorded crop intervals with dates are needed to check overlap.',
                       'তারিখের মিল দেখতে অন্তত দুইটি ফসলের শুরু ও শেষের তথ্য প্রয়োজন।')
    ordered = sorted(recorded, key=lambda s: s.start_date)
    if any(s.end_date < s.start_date for s in ordered):
        detail_en = 'A recorded harvest date precedes its planting date; please correct the record.'
        detail_bn = 'নথিতে ফসল কাটার তারিখ শুরুর তারিখের আগে; তথ্য সংশোধন করুন।'
    elif any(b.start_date <= a.end_date for a, b in zip(ordered, ordered[1:])):
        detail_en = 'Recorded crop intervals overlap; check the dates or confirm simultaneous cropping. This does not establish feasibility.'
        detail_bn = 'নথিতে ফসলের সময় একসঙ্গে পড়েছে; তারিখ বা একই সময়ে চাষের তথ্য যাচাই করুন। এতে উপযোগিতা নিশ্চিত হয় না।'
    else:
        shortest = min((b.start_date - a.end_date).days - 1 for a, b in zip(ordered, ordered[1:]))
        bn_days = str(shortest).translate(str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯'))
        detail_en = f'No overlap was found. The shortest gap between recorded intervals is {shortest} days; this is not verified fallow or a required turnaround. History may be incomplete; feasibility is not established.'
        detail_bn = f'নথিতে সময়ের মিল পাওয়া যায়নি। নথিভুক্ত ফসলের মধ্যবর্তী সবচেয়ে কম সময় {bn_days} দিন; এটি যাচাইকৃত পতিত সময় বা প্রয়োজনীয় বিরতি নয়। ইতিহাস অসম্পূর্ণ হতে পারে; উপযোগিতা নিশ্চিত নয়।'
    if excluded:
        detail_en += ' Expected or unconfirmed intervals are excluded.'
        detail_bn += ' সম্ভাব্য বা অনিশ্চিত সময় এই পরীক্ষায় বাদ দেওয়া হয়েছে।'
    if missing_dates:
        detail_en += ' Records with missing dates are excluded.'
        detail_bn += ' যেসব নথিতে তারিখ নেই সেগুলো বাদ দেওয়া হয়েছে।'
    return MetricEvidence(metric_id='recorded_calendar', status='partial' if excluded or missing_dates else 'available', method_id='recorded_interval_check_v1',
                          evidence_ids=[], detail_en=detail_en, detail_bn=detail_bn)


def _rainfall_metrics(steps, bundle):
    if not steps:
        return [_metric('historical_season_rainfall_mm', 'Dated steps and verified climate cache required.', 'তারিখসহ ধাপ ও যাচাইকৃত জলবায়ু ক্যাশ প্রয়োজন।')]
    if not bundle:
        descriptions = (
            ('historical_rainfall_mm', 'Historical rainfall is unavailable because the climate cache is missing or invalid.',
             'জলবায়ু ক্যাশ না থাকায় বা ভুল থাকায় ঐতিহাসিক বৃষ্টির তথ্য পাওয়া যায়নি।'),
            ('historical_dry_spell_days', 'Historical low-rainfall spell is unavailable because the climate cache is missing or invalid.',
             'জলবায়ু ক্যাশ না থাকায় বা ভুল থাকায় ঐতিহাসিক স্বল্পবৃষ্টির ধারার তথ্য পাওয়া যায়নি।'),
        )
        return [_metric(f'step_{index+1}_{metric}', en, bn)
                for index in range(len(steps)) for metric, en, bn in descriptions]
    # Replay each dated crop interval on the historical years, preserving year offsets.
    # This is exposure for the recorded interval, not counterfactual crop response.
    rows = [r.model_dump() for r in bundle.daily_series]
    metrics = []
    for index, step in enumerate(steps):
        if step.start_date is None or step.end_date is None:
            metrics.append(_metric(f'step_{index+1}_historical_rainfall_mm',
                'Start and end dates are needed for this interval.', 'এই সময়ের শুরুর ও শেষের তারিখ প্রয়োজন।'))
            metrics.append(_metric(f'step_{index+1}_historical_dry_spell_days',
                'Start and end dates are needed for the low-rainfall spell.', 'স্বল্পবৃষ্টির ধারাবাহিকতা দেখতে শুরুর ও শেষের তারিখ প্রয়োজন।'))
            continue
        if step.end_date < step.start_date or (step.end_date-step.start_date).days > 550:
            metrics.append(_metric(f'step_{index+1}_historical_rainfall_mm',
                'This interval has invalid dates or exceeds the supported duration; check the dates.',
                'এই সময়ের তারিখ ভুল বা সমর্থিত দৈর্ঘ্যের চেয়ে বেশি; তারিখ যাচাই করুন।'))
            metrics.append(_metric(f'step_{index+1}_historical_dry_spell_days',
                'Invalid dates or unsupported duration prevent this low-rainfall calculation.',
                'ভুল তারিখ বা অসমর্থিত সময়ের জন্য স্বল্পবৃষ্টির হিসাব করা যায়নি।'))
            continue
        totals, dry_spells = [], []
        total = bundle.manifest.coverage_end.year-bundle.manifest.coverage_start.year+1
        for year in range(bundle.manifest.coverage_start.year, bundle.manifest.coverage_end.year+1):
            try:
                start = step.start_date.replace(year=year)
                end = step.end_date.replace(year=year+step.end_date.year-step.start_date.year)
            except ValueError:  # Feb 29 is not silently shifted.
                continue
            result = rainfall_window(rows, start, end)
            if result['rainfall_mm'] is not None:
                totals.append(result['rainfall_mm'])
                dry_spells.append(result['longest_dry_spell_days'])
        available = len(totals) >= 10
        projected = step.event_basis == 'active_season_expected_harvest'
        if not available:
            detail_en = f'Insufficient complete historical data: {len(totals)} years; at least 10 are needed. No median was calculated.'
            detail_bn = f'সম্পূর্ণ ঐতিহাসিক তথ্য অপর্যাপ্ত: {str(len(totals)).translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))} বছর; অন্তত ১০ বছর প্রয়োজন। মধ্যক হিসাব করা হয়নি।'
        else:
            detail_en = ('Historical median for an interval ending at the expected harvest date; not a completed harvest.' if projected else 'Historical median for the recorded calendar interval.') + ' Representative POWER point, not crop water demand.'
            detail_bn = ('সম্ভাব্য কাটার তারিখসহ সময়ের ঐতিহাসিক মধ্যক; ফসল কাটা সম্পন্ন হয়নি।' if projected else 'নথিভুক্ত সময়ের ঐতিহাসিক মধ্যক বৃষ্টি।') + ' POWER নমুনা পয়েন্টের তথ্য, ফসলের পানির চাহিদা নয়।'
        metrics.append(MetricEvidence(metric_id=f'step_{index+1}_historical_rainfall_mm',
            status='available' if available else 'missing', value=median(totals) if available else None,
            unit='mm/dated crop interval', method_id='utc_complete_interval_median_v1',
            evidence_ids=['power-history'], valid_year_count=len(totals), total_year_count=total,
            detail_en=detail_en, detail_bn=detail_bn))
        if available:
            dry_en = 'Median of each historical interval’s longest run with daily rainfall ≤ 1 mm. POWER reference point; not a forecast or irrigation advice.'
            dry_bn = 'ঐতিহাসিক প্রতিটি সময়ে দৈনিক বৃষ্টি সর্বোচ্চ ১ মিমি এমন দীর্ঘতম ধারার মধ্যক। POWER নমুনা পয়েন্ট; এটি পূর্বাভাস বা সেচের পরামর্শ নয়।'
            if projected:
                dry_en += ' Interval ends at the expected harvest, not a completed harvest.'
                dry_bn += ' সময়ের শেষ সম্ভাব্য কাটার তারিখ; ফসল কাটা সম্পন্ন হয়নি।'
        else:
            dry_en = f'Insufficient complete historical data: {len(dry_spells)} years; at least 10 are needed. No low-rainfall median was calculated.'
            dry_bn = f'সম্পূর্ণ ঐতিহাসিক তথ্য অপর্যাপ্ত: {str(len(dry_spells)).translate(str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯"))} বছর; অন্তত ১০ বছর প্রয়োজন। স্বল্পবৃষ্টির মধ্যক হিসাব করা হয়নি।'
        metrics.append(MetricEvidence(metric_id=f'step_{index+1}_historical_dry_spell_days',
            status='available' if available else 'missing', value=median(dry_spells) if available else None,
            unit='days', method_id='complete_interval_longest_daily_le_1mm_median_v1',
            evidence_ids=['power-history'], valid_year_count=len(dry_spells), total_year_count=total,
            detail_en=dry_en, detail_bn=dry_bn))
    return metrics


def compare_rotations(snapshot: FarmProfileSnapshot, request: RotationCompareRequest, climate_root: Path, pilot_root: Path | None = None) -> RotationComparisonV2:
    content = snapshot.model_dump(mode='json', include={'farmland_id', 'farmer_id', 'profile', 'active_season', 'crop_priorities', 'rotation_history'})
    snapshot_hash = hashlib.sha256(json.dumps(content, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    raw_district = snapshot.profile.district_code or snapshot.profile.district
    try:
        district = district_for_input(raw_district).code if raw_district else None
    except ValueError:
        district = None
    common = dict(farmland_id=snapshot.farmland_id, district_code=district, planning_year=request.planning_year,
                  snapshot_hash=snapshot_hash, priorities=request.priorities)
    if district not in region_registry():
        return RotationComparisonV2(**common, status='unsupported_region', baseline_completeness='not_recorded',
            message_en='Regional comparison currently supports Rajshahi and Chattogram. Confirm the field district.',
            message_bn='এই তুলনা বর্তমানে রাজশাহী ও চট্টগ্রামের জন্য। জমির জেলা নিশ্চিত করুন।')
    bundle, cache_status = load_power_context(climate_root, district)
    from app.services.earth_observation.pilot import read_pilot_observation
    pilot = read_pilot_observation(pilot_root, district, snapshot.profile.latitude,
                                   snapshot.profile.longitude) if pilot_root else None
    catalog = json.loads(CATALOG_PATH.read_text())
    source = catalog['source']
    evidence = [EvidenceReference(evidence_id=source['source_id'], source='BRRI published crop patterns',
        product_id='regional_agronomy', version=catalog['catalog_version'], url=source['url'], role='published_examples_pending_review',
        spatial_support=source['source_scope_en'], cache_status='bundled_reference', scope='published_agronomy')]
    if bundle:
        m = bundle.manifest
        p = next(p for p in m.provenance if p.method == 'nasa_power')
        evidence.append(EvidenceReference(evidence_id='power-history', source=p.source_name, product_id='power',
            version=p.dataset_version or 'unknown', url=p.source_url, role='historical_exposure',
            spatial_support=product_registry()['power'].native_support, coverage_start=m.coverage_start,
            coverage_end=m.coverage_end, retrieved_at=p.retrieved_at.isoformat(), cache_status='hit', scope='reference_point'))
    steps = _baseline(snapshot)
    options = [RotationOptionV2(option_id='baseline', role='baseline', name_en='Your recorded sequence', name_bn='আপনার নথিভুক্ত ফসলের ধারা',
        steps=steps, eligibility='unknown', metrics=[recorded_calendar_metric(steps), *_rainfall_metrics(steps, bundle)],
        reasons_en=['History may be incomplete; expected harvest is not a completed harvest. Full annual feasibility has not been established.'],
        reasons_bn=['ইতিহাস অসম্পূর্ণ হতে পারে; সম্ভাব্য কাটার তারিখ সম্পন্ন ফসল কাটার রেকর্ড নয়। পুরো বছরের উপযোগিতা যাচাই হয়নি।'],
        evidence_ids=['power-history'] if bundle else [])]
    scope = catalog['profile_match']
    profile = snapshot.profile
    norm = lambda s: (s or '').casefold().replace('_', ' ').strip()
    mismatch = (profile.irrigation_available is False or
                (profile.land_type is not None and norm(profile.land_type) not in {norm(x) for x in scope['land_types']}) or
                (profile.soil_type is not None and norm(profile.soil_type) not in {norm(x) for x in scope['soil_types']}))
    for pattern in catalog['patterns']:
        options.append(RotationOptionV2(option_id=pattern['pattern_id'], role='alternative', name_en=pattern['name_en'], name_bn=pattern['name_bn'],
            steps=[RotationStepV2(crop_code=s['crop_code'], season_code=s['season_code'], event_basis='published_sequence_without_reviewed_dates',
                calendar_evidence=build_calendar_evidence(s,request.planning_year,bundle)) for s in pattern['steps']],
            eligibility='ineligible' if mismatch else 'unknown',
            reasons_en=[('Farm conditions conflict with published land/soil/irrigation scope.' if mismatch else 'Regional applicability, cultivar dates and agronomist review are required before this example becomes an eligible plan.')],
            reasons_bn=[('জমি, মাটি বা সেচের তথ্য প্রকাশিত শর্তের সঙ্গে মেলে না।' if mismatch else 'এই উদাহরণকে পরিকল্পনা হিসেবে নিতে স্থানীয় উপযোগিতা, জাতভিত্তিক তারিখ ও কৃষিবিদের পর্যালোচনা প্রয়োজন।')],
            metrics=[_metric('calendar', 'Reviewed dated crop calendar and turnaround rule required.', 'পর্যালোচিত তারিখসহ ফসলের ক্যালেন্ডার ও মধ্যবর্তী সময়ের নিয়ম প্রয়োজন।'),
                     _metric('water', 'No reviewed comparable irrigation-demand estimates.', 'তুলনাযোগ্য পর্যালোচিত সেচের চাহিদার তথ্য নেই।')],
            risks_en=['No measured yield, profit, nitrogen, soil-carbon or irrigation savings are established.'],
            risks_bn=['ফলন, লাভ, নাইট্রোজেন, মাটির কার্বন বা সেচ সাশ্রয়ের পরিমাপ প্রতিষ্ঠিত নয়।'], evidence_ids=[source['source_id']]))
    known_evidence = {e.evidence_id for e in evidence}
    for option in options:
        for step in option.steps:
            for ref in step.calendar_evidence.references if step.calendar_evidence else []:
                if ref.source_id not in known_evidence:
                    evidence.append(EvidenceReference(evidence_id=ref.source_id,source=f'BRRI Rice Profile — {ref.variety_name}',
                        product_id='regional_agronomy',version=ref.profile_id,url=ref.source_url,
                        role='published_reference_pending_agronomy_review',spatial_support=ref.scope_en,
                        retrieved_at=ref.accessed_on.isoformat(),cache_status='bundled_reference',scope='published_agronomy'))
                    known_evidence.add(ref.source_id)
    ordering = compare_options([{'option_id': o.option_id, 'eligibility': o.eligibility, 'metrics': {m.metric_id: m.value for m in o.metrics}} for o in options], request.priorities)
    return RotationComparisonV2(**common, **ordering, status='partial', baseline_completeness='incomplete' if steps else 'not_recorded', pilot_observation=pilot,
        options=options, evidence=evidence, release_id=bundle.manifest.bundle_id if bundle else None,
        products=[{'product_id': p.product_id, 'role': p.role,
                   'state': regional_product_state(p.product_id, cache_status, pilot)}
                  for p in product_registry().values()],
        message_en='Compare your recorded sequence with published examples. Reviewed local calendars and water evidence are still needed before choosing a preferred plan.',
        message_bn='আপনার নথিভুক্ত ফসলের সঙ্গে প্রকাশিত উদাহরণ তুলনা করুন। পছন্দের পরিকল্পনা বাছতে পর্যালোচিত স্থানীয় ক্যালেন্ডার ও পানির তথ্য প্রয়োজন।',
        limitations_en=['POWER is area-scale reference-point evidence, not a field measurement or district mean.', 'The optional IMERG pilot sample is separate from rotation scoring; other NASA products are not yet incorporated.', 'Farmer priorities are recorded; missing comparison evidence prevents a preferred-option claim.'],
        limitations_bn=['POWER নমুনা পয়েন্টের আঞ্চলিক তথ্য; জমির পরিমাপ বা জেলার গড় নয়।', 'IMERG-এর ঐচ্ছিক pilot sample rotation সিদ্ধান্তে ব্যবহার হয় না; অন্য NASA product এখনও যুক্ত হয়নি।', 'আপনার অগ্রাধিকার রাখা হয়েছে; তুলনার তথ্য অসম্পূর্ণ বলে সেরা বিকল্প দাবি করা হয়নি।'])
