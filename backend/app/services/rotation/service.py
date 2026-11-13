"""Source-bounded v2 comparison. Unreviewed patterns never authorize plans."""
from __future__ import annotations
import hashlib
import json
from datetime import date
from pathlib import Path
from statistics import median
from app.contracts.challenge.v1 import FarmProfileSnapshot
from app.contracts.challenge.v2 import (RotationCompareRequest, RotationComparisonV2, RotationOptionV2,
    RotationStepV2, MetricEvidence, EvidenceReference, ExplorationBasisV2, ExplorationEntryV2, UnrankedOptionV2)
from app.services.district_advisory import district_for_input
from app.services.earth_observation.provider import load_power_context
from app.services.earth_observation.registry import product_registry, region_registry
from app.services.rotation_comparison import CATALOG_PATH
from app.services.rotation.calendars import build_calendar_evidence
from app.services.rotation.catalog import load_rotation_candidates
from src.compute.rotation_calendar import evaluate_calendar
from src.compute.rotation_exposure import rainfall_window
from src.compute.rotation_preferences import compare_options
from src.compute.rotation_traits import PRIORITY_METRICS, exploration_order, normalize_crop, sequence_traits

GUIDANCE_PATH = Path(__file__).resolve().parents[2] / 'data/m2_knowledge_sources/rotation_option_guidance.json'
_BN_DIGITS = str.maketrans('0123456789', '০১২৩৪৫৬৭৮৯')


def _bn(value) -> str:
    return str(value).translate(_BN_DIGITS)


def _trait_metrics(trait_steps: list[dict], dry_spells: list[float | None], dated_steps: int) -> list[MetricEvidence]:
    """Comparable, sequence-derived metrics used for the priority-based discussion order."""
    if not trait_steps:
        return [
            _metric('irrigated_dry_season_steps', 'No crop is recorded yet; add the crop you grew last season.', 'কোনো ফসল নথিভুক্ত নেই; গত মৌসুমের ফসল যোগ করুন।'),
            _metric('crop_family_count', 'No crop is recorded yet.', 'কোনো ফসল নথিভুক্ত নেই।'),
            _metric('dry_spell_exposure_days', 'No dated crop interval is recorded.', 'তারিখসহ কোনো ফসলের সময় নথিভুক্ত নেই।'),
            _metric('calendar_coverage_share', 'No crop is recorded yet.', 'কোনো ফসল নথিভুক্ত নেই।'),
            _metric('market_income_evidence', 'No market price or income data is connected yet.', 'বাজারদর বা আয়ের তথ্য এখনও যুক্ত নয়।'),
        ]
    t = sequence_traits(trait_steps)
    n = t['step_count']
    metrics = []
    if t['unknown_water_steps'] == n:
        metrics.append(_metric('irrigated_dry_season_steps', 'Season or crop is not known well enough to classify dry-season irrigation need.',
                               'শুকনো মৌসুমের সেচ চাহিদা বোঝার জন্য ফসল বা মৌসুম যথেষ্ট জানা নেই।'))
    else:
        partial = t['unknown_water_steps'] > 0
        en = (f"{t['irrigated_dry_season_steps']} of {n} crops are dry-season crops that usually need irrigation "
              f"({t['high_water_steps']} Boro rice). General water-use class, not a measured water amount.")
        bn = (f"{_bn(n)}টি ফসলের মধ্যে {_bn(t['irrigated_dry_season_steps'])}টি শুকনো মৌসুমের ফসল যাতে সাধারণত সেচ লাগে "
              f"({_bn(t['high_water_steps'])}টি বোরো ধান)। এটি সাধারণ পানি-ব্যবহারের শ্রেণি, মাপা পানির পরিমাণ নয়।")
        if partial:
            en += f" {t['unknown_water_steps']} crop(s) could not be classified."
            bn += f" {_bn(t['unknown_water_steps'])}টি ফসলের শ্রেণি নির্ধারণ করা যায়নি।"
        metrics.append(MetricEvidence(metric_id='irrigated_dry_season_steps', status='partial' if partial else 'available',
            value=float(t['irrigated_dry_season_steps']), unit='crops per sequence', method_id='general_water_use_class_v1',
            evidence_ids=['fieldshift-crop-traits'], detail_en=en, detail_bn=bn))
    if t['family_count'] == 0:
        metrics.append(_metric('crop_family_count', 'Crop names could not be matched to a plant family.', 'ফসলের নাম কোনো উদ্ভিদ পরিবারের সঙ্গে মেলানো যায়নি।'))
    else:
        legume_en = f" Includes {t['legume_steps']} legume crop(s), which can fix nitrogen." if t['legume_steps'] else ' No legume crop.'
        legume_bn = f" {_bn(t['legume_steps'])}টি শিম জাতীয় ফসল আছে, যা নাইট্রোজেন যোগ করতে পারে।" if t['legume_steps'] else ' কোনো শিম জাতীয় ফসল নেই।'
        metrics.append(MetricEvidence(metric_id='crop_family_count', status='partial' if t['unknown_family_steps'] else 'available',
            value=float(t['family_count']), unit='plant families', method_id='botanical_family_count_v1', evidence_ids=['fieldshift-crop-traits'],
            detail_en=f"{t['family_count']} different plant famil{'y' if t['family_count'] == 1 else 'ies'} in the sequence. More families usually break pest and disease cycles.{legume_en}",
            detail_bn=f"ধারায় {_bn(t['family_count'])}টি ভিন্ন উদ্ভিদ পরিবার। বেশি পরিবার সাধারণত পোকা ও রোগের চক্র ভাঙে।{legume_bn}"))
    known = [d for d in dry_spells if d is not None]
    if not known:
        metrics.append(_metric('dry_spell_exposure_days', 'No dated or calendar-matched crop interval, so NASA POWER dry spells could not be replayed.',
                               'তারিখ বা মেলানো ক্যালেন্ডার নেই, তাই NASA POWER-এর শুকনো দিনের হিসাব করা যায়নি।'))
    else:
        partial = len(known) < n
        en = (f'Longest typical dry spell (days with ≤1 mm rain) during the crops, from 25 years of NASA POWER history: {max(known):.0f} days. '
              'Historical exposure, not a forecast.')
        bn = (f'ফসলের সময়ে সাধারণ দীর্ঘতম শুকনো সময় (দৈনিক ≤১ মিমি বৃষ্টি), NASA POWER-এর ২৫ বছরের ইতিহাস থেকে: {_bn(round(max(known)))} দিন। '
              'ঐতিহাসিক তথ্য, পূর্বাভাস নয়।')
        if partial:
            en += f' Covers {len(known)} of {n} crops.'
            bn += f' {_bn(n)}টির মধ্যে {_bn(len(known))}টি ফসলের হিসাব।'
        metrics.append(MetricEvidence(metric_id='dry_spell_exposure_days', status='partial' if partial else 'available', value=float(max(known)),
            unit='days', method_id='max_step_dry_spell_median_v1', evidence_ids=['power-history'], detail_en=en, detail_bn=bn))
    share = dated_steps / n
    metrics.append(MetricEvidence(metric_id='calendar_coverage_share', status='available', value=round(share, 3), unit='share of crops',
        method_id='sourced_or_recorded_dates_share_v1', evidence_ids=[],
        detail_en=f'{dated_steps} of {n} crops have published or recorded dates.',
        detail_bn=f'{_bn(n)}টি ফসলের মধ্যে {_bn(dated_steps)}টির প্রকাশিত বা নথিভুক্ত তারিখ আছে।'))
    metrics.append(_metric('market_income_evidence', 'No market price or income data is connected yet.', 'বাজারদর বা আয়ের তথ্য এখনও যুক্ত নয়।'))
    return metrics


def _calendar_dry_spells(steps: list[RotationStepV2]) -> tuple[list[float | None], int]:
    spells, dated = [], 0
    for step in steps:
        ev = step.calendar_evidence
        if ev and ev.status == 'source_reference_available':
            dated += 1
        values = [r.weather.long_interval_dry_spell_median_days for r in (ev.references if ev else [])
                  if r.weather and r.weather.status == 'available' and r.weather.long_interval_dry_spell_median_days is not None]
        spells.append(max(values) if values else None)
    return spells, dated


def _gaps(metrics: list[MetricEvidence], lang: str) -> list[str]:
    return [getattr(m, f'detail_{lang}') for m in metrics if m.status == 'missing']


_UNRANKED_TEXT = {
    'outside_documented_conditions': ('Not ordered: your land, soil or irrigation is outside the conditions this example was published for.',
                                      'ক্রমে রাখা হয়নি: আপনার জমি, মাটি বা সেচ এই উদাহরণের প্রকাশিত শর্তের বাইরে।'),
}
_PRIORITY_LABEL = {
    'irrigated_dry_season_steps': ('dry-season irrigation need', 'শুকনো মৌসুমের সেচ চাহিদা'),
    'dry_spell_exposure_days': ('NASA rainfall dry-spell history', 'NASA বৃষ্টির শুকনো সময়ের ইতিহাস'),
    'crop_family_count': ('crop variety', 'ফসলের বৈচিত্র্য'),
    'calendar_coverage_share': ('calendar evidence', 'ক্যালেন্ডারের তথ্য'),
    'market_income_evidence': ('income data', 'আয়ের তথ্য'),
}


def _metric(name, detail_en, detail_bn):
    return MetricEvidence(metric_id=name, status='missing', method_id='review_required', evidence_ids=[], detail_en=detail_en, detail_bn=detail_bn)


def _candidate_calendar_metrics(candidate, planning_year):
    assessment = evaluate_calendar(candidate, planning_year, rules=None)
    if assessment.status == 'overlap':
        calendar_en = 'The sourced date windows overlap. Confirm the exact variety, establishment method, and local dates; no feasible plan is claimed.'
        calendar_bn = 'উৎসের তারিখের সময়সীমা একে অপরের সঙ্গে মিলে যায়। জাত, চাষপদ্ধতি ও স্থানীয় তারিখ নিশ্চিত করুন; উপযোগী পরিকল্পনা দাবি করা হচ্ছে না।'
    elif assessment.status == 'needs_turnaround_rule':
        calendar_en = 'The published date windows do not overlap, but no reviewed turnaround rule or local calendar approval is available.'
        calendar_bn = 'প্রকাশিত তারিখের সময়সীমা মেলে না, তবে পর্যালোচিত মধ্যবর্তী সময়ের নিয়ম বা স্থানীয় ক্যালেন্ডার অনুমোদন নেই।'
    else:
        calendar_en = 'Exact cultivar-specific establishment and harvest windows are missing for one or more steps; no dates were inferred from the published sequence.'
        calendar_bn = 'এক বা একাধিক ধাপের জাতভিত্তিক চাষ শুরু ও ফসল কাটার নির্দিষ্ট সময় নেই; প্রকাশিত ধারার ভিত্তিতে তারিখ অনুমান করা হয়নি।'
    gdd_en = 'No validated cultivar-specific GDD base, cap, target, and stage duration are recorded; thermal feasibility is not scored.'
    gdd_bn = 'জাতভিত্তিক যাচাইকৃত GDD ভিত্তি, সর্বোচ্চ সীমা, লক্ষ্য ও বৃদ্ধির ধাপের সময় নেই; তাপীয় উপযোগিতা স্কোর করা হয়নি।'
    return [
        MetricEvidence(metric_id='calendar', status='missing', method_id='source_scoped_calendar_review_pending',
            evidence_ids=list(candidate.source_ids), detail_en=calendar_en, detail_bn=calendar_bn),
        MetricEvidence(metric_id='gdd', status='missing', method_id='cultivar_gdd_review_required',
            evidence_ids=list(candidate.source_ids), detail_en=gdd_en, detail_bn=gdd_bn),
    ]


def regional_product_state(product_id: str, power_cache_status: str, pilot: dict | None) -> str:
    """Report data availability without implying unreviewed products drive advice."""
    if product_id == 'power':
        return power_cache_status
    if product_id == 'imerg' and pilot is not None:
        return 'pilot_unreviewed'
    if product_id == 'srtm' and pilot is not None and pilot.get('terrain') is not None:
        return 'pilot_unreviewed'
    return 'not_acquired'


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
    candidates = load_rotation_candidates(district, snapshot)
    candidate_by_id = {candidate.candidate_id: candidate for candidate in candidates}
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
    guidance = json.loads(GUIDANCE_PATH.read_text(encoding='utf-8'))
    evidence.append(EvidenceReference(evidence_id='fieldshift-crop-traits', source='FieldShift crop traits (botanical family, general dry-season water-use class)',
        product_id='regional_agronomy', version=guidance['guidance_version'], url='https://github.com/aroyy007/FieldShiftBD/blob/main/backend/app/data/m2_knowledge_sources/rotation_option_guidance.json', role='general_agronomy_pending_review',
        spatial_support='Crop-level general classification; not field-specific', cache_status='bundled_reference', scope='published_agronomy'))
    baseline = candidate_by_id['baseline']
    steps = [RotationStepV2(crop_code=(normalize_crop(s.crop_code) or s.crop_code) if s.event_basis == 'farmer_reported_previous_crop' else s.crop_code,
                            start_date=s.start_date, end_date=s.end_date, event_basis=s.event_basis) for s in baseline.steps]
    base_metrics = [recorded_calendar_metric(steps), *_rainfall_metrics(steps, bundle)]
    base_spells = [next((m.value for m in base_metrics if m.metric_id == f'step_{i+1}_historical_dry_spell_days'), None) for i in range(len(steps))]
    base_metrics += _trait_metrics([{'crop_code': s.crop_code, 'season_code': s.season_code, 'start_date': s.start_date} for s in steps],
                                   base_spells, sum(1 for s in steps if s.start_date and s.end_date))
    previous_only = bool(steps) and all(s.event_basis == 'farmer_reported_previous_crop' for s in steps)
    g = guidance['baseline']
    options = [RotationOptionV2(option_id='baseline', role='baseline', name_en='Your current crops', name_bn='আপনার বর্তমান ফসল',
        steps=steps, eligibility='unknown', metrics=base_metrics,
        reasons_en=['Based only on the previous crop you entered; add dated seasons for a full-year picture.' if previous_only else
                    'History may be incomplete; expected harvest is not a completed harvest. Full annual feasibility has not been established.'],
        reasons_bn=['শুধু আপনার দেওয়া আগের ফসলের ভিত্তিতে; পুরো বছরের চিত্রের জন্য তারিখসহ মৌসুম যোগ করুন।' if previous_only else
                    'ইতিহাস অসম্পূর্ণ হতে পারে; সম্ভাব্য কাটার তারিখ সম্পন্ন ফসল কাটার রেকর্ড নয়। পুরো বছরের উপযোগিতা যাচাই হয়নি।'],
        why_en=g['why_en'], why_bn=g['why_bn'], benefits_en=g['benefits_en'], benefits_bn=g['benefits_bn'],
        risks_en=g['risks_en'], risks_bn=g['risks_bn'],
        gaps_en=(['Add the planting and harvest dates of your recent seasons to compare calendars and NASA rainfall history.',
                  'No market price or income data is connected yet.'] if previous_only else _gaps(base_metrics, 'en')),
        gaps_bn=(['ক্যালেন্ডার ও NASA বৃষ্টির ইতিহাস তুলনা করতে সাম্প্রতিক মৌসুমের রোপণ ও কাটার তারিখ যোগ করুন।',
                  'বাজারদর বা আয়ের তথ্য এখনও যুক্ত নয়।'] if previous_only else _gaps(base_metrics, 'bn')),
        evidence_ids=['power-history', 'fieldshift-crop-traits'] if bundle else ['fieldshift-crop-traits'])]
    for pattern in catalog['patterns']:
        candidate = candidate_by_id[pattern['pattern_id']]
        alt_steps = [RotationStepV2(crop_code=s['crop_code'], season_code=s['season_code'], event_basis='published_sequence_without_reviewed_dates',
                calendar_evidence=build_calendar_evidence(s,request.planning_year,bundle)) for s in pattern['steps']]
        spells, dated = _calendar_dry_spells(alt_steps)
        alt_metrics = [*_candidate_calendar_metrics(candidate, request.planning_year),
                       *_trait_metrics([{'crop_code': s.crop_code, 'season_code': s.season_code, 'start_date': None} for s in alt_steps], spells, dated)]
        g = guidance['patterns'].get(pattern['pattern_id'], {})
        options.append(RotationOptionV2(option_id=pattern['pattern_id'], role='alternative', name_en=pattern['name_en'], name_bn=pattern['name_bn'],
            steps=alt_steps,
            eligibility=candidate.applicability,
            reasons_en=[('Farm conditions conflict with published land/soil/irrigation scope.' if candidate.applicability == 'ineligible' else 'Regional applicability, cultivar dates and agronomist review are required before this example becomes an eligible plan.')],
            reasons_bn=[('জমি, মাটি বা সেচের তথ্য প্রকাশিত শর্তের সঙ্গে মেলে না।' if candidate.applicability == 'ineligible' else 'এই উদাহরণকে পরিকল্পনা হিসেবে নিতে স্থানীয় উপযোগিতা, জাতভিত্তিক তারিখ ও কৃষিবিদের পর্যালোচনা প্রয়োজন।')],
            metrics=alt_metrics,
            why_en=g.get('why_en', []), why_bn=g.get('why_bn', []),
            benefits_en=g.get('benefits_en', []), benefits_bn=g.get('benefits_bn', []),
            risks_en=[*g.get('risks_en', []), 'No measured yield, profit, nitrogen, soil-carbon or irrigation savings are established for your field.'],
            risks_bn=[*g.get('risks_bn', []), 'আপনার জমিতে ফলন, লাভ, নাইট্রোজেন, মাটির কার্বন বা সেচ সাশ্রয়ের পরিমাপ প্রতিষ্ঠিত নয়।'],
            gaps_en=_gaps(alt_metrics, 'en'), gaps_bn=_gaps(alt_metrics, 'bn'),
            evidence_ids=[source['source_id'], 'fieldshift-crop-traits']))
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
    explored = exploration_order([{'option_id': o.option_id, 'eligibility': o.eligibility,
                                   'metrics': {m.metric_id: m.value for m in o.metrics}} for o in options], request.priorities)
    unranked = []
    for item in explored['unranked']:
        reason = item['reason']
        if reason in _UNRANKED_TEXT:
            en, bn = _UNRANKED_TEXT[reason]
        else:
            label_en, label_bn = _PRIORITY_LABEL.get(reason.removeprefix('missing_'), (reason, reason))
            en = f'Not ordered: no {label_en} value for this option yet.'
            bn = f'ক্রমে রাখা হয়নি: এই বিকল্পের {label_bn} এখনও নেই।'
        unranked.append(UnrankedOptionV2(option_id=item['option_id'], reason=reason, detail_en=en, detail_bn=bn))
    first_en, first_bn = _PRIORITY_LABEL[PRIORITY_METRICS[request.priorities[0]][0]]
    exploration = dict(
        exploration_status=explored['status'],
        exploration_order=[ExplorationEntryV2(option_id=e['option_id'], position=e['position'],
            basis=[ExplorationBasisV2(**b) for b in e['basis']]) for e in explored['order']],
        unranked_options=unranked,
        exploration_note_en=f'Options are listed by your priority ({first_en}), using the values shown for each option. '
                            'This is an order for discussion, not a recommendation. Your experience and your local agriculture officer decide.',
        exploration_note_bn=f'আপনার অগ্রাধিকার ({first_bn}) অনুযায়ী, প্রতিটি বিকল্পের দেখানো মান ব্যবহার করে সাজানো হয়েছে। '
                            'এটি আলোচনার জন্য ক্রম, সুপারিশ নয়। সিদ্ধান্ত আপনার অভিজ্ঞতা ও স্থানীয় কৃষি কর্মকর্তার।')
    return RotationComparisonV2(**common, **ordering, **exploration, status='partial', baseline_completeness='incomplete' if steps else 'not_recorded', pilot_observation=pilot,
        options=options, evidence=evidence, release_id=bundle.manifest.bundle_id if bundle else None,
        products=[{'product_id': p.product_id, 'role': p.role,
                   'state': regional_product_state(p.product_id, cache_status, pilot)}
                  for p in product_registry().values()],
        message_en='Compare your recorded sequence with published examples. Reviewed local calendars and water evidence are still needed before choosing a preferred plan.',
        message_bn='আপনার নথিভুক্ত ফসলের সঙ্গে প্রকাশিত উদাহরণ তুলনা করুন। পছন্দের পরিকল্পনা বাছতে পর্যালোচিত স্থানীয় ক্যালেন্ডার ও পানির তথ্য প্রয়োজন।',
        limitations_en=['POWER is area-scale reference-point evidence, not a field measurement or district mean.', 'The optional IMERG pilot sample is not used in the order; other NASA products are not yet incorporated.', 'Your priority changes the discussion order using sequence traits and NASA POWER rainfall history; it never selects a plan for you.'],
        limitations_bn=['POWER নমুনা পয়েন্টের আঞ্চলিক তথ্য; জমির পরিমাপ বা জেলার গড় নয়।', 'IMERG-এর ঐচ্ছিক pilot sample rotation সিদ্ধান্তে ব্যবহার হয় না; অন্য NASA product এখনও যুক্ত হয়নি।', 'আপনার অগ্রাধিকার ফসলের ধারার বৈশিষ্ট্য ও NASA POWER বৃষ্টির ইতিহাস দিয়ে আলোচনার ক্রম বদলায়; এটি আপনার হয়ে পরিকল্পনা বেছে নেয় না।'])
