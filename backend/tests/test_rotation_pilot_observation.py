import json

import pytest

from app.services.earth_observation.release import publish_release
from app.services.earth_observation.pilot import read_pilot_observation


def test_pilot_summary_uses_coverage_and_native_support_not_grid_count(tmp_path):
    metadata={'district_code':'5081','products':['imerg'],'scope':'pilot_grid',
        'district_assignment':'unverified_request_label','half_hour_coverage_policy':'require_48_valid_retrievals','time_bounds_policy':'verified_utc_day',
        'quality_status':'decoded_pending_release_review','coverage_start':'2024-01-01','coverage_end':'2024-01-01',
        'bbox_wgs84':[88.5,24.2,88.8,24.5], 'native_support':'0.1 degree', 'units':'mm/day',
        'source_assets':[{'product_id':'imerg','version':'07','granule_id':'G-TEST','acquisition_method':'user_supplied_unverified'}]}
    rows=[{'rainfall_mm':2.,'valid_fraction':1.,'analysis_area_m2':100.,'source_support_ids':['a']},
          {'rainfall_mm':4.,'valid_fraction':0.5,'analysis_area_m2':200.,'source_support_ids':['a','b']},
          {'rainfall_mm':None,'valid_fraction':0.,'analysis_area_m2':100.,'source_support_ids':[]}]
    release=publish_release(tmp_path/'staged', metadata, rows)
    (tmp_path/'pilot-index.json').write_text(json.dumps({'5081':release}))
    result=read_pilot_observation(tmp_path,'5081')
    assert result['mean_mm'] == pytest.approx(3.0)
    assert result['coverage_fraction'] == pytest.approx(.5)
    assert result['native_support_count'] == 2
    assert result['status']=='prototype_unreviewed'
    assert result['acquisition_method']=='user_supplied_unverified'
    assert 'unverified' in result['source'].lower()


def test_missing_or_tampered_pilot_is_never_presented_as_observation(tmp_path):
    assert read_pilot_observation(tmp_path,'5081') is None
    (tmp_path/'pilot-index.json').write_text(json.dumps({'5081':'a'*64}))
    assert read_pilot_observation(tmp_path,'5081') is None
