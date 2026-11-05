from datetime import date,timedelta
import pytest


def test_wet_seeded_rice_never_receives_transplanted_calendar():
    from app.services.rotation.calendars import match_calendar_references
    result=match_calendar_references({'crop_code':'rice','season_code':'aman','cultivation_method':'wet_seeded','variety_names':['BRRI dhan33']})
    assert result['status']=='method_mismatch'
    assert result['matching']==[]


def test_unspecified_method_does_not_silently_select_transplanted_boro():
    from app.services.rotation.calendars import match_calendar_references
    result=match_calendar_references({'crop_code':'rice','season_code':'boro','cultivation_method':'unspecified','variety_names':['BR14']})
    assert result['status']=='method_not_recorded'
    assert result['matching']==[]
    assert result['available'][0]['profile_id']=='bd-rice-br14-boro-reference-v1'


def test_calendar_weather_preserves_date_range_and_cross_year_anchor():
    from src.compute.rotation_exposure import calendar_weather_bounds
    rows=[]
    for y in range(2001,2012):
        for i in range((date(y+1,1,1)-date(y,1,1)).days):
            rows.append({'date':date(y,1,1)+timedelta(days=i),'rainfall_mm':1.0})
    # BRRI dhan31 source window: Jul23–Aug14 establishment; Nov9–Nov24 harvest.
    result=calendar_weather_bounds(rows,{'start':'07-23','end':'08-14'},{'start':'11-09','end':'11-24'},planning_year=2027)
    assert result['short_interval_median_mm']==88
    assert result['long_interval_median_mm']==125
    assert result['short_interval_dry_spell_median_days']==88
    assert result['long_interval_dry_spell_median_days']==125
    assert result['valid_year_count']==11
    assert result['establishment_start']=='2027-07-23'
    # BR14 winter establishment spans the year before its April harvest.
    boro=calendar_weather_bounds(rows,{'start':'12-25','end':'01-23'},{'start':'04-14','end':'04-28'},planning_year=2027)
    assert boro['establishment_start']=='2026-12-25'
    assert boro['establishment_end']=='2027-01-23'
    assert boro['harvest_start']=='2027-04-14'
    assert boro['valid_year_count']==10


def test_calendar_weather_excludes_missing_window_days():
    from src.compute.rotation_exposure import calendar_weather_bounds
    result=calendar_weather_bounds([{'date':date(2020,1,1),'rainfall_mm':5}],{'start':'07-23','end':'08-14'},{'start':'11-09','end':'11-24'},planning_year=2027)
    assert result['status']=='insufficient_data'
    assert result['short_interval_median_mm'] is None
    assert result['long_interval_median_mm'] is None
    assert result['short_interval_dry_spell_median_days'] is None
    assert result['long_interval_dry_spell_median_days'] is None


def test_rotation_api_exposes_only_method_matched_calendar_weather(client_and_farm):
    from app.core.database import get_db
    from app.models.core import Farmland
    client,farm_id,*_=client_and_farm
    dep=client.app.dependency_overrides[get_db]();db=next(dep)
    db.get(Farmland,farm_id).district='Rajshahi';db.commit()
    response=client.post(f'/advisor/v2/farmlands/{farm_id}/rotation-comparisons',json={'planning_year':2027})
    assert response.status_code==200
    options={o['option_id']:o for o in response.json()['options']}
    first=options['BRRI-RFS-01']
    assert first['steps'][0]['calendar_evidence']['status']=='method_not_recorded'
    assert first['steps'][1]['calendar_evidence']['status']=='source_reference_available'
    reference=first['steps'][1]['calendar_evidence']['references'][0]
    assert reference['variety_name']=='BRRI dhan31'
    assert reference['establishment_window']=={'start':'07-23','end':'08-14'}
    assert first['eligibility']=='unknown'
    wet=options['BRRI-RFS-02']['steps'][-1]
    assert wet['calendar_evidence']['status']=='method_mismatch'
    assert all(r['weather'] is None for r in wet['calendar_evidence']['references'])
    assert response.json()['selection_allowed'] is False
    dep.close()
