"""Worker tests use explicitly synthetic files; no real observation claim."""
from datetime import date
import pytest

h5py = pytest.importorskip('h5py')
np = pytest.importorskip('numpy')


def make_granule(path, *, units='mm/hr', day=19723, values=None):
    with h5py.File(path,'w') as f:
        time=f.create_dataset('time',data=[day]);time.attrs['units']='days since 1970-01-01 00:00:00';time.make_scale('time')
        lat=f.create_dataset('lat',data=[24.05,24.15]);lat.make_scale('lat')
        lon=f.create_dataset('lon',data=[88.55,88.65]);lon.make_scale('lon')
        ds=f.create_dataset('precipitation',data=np.array(values if values is not None else [[[2,2],[2,-9999]]],dtype='f4'))
        ds.attrs['units']=units;ds.attrs['_FillValue']=-9999.0
        for i,axis in enumerate([time,lat,lon]):ds.dims[i].attach_scale(axis)
    return path


def test_daily_imerg_rate_converts_and_preserves_fill_and_support(tmp_path):
    from app.services.earth_observation.products.imerg import read_daily_granule
    path=make_granule(tmp_path/'synthetic.nc4')
    result=read_daily_granule(path,(88.5,24.0,88.7,24.2),expected_day=date(2024,1,1))
    assert result['quality_status']=='decoded_pending_release_review'
    assert len(result['rows'])==4
    assert [r['rainfall_mm'] for r in result['rows']]==[48,48,48,None]
    assert len({r['source_support_id'] for r in result['rows']})==4
    assert result['source_units']=='mm/hr'
    assert result['units']=='mm/day'
    assert result['rows'][0]['bounds_wgs84']==pytest.approx([88.5,24.0,88.6,24.1])


def test_reader_rejects_wrong_day_unknown_units_and_no_overlap(tmp_path):
    from app.services.earth_observation.products.imerg import read_daily_granule
    path=make_granule(tmp_path/'synthetic.nc4')
    with pytest.raises(ValueError,match='date'):
        read_daily_granule(path,(88.5,24.0,88.7,24.2),expected_day=date(2024,1,2))
    with pytest.raises(ValueError,match='overlap'):
        read_daily_granule(path,(91,22,92,23),expected_day=date(2024,1,1))
    path=make_granule(tmp_path/'bad.nc4',units='inches per month')
    with pytest.raises(ValueError,match='unit'):
        read_daily_granule(path,(88.5,24.0,88.7,24.2),expected_day=date(2024,1,1))


def test_real_style_array_attributes_and_subdaily_count_are_checked(tmp_path):
    from app.services.earth_observation.products.imerg import read_daily_granule
    path = make_granule(tmp_path/'real-style.nc4', units='mm/day', values=[[[5, 6], [7, 8]]])
    with h5py.File(path, 'a') as f:
        f['time'].attrs['units'] = np.array(['days since 1970-01-01 00:00:00Z'], dtype=h5py.string_dtype())
        f['precipitation'].attrs['units'] = np.array(['mm/day'], dtype=h5py.string_dtype())
        count = f.create_dataset('precipitation_cnt', data=np.array([[[48,24],[0,48]]],dtype='i1'))
        for i, axis in enumerate(['time','lat','lon']): count.dims[i].attach_scale(f[axis])
        bounds = f.create_dataset('time_bnds', data=np.array([[19723,19723+86399/86400]]))
        bounds.attrs['units'] = np.array(['days since 1970-01-01 00:00:00Z'], dtype=h5py.string_dtype())
    result = read_daily_granule(path,(88.5,24,88.7,24.2),expected_day=date(2024,1,1))
    assert [r['rainfall_mm'] for r in result['rows']] == [5,None,None,8]
    assert [r['valid_halfhour_count'] for r in result['rows']] == [48,24,0,48]
    assert result['rows'][1]['quality'] == 'incomplete_subdaily_coverage'
    assert result['half_hour_coverage_policy'] == 'require_48_valid_retrievals'
    assert result['time_bounds_policy'] == 'verified_utc_day'
    with h5py.File(path, 'a') as f:
        f['time_bnds'][0, 0] += .1
    with pytest.raises(ValueError, match='UTC day'):
        read_daily_granule(path,(88.5,24,88.7,24.2),expected_day=date(2024,1,1))


def test_lat_lon_axis_order_is_taken_from_dimension_scales(tmp_path):
    from app.services.earth_observation.products.imerg import read_daily_granule
    path=make_granule(tmp_path/'axes.nc4',units='mm/day',values=[[[1,2],[3,4]]])
    with h5py.File(path,'a') as f:
        del f['precipitation']
        ds=f.create_dataset('precipitation',data=np.array([[[1,3],[2,4]]],dtype='f4'))
        ds.attrs['units']='mm/day'
        for i,axis in enumerate(['time','lon','lat']):ds.dims[i].attach_scale(f[axis])
    result=read_daily_granule(path,(88.5,24.0,88.7,24.2),expected_day=date(2024,1,1))
    assert [r['rainfall_mm'] for r in result['rows']]==[1,2,3,4]


def test_grid_aggregation_retains_coarse_source_support_and_missing_fraction():
    from app.services.earth_observation.harmonize import grid_daily_precipitation
    from pyproj import Transformer
    from shapely.geometry import box
    # One native IMERG cell overlaps many 1 km analysis cells; each has one source support.
    decoded={'product_id':'imerg','version':'07','date':'2024-01-01','units':'mm/day','rows':[
        {'bounds_wgs84':[88.5,24.0,88.6,24.1],'rainfall_mm':20.,'source_support_id':'imerg-v07:88.55:24.05'},
        {'bounds_wgs84':[88.6,24.0,88.7,24.1],'rainfall_mm':None,'source_support_id':'imerg-v07:88.65:24.05'}]}
    result=grid_daily_precipitation(decoded,box(88.5,24.0,88.7,24.1))
    assert len(result)>100
    assert all(r['rainfall_mm']==pytest.approx(20) for r in result if r['rainfall_mm'] is not None)
    assert any(r['rainfall_mm'] is None for r in result)
    assert all(r['independent_support_count'] <= 1 for r in result)
    assert all(0 <= r['valid_fraction'] <= 1 for r in result)
    assert all(r['cell_id'].startswith('bd-ea-1km-v1:') for r in result)


def test_grid_rejects_unbounded_region_and_wrong_product():
    from app.services.earth_observation.harmonize import grid_daily_precipitation
    from shapely.geometry import box
    with pytest.raises(ValueError,match='budget'):
        grid_daily_precipitation({'product_id':'imerg','units':'mm/day','rows':[]}, box(88,22,93,27), max_cells=10)
    with pytest.raises(ValueError,match='product'):
        grid_daily_precipitation({'product_id':'grace','units':'cm','rows':[]},box(88.5,24,88.6,24.1))


def test_stage_sample_is_explicitly_synthetic_and_never_approved(tmp_path):
    import hashlib,json
    from app.services.earth_observation.ingestion import stage_imerg_sample
    from app.services.earth_observation.release import read_release
    source=make_granule(tmp_path/'synthetic.nc4')
    data=source.read_bytes();digest=hashlib.sha256(data).hexdigest()
    raw=tmp_path/'raw';raw.mkdir();(raw/digest).write_bytes(data)
    report={'district_code':'5081','bbox':[88.5,24,88.7,24.2],'synthetic':True,'results':[{
        'product_id':'imerg','state':'metadata_only','assets':[], 'query':{'short_name':'GPM_3IMERGDF','version':'07','bounding_box':'88.5,24,88.7,24.2'},
        'sample':{'state':'downloaded_pending_product_qa','checksum_sha256':digest,'relative_path':digest,
                  'granule_id':'G-SYNTHETIC','observation_start':'2024-01-01T00:00:00Z'}}]}
    staged=stage_imerg_sample(report,raw,tmp_path/'releases')
    result=read_release(tmp_path/'releases',staged['release_id'])
    assert result['metadata']['scope']=='pilot_grid'
    assert result['metadata']['district_assignment']=='unverified_request_label'
    assert result['metadata']['quality_status']=='synthetic'
    assert result['metadata']['source_assets'][0]['checksum_sha256']==digest
    assert staged['state']=='staged_pending_review'
    assert result['rows'][0]['grid_id']=='bd-ea-1km-v1'
    report['bbox'] = [91.5, 22, 91.7, 22.2]
    with pytest.raises(ValueError, match='search bounding box'):
        stage_imerg_sample(report,raw,tmp_path/'releases')


def test_stage_refuses_failed_download_reports(tmp_path):
    from app.services.earth_observation.ingestion import stage_imerg_sample
    report={'district_code':'5081','bbox':[88.5,24,88.7,24.2],'results':[{'product_id':'imerg','state':'source_approval_required'}]}
    with pytest.raises(ValueError,match='download'):
        stage_imerg_sample(report,tmp_path/'raw',tmp_path/'releases')


def test_user_download_can_be_imported_and_staged_as_unverified(tmp_path):
    from app.services.earth_observation.manual_import import import_imerg_granule
    from app.services.earth_observation.ingestion import stage_imerg_sample
    from app.services.earth_observation.release import read_release
    path=make_granule(tmp_path/'synthetic.nc4')
    report={'district_code':'5081','bbox':[88.5,24,88.7,24.2],'synthetic':True,'results':[{
        'product_id':'imerg','query':{'short_name':'GPM_3IMERGDF','version':'07','bounding_box':'88.5,24,88.7,24.2'},
        'assets':[{'granule_id':'G-SYNTHETIC','start':'2024-01-01T00:00:00Z',
                   'download_urls':['https://gpm1.gesdisc.eosdis.nasa.gov/data/synthetic.nc4']}]}]}
    imported=import_imerg_granule(report,'G-SYNTHETIC',path,tmp_path/'raw')
    staged=stage_imerg_sample(imported,tmp_path/'raw',tmp_path/'releases')
    metadata=read_release(tmp_path/'releases',staged['release_id'])['metadata']
    assert metadata['source_assets'][0]['acquisition_method']=='user_supplied_unverified'
    assert metadata['quality_status']=='synthetic' and not staged['published_as_current']


def test_reader_refuses_string_arrays_before_decoding(tmp_path):
    from app.services.earth_observation.products.imerg import read_daily_granule
    path=make_granule(tmp_path/'text.nc4')
    with h5py.File(path,'a') as f:
        del f['precipitation']
        ds=f.create_dataset('precipitation',data=np.array([[['1','2'],['3','4']]],dtype=h5py.string_dtype()))
        ds.attrs['units']='mm/day'
        for i,axis in enumerate(['time','lat','lon']):ds.dims[i].attach_scale(f[axis])
    with pytest.raises(ValueError,match='numeric'):
        read_daily_granule(path,(88.5,24,88.7,24.2),expected_day=date(2024,1,1))


def test_float32_coordinates_produce_adjacent_grid_cells(tmp_path):
    from app.services.earth_observation.products.imerg import read_daily_granule
    from app.services.earth_observation.harmonize import grid_daily_precipitation
    from shapely.geometry import box
    path = tmp_path / 'float32.nc4'
    with h5py.File(path, 'w') as f:
        time = f.create_dataset('time', data=[19723]); time.attrs['units'] = 'days since 1970-01-01'; time.make_scale('time')
        lat = f.create_dataset('lat', data=np.array([24.05, 24.15], dtype='f4')); lat.make_scale('lat')
        lon = f.create_dataset('lon', data=np.array([88.55, 88.65], dtype='f4')); lon.make_scale('lon')
        ds = f.create_dataset('precipitation', data=np.ones((1, 2, 2), dtype='f4')); ds.attrs['units'] = 'mm/day'
        for i, axis in enumerate([time, lat, lon]): ds.dims[i].attach_scale(axis)
    result = read_daily_granule(path, (88.5, 24.0, 88.7, 24.2), expected_day=date(2024, 1, 1))
    assert result['rows'][0]['bounds_wgs84'][2] == result['rows'][1]['bounds_wgs84'][0]
    assert grid_daily_precipitation(result, box(88.5, 24.0, 88.7, 24.2))
    with h5py.File(path, 'a') as f:
        f['lon'][:] = [88.56, 88.66]
    with pytest.raises(ValueError, match='expected global grid'):
        read_daily_granule(path, (88.5, 24.0, 88.7, 24.2), expected_day=date(2024, 1, 1))


def test_stage_rejects_wrong_cmr_product_before_reading_asset(tmp_path):
    from app.services.earth_observation.ingestion import stage_imerg_sample
    report={'district_code':'5081','bbox':[88.5,24,88.7,24.2],'results':[{
        'product_id':'imerg','query':{'short_name':'GPM_3IMERGDE','version':'07'},
        'sample':{'state':'downloaded_pending_product_qa','checksum_sha256':'a'*64,'relative_path':'a'*64,'granule_id':'G-TEST','observation_start':'2024-01-01'}}]}
    with pytest.raises(ValueError,match='product'):
        stage_imerg_sample(report,tmp_path/'raw',tmp_path/'releases')
