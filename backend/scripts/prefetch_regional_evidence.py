"""Discover bounded pilot assets; optionally download the first candidate per product.

Example: python -m scripts.prefetch_regional_evidence --district 5081 --bbox 88.5 24.0 88.7 24.2 --start 2024-01-01 --end 2024-01-31 --products imerg,modis --report data/earth_observation/discovery-5081.json
A search rectangle is not a verified district boundary. No arrays are published automatically.
"""
import argparse
import json
import os
import httpx
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from app.services.earth_observation.discovery import discover_assets
from app.services.earth_observation.acquisition import download_asset, SourceApprovalRequired
from app.services.earth_observation.registry import region_registry


def main():
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--district', choices=list(region_registry()), required=True)
    parser.add_argument('--bbox', nargs=4, type=float, required=True)
    parser.add_argument('--start', type=date.fromisoformat, required=True)
    parser.add_argument('--end', type=date.fromisoformat, required=True)
    parser.add_argument('--products', default='imerg,smap_surface,modis')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--download-first', action='store_true')
    parser.add_argument('--offline', action='store_true')
    parser.add_argument('--raw-dir', type=Path, default=Path('data/earth_observation/raw'))
    args = parser.parse_args()
    if args.offline:
        if not args.report.is_file():
            parser.error('Offline metadata report is missing')
        print('Offline report available; no acquisition performed.')
        return
    results = []
    for product in args.products.split(','):
        result = {'product_id': product, 'assets': [], 'observations_downloaded': 0}
        try:
            result = discover_assets(product, tuple(args.bbox), args.start, args.end)
            if args.download_first:
                asset = next((a for a in result['assets'] if a['download_urls']), None)
                if asset:
                    result['sample'] = download_asset(asset['download_urls'][0],args.raw_dir,token=os.environ.get('EARTHDATA_TOKEN'))
                    result['sample'].update(granule_id=asset['granule_id'],observation_start=asset['start'])
                else:
                    result['sample'] = {'state':'no_download_link'}
            results.append(result)
        except SourceApprovalRequired as error:
            result.update(state='source_approval_required', approval_url=error.approval_url)
            results.append(result)
        except Exception as error:
            # Exception URLs/messages can contain upstream credentials: emit type only.
            result.update(state='acquisition_failed', error_type=type(error).__name__)
            if isinstance(error, httpx.HTTPStatusError):
                result['http_status'] = error.response.status_code
            results.append(result)
    report = {'district_code': args.district, 'spatial_scope':'user_supplied_search_rectangle_not_district_average',
              'bbox': args.bbox, 'results':results, 'published_observations':0}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({r['product_id']:r['state'] for r in results}))


if __name__ == '__main__':
    main()
