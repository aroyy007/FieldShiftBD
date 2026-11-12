"""Public contracts and numerical seams for regional crop comparisons."""
from datetime import date
import pytest
from pydantic import ValidationError


def test_request_rejects_duplicate_priorities_and_unbounded_year():
    from app.contracts.challenge.v2 import RotationCompareRequest
    with pytest.raises(ValidationError):
        RotationCompareRequest(planning_year=2027, priorities=['water', 'water'])
    with pytest.raises(ValidationError):
        RotationCompareRequest(planning_year=2100)
    assert RotationCompareRequest(planning_year=2027).priorities == ['water', 'calendar']


def test_missing_metric_cannot_carry_a_numeric_claim():
    from app.contracts.challenge.v2 import MetricEvidence
    with pytest.raises(ValidationError):
        MetricEvidence(metric_id='rain', status='missing', value=12, method_id='sum', evidence_ids=[])


def test_evidence_cache_status_distinguishes_bundled_references():
    from app.contracts.challenge.v2 import EvidenceReference

    source = EvidenceReference(
        evidence_id='brri-catalog', source='BRRI', product_id='agronomy', version='v1',
        url='https://example.org', role='published_examples_pending_review',
        spatial_support='published source', cache_status='bundled_reference',
        scope='published_agronomy',
    )
    assert source.cache_status == 'bundled_reference'


def test_registry_keeps_all_products_and_context_roles():
    from app.services.earth_observation.registry import product_registry, region_registry
    products = product_registry()
    assert {'power', 'imerg', 'smap_surface', 'smap_rootzone', 'modis', 'landsat', 'ecostress_lst', 'ecostress_et', 'grace', 'srtm', 'gedi'} <= set(products)
    assert products['grace'].role == 'context_only'
    assert products['imerg'].role == 'context_only'
    assert products['srtm'].role == 'context_only'
    assert products['gedi'].role == 'conditional_context'
    assert products['smap_rootzone'].shared_input_groups == ['imerg_precipitation']
    assert set(region_registry()) == {'5081', '2015'}
    assert all(r.area_status == 'boundary_required' for r in region_registry().values())


def test_pilot_products_are_reported_as_context_only_when_present():
    from app.services.rotation.service import regional_product_state

    pilot = {'terrain': {'elevation_m': 11}}
    assert regional_product_state('power', 'hit', pilot) == 'hit'
    assert regional_product_state('imerg', 'hit', pilot) == 'pilot_unreviewed'
    assert regional_product_state('srtm', 'hit', pilot) == 'pilot_unreviewed'
    assert regional_product_state('srtm', 'hit', None) == 'not_acquired'
    assert regional_product_state('modis', 'hit', pilot) == 'not_acquired'


def test_grid_floor_and_same_cell_identity():
    from app.services.earth_observation.grid import projected_cell
    assert projected_cell(-1, -1001).cell_id == 'bd-ea-1km-v1:-1:-2'
    assert projected_cell(100, 900).cell_id == projected_cell(999, 1).cell_id
    with pytest.raises(ValueError):
        projected_cell(float('nan'), 0)


def test_harmonization_keeps_coarse_support_and_ignores_nodata():
    from app.services.earth_observation.harmonize import aggregate_samples
    result = aggregate_samples([(10.0, 1.0, 'pixel-A'), (None, 1.0, 'pixel-B'), (20.0, 2.0, 'pixel-A')])
    assert result['value'] == pytest.approx(50 / 3)
    assert result['valid_fraction'] == 0.75
    assert result['independent_support_count'] == 1
    assert aggregate_samples([(None, 1.0, 'x')])['value'] is None
    with pytest.raises(ValueError):
        aggregate_samples([(1.0, -1.0, 'x')])


def test_release_roundtrip_tamper_and_path_rejection(tmp_path):
    from app.services.earth_observation.release import publish_release, read_release
    metadata = {'district_code': '5081', 'products': ['imerg'], 'scope': 'reference_point'}
    release_id = publish_release(tmp_path, metadata, [{'date': '2024-01-01', 'rainfall_mm': 4.0}])
    assert read_release(tmp_path, release_id)['rows'][0]['rainfall_mm'] == 4.0
    with pytest.raises(ValueError):
        read_release(tmp_path, '../escape')
    (tmp_path / release_id / 'features.parquet').write_bytes(b'tampered')
    with pytest.raises(ValueError, match='checksum'):
        read_release(tmp_path, release_id)


def test_rainfall_missing_day_does_not_shorten_dry_spell():
    from src.compute.rotation_exposure import rainfall_window
    rows = [{'date': date(2024, 1, 1), 'rainfall_mm': 0}, {'date': date(2024, 1, 3), 'rainfall_mm': 10}]
    result = rainfall_window(rows, date(2024, 1, 1), date(2024, 1, 3))
    assert result['coverage'] == pytest.approx(2 / 3)
    assert result['longest_dry_spell_days'] is None
    assert result['rainfall_mm'] is None


def test_calendar_cross_year_overlap_and_missing_rules():
    from app.services.rotation.catalog import ReviewedRuleSet, RotationCandidate, RotationCandidateStep
    from src.compute.rotation_calendar import evaluate_calendar
    steps = (
        RotationCandidateStep('rice', 'aman', 'reported', ('history',), start_date=date(2026, 8, 1), end_date=date(2026, 11, 30)),
        RotationCandidateStep('wheat', 'rabi', 'reported', ('history',), start_date=date(2026, 11, 25), end_date=date(2027, 3, 1)),
    )
    candidate = RotationCandidate('synthetic', 'baseline', '5081', steps, ('history',), 'farmer_recorded', 'unknown')
    assert evaluate_calendar(candidate, 2026, None).status == 'overlap'
    steps = (steps[0], RotationCandidateStep('wheat', 'rabi', 'reported', ('history',), start_date=date(2026, 12, 10), end_date=date(2027, 3, 1)))
    candidate = RotationCandidate('synthetic', 'baseline', '5081', steps, ('history',), 'farmer_recorded', 'unknown')
    assert evaluate_calendar(candidate, 2026, None).status == 'needs_turnaround_rule'
    rule = ReviewedRuleSet(7, ('reviewed-turnaround-rule',), 'reviewed')
    assert evaluate_calendar(candidate, 2026, rule).status == 'feasible'
    incomplete = RotationCandidate('synthetic', 'baseline', '5081', (steps[0], RotationCandidateStep('wheat', 'rabi', 'reported', ('history',))), ('history',), 'farmer_recorded', 'unknown')
    assert evaluate_calendar(incomplete, 2026, rule).status == 'insufficient_dates'


def test_preference_order_respects_unknown_income_and_water_priority():
    from src.compute.rotation_preferences import compare_options
    options = [{'option_id': 'high-water', 'eligibility': 'eligible', 'metrics': {'water': 3, 'calendar': 20}}, {'option_id': 'low-water', 'eligibility': 'eligible', 'metrics': {'water': 1, 'calendar': 5}}]
    assert compare_options(options, ['water', 'calendar'])['preferred_option_ids'] == ['low-water']
    assert compare_options(options, ['calendar', 'water'])['preferred_option_ids'] == ['high-water']
    assert compare_options(options, ['income'])['ordering_status'] == 'insufficient_evidence'


def test_regional_api_owns_farm_and_does_not_mutate_seasons(client_and_farm):
    from app.core.database import get_db
    from app.models.core import Farmland
    client, farm_id, season_id, _ = client_and_farm
    dep = client.app.dependency_overrides[get_db]()
    db = next(dep)
    farm = db.get(Farmland, farm_id)
    farm.district = 'Rajshahi'
    farm.irrigation_available = True
    farm.land_type = 'high'
    farm.soil_type = 'clay'
    db.commit()
    before = client.get(f'/farmlands/{farm_id}/state').json()
    response = client.post(f'/advisor/v2/farmlands/{farm_id}/rotation-comparisons', json={'planning_year': 2027})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['district_code'] == '5081'
    assert body['contract_version'] == '2.0.0'
    assert body['options'][0]['role'] == 'baseline'
    calendar = next(m for m in body['options'][0]['metrics'] if m['metric_id'] == 'recorded_calendar')
    assert calendar['status'] == 'missing'
    assert 'expected' in calendar['detail_en'].lower()
    assert len(body['options']) >= 3
    assert body['selection_allowed'] is False
    assert body['ordering_status'] == 'insufficient_evidence'
    assert body['options'][1]['eligibility'] == 'unknown'
    calendar_metric = next(m for m in body['options'][1]['metrics'] if m['metric_id'] == 'calendar')
    gdd_metric = next(m for m in body['options'][1]['metrics'] if m['metric_id'] == 'gdd')
    assert calendar_metric['status'] == 'missing' and calendar_metric['value'] is None
    assert 'windows are missing' in calendar_metric['detail_en'] or 'overlap' in calendar_metric['detail_en']
    assert gdd_metric['status'] == 'missing' and gdd_metric['value'] is None
    assert 'GDD base, cap, target' in gdd_metric['detail_en']
    agronomy_evidence = [item for item in body['evidence'] if item['scope'] == 'published_agronomy']
    assert agronomy_evidence
    assert all(item['cache_status'] == 'bundled_reference' for item in agronomy_evidence)
    power_evidence = [item for item in body['evidence'] if item['product_id'] == 'power']
    assert all(item['cache_status'] == 'hit' for item in power_evidence)
    assert body['snapshot_hash'] == client.post(f'/advisor/v2/farmlands/{farm_id}/rotation-comparisons', json={'planning_year': 2027}).json()['snapshot_hash']
    assert client.post(f'/advisor/v2/farmlands/{client.app.state.other_farmland_id}/rotation-comparisons', json={'planning_year': 2027}).status_code == 404
    after = client.get(f'/farmlands/{farm_id}/state').json()
    assert after['active_season']['id'] == before['active_season']['id']
    assert after['tasks'] == before['tasks']
    assert after['open_problems'] == before['open_problems']
    dep.close()


def test_regional_inventory_is_truthful_and_public(client_and_farm):
    client, *_ = client_and_farm
    result = client.get('/advisor/v2/regions')
    assert result.status_code == 200
    assert len(result.json()['regions']) == 2
    assert next(p for p in result.json()['products'] if p['product_id'] == 'gedi')['state'] == 'not_acquired'


def test_discovery_never_counts_metadata_as_observations():
    import httpx
    from app.services.earth_observation.discovery import discover_assets
    def respond(request):
        assert request.url.host == 'cmr.earthdata.nasa.gov'
        assert request.url.params['short_name'] == 'GPM_3IMERGDF'
        assert request.url.params['page_size'] == '20'
        return httpx.Response(200, json={'feed': {'entry': [{'id': 'G1-TEST', 'time_start': '2024-01-01T00:00:00Z', 'links': [{'href':'https://gpm1.gesdisc.eosdis.nasa.gov/data/test.nc4','rel':'http://esipfed.org/ns/fedsearch/1.1/data#'}]}]}})
    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        result = discover_assets('imerg', (88.5,24.0,88.7,24.2), date(2024,1,1), date(2024,1,2), client=client)
    assert result['state'] == 'metadata_only'
    assert result['assets'][0]['granule_id'] == 'G1-TEST'
    assert result['observations_downloaded'] == 0


def test_safe_download_rejects_non_nasa_hosts_and_html(tmp_path):
    import httpx
    from app.services.earth_observation.acquisition import download_asset
    with pytest.raises(ValueError, match='host'):
        download_asset('https://example.com/secret', tmp_path)
    with httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(200, content=b'<html>Login</html>', headers={'content-type':'text/html'}))) as client:
        with pytest.raises(ValueError, match='HTML'):
            download_asset('https://gpm1.gesdisc.eosdis.nasa.gov/data/test.nc4', tmp_path, client=client)
    assert list(tmp_path.iterdir()) == []


def test_download_reports_official_eula_handoff_without_token(tmp_path):
    import httpx
    from app.services.earth_observation.acquisition import download_asset, SourceApprovalRequired
    reply = {'error_description':'EULA Acceptance Failure','resolution_url':'https://urs.earthdata.nasa.gov/approve_app?client_id=public-client-id'}
    with httpx.Client(transport=httpx.MockTransport(lambda req: httpx.Response(403,json=reply))) as client:
        with pytest.raises(SourceApprovalRequired) as caught:
            download_asset('https://data.gesdisc.earthdata.nasa.gov/data/sample.nc4',tmp_path,client=client,token='TEST-ONLY-SECRET')
    assert caught.value.approval_url == reply['resolution_url']
    assert 'TEST-ONLY-SECRET' not in str(caught.value)
    assert not list(tmp_path.iterdir())


def test_analysis_grid_projects_known_origin_and_rejects_wrong_boundary():
    pytest.importorskip('pyproj')
    pytest.importorskip('shapely')
    from app.services.earth_observation.grid import resolve_analysis_cell
    from shapely.geometry import box
    assert resolve_analysis_cell(0, 0, boundary=box(-1,-1,1,1)).cell_id == 'bd-ea-1km-v1:0:0'
    with pytest.raises(ValueError, match='outside'):
        resolve_analysis_cell(2, 2, boundary=box(-1,-1,1,1))


def test_imerg_normalization_checks_units_and_masks_fill():
    from app.services.earth_observation.qa import normalize_precipitation
    assert normalize_precipitation(2, units='mm/hr', interval_hours=0.5) == 1
    assert normalize_precipitation(-9999, units='mm/day', fill_value=-9999) is None
    with pytest.raises(ValueError, match='unit'):
        normalize_precipitation(2, units='unknown')


def test_landsat_index_applies_offset_before_ratio():
    from app.services.earth_observation.qa import landsat_ndvi
    # Red DN 10000 -> 0.075; NIR DN 20000 -> 0.35; NDVI = 0.275/0.425.
    assert landsat_ndvi(10000, 20000, quality_ok=True) == pytest.approx(0.6470588235294118)
    assert landsat_ndvi(10000, 20000, quality_ok=False) is None


@pytest.mark.parametrize('manifest_quality,source_quality', [('synthetic','verified'),('verified','synthetic'),('verified','stale'),('verified','unavailable')])
def test_power_loader_never_publishes_synthetic_or_unavailable_evidence(tmp_path,monkeypatch,manifest_quality,source_quality):
    from types import SimpleNamespace
    from app.services.earth_observation.provider import load_power_context
    from app.services.climate.cache import ClimateBundleCache
    bundle = SimpleNamespace(manifest=SimpleNamespace(sampling_point=object(), quality_status=manifest_quality,
        provenance=[SimpleNamespace(method='nasa_power',quality_status=source_quality)]))
    monkeypatch.setattr(ClimateBundleCache, 'load_bundle', lambda self, district: bundle)
    assert load_power_context(tmp_path,'5081') == (None,'corrupt')


def test_priority_reorders_options_and_previous_crop_forms_baseline(client_and_farm):
    from app.core.database import get_db
    from app.models.core import Farmland
    client, farm_id, _, _ = client_and_farm
    dep = client.app.dependency_overrides[get_db]()
    db = next(dep)
    farm = db.get(Farmland, farm_id)
    farm.district, farm.irrigation_available, farm.land_type, farm.soil_type = 'Rajshahi', True, 'high', 'clay'
    db.commit()
    url = f'/advisor/v2/farmlands/{farm_id}/rotation-comparisons'
    water = client.post(url, json={'planning_year': 2027, 'priorities': ['water', 'diversity']}).json()
    diversity = client.post(url, json={'planning_year': 2027, 'priorities': ['diversity', 'water']}).json()
    income = client.post(url, json={'planning_year': 2027, 'priorities': ['income']}).json()
    assert water['exploration_order'][0]['option_id'] == 'BRRI-RFS-02'
    assert [e['option_id'] for e in water['exploration_order']] != [e['option_id'] for e in diversity['exploration_order']]
    assert income['exploration_status'] == 'insufficient_evidence' and income['exploration_order'] == []
    assert water['preferred_option_ids'] == [] and water['selection_allowed'] is False
    for option in water['options'][1:]:
        assert option['why_en'] and option['benefits_en'] and option['risks_en'] and option['gaps_en']
    dep.close()


def test_previous_crop_forms_provisional_baseline_when_no_history():
    from types import SimpleNamespace
    from app.services.rotation.catalog import _history_steps
    snapshot = SimpleNamespace(rotation_history=[], active_season=None, profile=SimpleNamespace(previous_crop=' Potato '))
    (step,) = _history_steps(snapshot)
    assert step.crop_code == 'Potato' and step.event_basis == 'farmer_reported_previous_crop' and step.start_date is None
    assert _history_steps(SimpleNamespace(rotation_history=[], active_season=None, profile=SimpleNamespace(previous_crop=None))) == ()
