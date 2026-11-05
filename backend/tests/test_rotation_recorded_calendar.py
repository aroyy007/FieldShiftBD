from datetime import date
from types import SimpleNamespace

from app.contracts.challenge.v2 import RotationStepV2
from app.services.rotation.service import recorded_calendar_metric


def step(start, end, basis='farmer_reported'):
    return RotationStepV2(crop_code='rice', start_date=start, end_date=end, event_basis=basis)


def test_overlapping_recorded_intervals_are_flagged_without_judging_feasibility():
    result = recorded_calendar_metric([
        step(date(2025, 8, 1), date(2025, 11, 30)),
        step(date(2025, 11, 20), date(2026, 2, 10)),
    ])
    assert result.status == 'available'
    assert 'overlap' in result.detail_en.lower()
    assert result.value is None


def test_expected_harvest_cannot_be_treated_as_completed_history():
    result = recorded_calendar_metric([
        step(date(2025, 8, 1), date(2025, 11, 30)),
        step(date(2025, 11, 20), date(2026, 2, 10), 'active_season_expected_harvest'),
    ])
    assert result.status == 'missing'
    assert 'expected' in result.detail_en.lower()


def test_chronology_orders_history_and_keeps_missing_dates_unknown():
    result = recorded_calendar_metric([
        step(date(2025, 12, 10), date(2026, 2, 10)),
        step(date(2025, 8, 1), date(2025, 11, 30)),
    ])
    assert result.status == 'available'
    assert 'no overlap' in result.detail_en.lower()
    assert 'not' in result.detail_en.lower()
    assert recorded_calendar_metric([step(None, date(2025, 11, 30))]).status == 'missing'


def test_completed_season_records_labeled_recorded_plan_are_checked():
    result = recorded_calendar_metric([
        step(date(2025, 8, 1), date(2025, 11, 30), 'recorded_plan'),
        step(date(2025, 11, 20), date(2026, 2, 10), 'recorded_plan'),
    ])
    assert result.status == 'available'
    assert 'overlap' in result.detail_en.lower()


def test_expected_season_is_excluded_but_completed_history_is_checked():
    result = recorded_calendar_metric([
        step(date(2024, 8, 1), date(2024, 11, 30), 'recorded_plan'),
        step(date(2024, 11, 20), date(2025, 2, 10), 'recorded_plan'),
        step(date(2026, 1, 1), date(2026, 5, 1), 'active_season_expected_harvest'),
    ])
    assert result.status == 'partial'
    assert 'overlap' in result.detail_en.lower()
    assert 'expected' in result.detail_en.lower()


def test_historical_rainfall_labels_expected_harvest_as_a_scenario():
    from app.services.rotation.service import _rainfall_metrics
    rows = [SimpleNamespace(model_dump=lambda y=y: {'date': date(y, 1, 1), 'rainfall_mm': 1.0})
            for y in range(2010, 2020)]
    bundle = SimpleNamespace(daily_series=rows, manifest=SimpleNamespace(
        coverage_start=date(2010, 1, 1), coverage_end=date(2019, 12, 31)))
    result = _rainfall_metrics([step(date(2026, 1, 1), date(2026, 1, 1), 'active_season_expected_harvest')], bundle)[0]
    assert result.status == 'available'
    assert 'expected harvest' in result.detail_en.lower()
    assert 'সম্ভাব্য' in result.detail_bn


def test_missing_step_does_not_hide_other_steps_historical_rainfall():
    from app.services.rotation.service import _rainfall_metrics
    rows = [SimpleNamespace(model_dump=lambda y=y: {'date': date(y, 1, 1), 'rainfall_mm': 1.0})
            for y in range(2010, 2020)]
    bundle = SimpleNamespace(daily_series=rows, manifest=SimpleNamespace(
        coverage_start=date(2010, 1, 1), coverage_end=date(2019, 12, 31)))
    result = _rainfall_metrics([
        step(date(2026, 1, 1), date(2026, 1, 1)),
        step(None, date(2026, 6, 1)),
        step(date(2026, 7, 1), date(2026, 6, 1)),
    ], bundle)
    rainfall = [m for m in result if m.metric_id.endswith('historical_rainfall_mm')]
    assert [m.metric_id for m in rainfall] == ['step_1_historical_rainfall_mm', 'step_2_historical_rainfall_mm', 'step_3_historical_rainfall_mm']
    assert [m.status for m in rainfall] == ['available', 'missing', 'missing']
    assert 'date' in rainfall[1].detail_en.lower()
    assert 'date' in rainfall[2].detail_en.lower()


def test_recorded_intervals_show_shortest_between_record_gap_without_claiming_fallow():
    result = recorded_calendar_metric([
        step(date(2025, 12, 10), date(2026, 2, 10)),
        step(date(2025, 8, 1), date(2025, 11, 30)),
    ])
    assert '9 days' in result.detail_en
    assert '৯ দিন' in result.detail_bn
    assert 'fallow' in result.detail_en.lower()


def test_incomplete_record_does_not_hide_overlap_of_complete_records():
    result = recorded_calendar_metric([
        step(date(2025, 8, 1), date(2025, 11, 30)),
        step(date(2025, 11, 20), date(2026, 2, 10)),
        step(None, date(2026, 6, 1)),
    ])
    assert result.status == 'partial'
    assert 'overlap' in result.detail_en.lower()
    assert 'missing' in result.detail_en.lower()


def test_rainfall_with_insufficient_years_explains_no_median():
    from app.services.rotation.service import _rainfall_metrics
    rows = [SimpleNamespace(model_dump=lambda y=y: {'date': date(y, 1, 1), 'rainfall_mm': 1.0})
            for y in range(2010, 2019)]
    bundle = SimpleNamespace(daily_series=rows, manifest=SimpleNamespace(
        coverage_start=date(2010, 1, 1), coverage_end=date(2018, 12, 31)))
    result = _rainfall_metrics([step(date(2026, 1, 1), date(2026, 1, 1))], bundle)[0]
    assert result.status == 'missing'
    assert result.value is None
    assert 'insufficient' in result.detail_en.lower()
    assert '9' in result.detail_en and '10' in result.detail_en


def test_historical_dry_spells_use_complete_years_and_state_threshold():
    from app.services.rotation.service import _rainfall_metrics
    rows = [SimpleNamespace(model_dump=lambda y=y, d=d, mm=mm: {'date': date(y, 1, d), 'rainfall_mm': mm})
            for y in range(2010, 2020) for d, mm in [(1, 0), (2, 1), (3, 4)]]
    bundle = SimpleNamespace(daily_series=rows, manifest=SimpleNamespace(
        coverage_start=date(2010, 1, 1), coverage_end=date(2019, 12, 31)))
    metrics = _rainfall_metrics([step(date(2026, 1, 1), date(2026, 1, 3))], bundle)
    dry = next(m for m in metrics if m.metric_id == 'step_1_historical_dry_spell_days')
    assert dry.value == 2 and dry.valid_year_count == 10
    assert dry.status == 'available' and dry.unit == 'days'
    assert '1 mm' in dry.detail_en and 'forecast' in dry.detail_en.lower()
    assert '১ মিমি' in dry.detail_bn
    bundle.daily_series.pop()
    dry = next(m for m in _rainfall_metrics([step(date(2026, 1, 1), date(2026, 1, 3))], bundle)
               if m.metric_id == 'step_1_historical_dry_spell_days')
    assert dry.status == 'missing' and dry.value is None and dry.valid_year_count == 9


def test_missing_climate_cache_reports_both_step_metrics_unavailable():
    from app.services.rotation.service import _rainfall_metrics
    metrics = _rainfall_metrics([step(date(2026, 1, 1), date(2026, 1, 3))], None)
    assert {m.metric_id for m in metrics} == {'step_1_historical_rainfall_mm', 'step_1_historical_dry_spell_days'}
    assert all(m.status == 'missing' and 'cache' in m.detail_en.lower() for m in metrics)
    assert 'rainfall' in metrics[0].detail_en.lower()
    assert 'spell' in metrics[1].detail_en.lower()
