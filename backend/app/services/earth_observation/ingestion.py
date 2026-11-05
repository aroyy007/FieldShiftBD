"""Offline worker: downloaded IMERG sample → decoded pilot grid → review staging."""
from datetime import date
from pathlib import Path
import re
from app.services.earth_observation.registry import region_registry
from app.services.earth_observation.products.imerg import read_daily_granule
from app.services.earth_observation.harmonize import grid_daily_precipitation
from app.services.earth_observation.release import publish_release


def stage_imerg_sample(report: dict, raw_root: Path, release_root: Path) -> dict:
    from shapely.geometry import box
    district = report.get('district_code')
    if district not in region_registry():
        raise ValueError('Unsupported region')
    record = next((r for r in report.get('results', []) if r.get('product_id') == 'imerg'), None)
    sample = record.get('sample', {}) if record else {}
    if sample.get('state') != 'downloaded_pending_product_qa':
        raise ValueError('No completed IMERG download is available for staging')
    query = record.get('query', {})
    if query.get('short_name') != 'GPM_3IMERGDF' or query.get('version') != '07':
        raise ValueError('Source product/version is not IMERG Final daily V07')
    bbox = tuple(report['bbox'])
    try:
        query_bbox = tuple(float(value) for value in query['bounding_box'].split(','))
    except (KeyError, ValueError, AttributeError) as exc:
        raise ValueError('Missing or invalid search bounding box') from exc
    if len(bbox) != 4 or query_bbox != bbox:
        raise ValueError('Report and search bounding box do not match')
    digest = sample.get('checksum_sha256', '')
    if not re.fullmatch(r'[a-f0-9]{64}', digest) or sample.get('relative_path') != digest:
        raise ValueError('Invalid raw asset identity')
    day = date.fromisoformat(sample['observation_start'][:10])
    decoded = read_daily_granule(raw_root.resolve()/digest,bbox,expected_day=day)
    if decoded['checksum_sha256'] != digest:
        raise ValueError('Downloaded asset checksum does not match source report')
    rows = grid_daily_precipitation(decoded,box(*bbox))
    metadata = {'district_code':district,'district_assignment':'unverified_request_label','products':['imerg'],'scope':'pilot_grid',
        'quality_status':'synthetic' if report.get('synthetic') is True else 'decoded_pending_release_review',
        'spatial_scope':'pilot_search_rectangle_not_district_or_cropland_average',
        'bbox_wgs84':list(bbox),'grid_id':'bd-ea-1km-v1','crs':'EPSG:6933','cell_size_m':1000,
        'units':'mm/day','native_support':'0.1 degree','coverage_start':str(day),'coverage_end':str(day),
        'method_id':'imerg_daily_units_dimension_qa_overlap_mean_v1',
        'half_hour_coverage_policy':decoded['half_hour_coverage_policy'],
        'time_bounds_policy':decoded['time_bounds_policy'],
        'source_units':decoded['source_units'],
        'source_assets':[{'product_id':'imerg','version':'07','granule_id':sample['granule_id'],
                          'checksum_sha256':digest,'observation_start':sample['observation_start'],
                          'acquisition_method':sample.get('acquisition_method','official_download_pending_review')}],
        'limitations':['Requested district label is unverified; pilot rectangle is not a district/cropland mask.',
                       'Target 1 km cells sharing one native source cell are not independent observations.',
                       'Decoding and QA tests do not establish field accuracy or a historical series.']}
    release_id=publish_release(release_root,metadata,rows)
    return {'state':'staged_pending_review','release_id':release_id,'grid_rows':len(rows),
            'quality_status':metadata['quality_status'],'published_as_current':False}
