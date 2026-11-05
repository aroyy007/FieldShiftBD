"""Public CMR discovery. Metadata availability is never observation ingestion."""
from datetime import date
import math
import httpx
from app.services.earth_observation.registry import product_registry

CMR = 'https://cmr.earthdata.nasa.gov/search/granules.json'
# Explicitly resolved short-name/version seams; other catalogs need exact collection IDs.
CMR_PRODUCTS = {'imerg': ('GPM_3IMERGDF', '07'), 'smap_surface': ('SPL3SMP_E', '006'),
                'smap_rootzone': ('SPL4SMGP', '008'), 'modis': ('MOD13Q1', '061'),
                'ecostress_lst': ('ECO_L2T_LSTE', '003'), 'ecostress_et': ('ECO_L3T_JET', '002'),
                'srtm': ('SRTMGL1', '003')}


def discover_assets(product_id: str, bbox: tuple[float, float, float, float], start: date, end: date,
                    *, client: httpx.Client | None = None, page_size: int = 20) -> dict:
    if product_id not in product_registry():
        raise ValueError('Unknown product')
    if len(bbox) != 4 or any(not math.isfinite(v) for v in bbox) or not (-180 <= bbox[0] < bbox[2] <= 180 and -90 <= bbox[1] < bbox[3] <= 90):
        raise ValueError('Invalid WGS84 search bounding box')
    if end < start or not 1 <= page_size <= 100:
        raise ValueError('Invalid discovery bounds')
    if product_id not in CMR_PRODUCTS:
        return {'product_id': product_id, 'state': 'collection_resolution_required', 'observations_downloaded': 0, 'assets': []}
    short_name, version = CMR_PRODUCTS[product_id]
    params = {'short_name': short_name, 'version': version, 'bounding_box': ','.join(map(str, bbox)),
              'temporal': f'{start}T00:00:00Z,{end}T23:59:59Z', 'page_size': page_size, 'sort_key': 'start_date'}
    if client is None:
        with httpx.Client(timeout=30, follow_redirects=False) as session:
            return discover_assets(product_id, bbox, start, end, client=session, page_size=page_size)
    response = client.get(CMR, params=params)
    response.raise_for_status()
    if len(response.content) > 4*1024*1024:
        raise ValueError('Discovery response exceeds metadata limit')
    assets = []
    for entry in response.json().get('feed', {}).get('entry', []):
        links = [l['href'] for l in entry.get('links', []) if l.get('rel', '').endswith('/data#') and not l.get('inherited') and l.get('href','').startswith('https://')]
        assets.append({'granule_id': entry['id'], 'collection_id': entry.get('collection_concept_id'),
                       'start': entry.get('time_start'), 'end': entry.get('time_end'), 'download_urls': links})
    return {'product_id': product_id, 'state': 'metadata_only', 'observations_downloaded': 0,
            'query': params, 'truncated': len(assets) == page_size, 'assets': assets}
