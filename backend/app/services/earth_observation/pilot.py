"""Read a locally staged one-day demonstration; never a recommendation input."""
import json
import math
from functools import lru_cache
from pathlib import Path

import pyarrow
from app.services.earth_observation.release import read_release


@lru_cache(maxsize=8)
def _verified_srtm_sample(path: str, size: int, modified_ns: int, changed_ns: int, inode: int, latitude: float, longitude: float) -> dict:
    from app.services.earth_observation.products.srtm import sample_hgt
    return sample_hgt(Path(path), latitude, longitude)


def read_pilot_terrain(root: Path, district: str, latitude: float | None,
                       longitude: float | None) -> dict | None:
    try:
        if latitude is None or longitude is None:
            return None
        expected_files = {'5081':'N24E088.SRTMGL1.hgt.zip', '2015':'N22E091.SRTMGL1.hgt.zip'}
        if district not in expected_files or not math.isfinite(latitude) or not math.isfinite(longitude):
            return None
        source = root/'raw'/expected_files[district]
        if source.is_symlink() or not source.is_file():
            return None
        stat = source.stat()
        if stat.st_size > 64*1024*1024:
            return None
        sample = _verified_srtm_sample(str(source), stat.st_size, stat.st_mtime_ns,
                                       stat.st_ctime_ns, stat.st_ino, latitude, longitude)
        return {**sample, 'sample_basis':'field_profile_coordinate'}
    except (KeyError, ValueError, TypeError, OSError):
        return None


def read_pilot_observation(root: Path, district: str, latitude: float | None = None,
                           longitude: float | None = None) -> dict | None:
    try:
        index = root / 'pilot-index.json'
        if index.is_symlink() or not index.is_file() or index.stat().st_size > 4096:
            return None
        release_id = json.loads(index.read_text())[district]
        release = read_release(root / 'staged', release_id)
        meta, rows = release['metadata'], release['rows']
        assets = meta['source_assets']
        if (meta['district_code'] != district or meta['scope'] != 'pilot_grid'
            or meta['district_assignment'] != 'unverified_request_label'
            or meta['quality_status'] != 'decoded_pending_release_review'
            or meta['half_hour_coverage_policy'] != 'require_48_valid_retrievals'
            or meta['time_bounds_policy'] != 'verified_utc_day'
            or meta['products'] != ['imerg'] or meta['units'] != 'mm/day'
            or meta['coverage_start'] != meta['coverage_end']
            or len(assets) != 1 or assets[0]['product_id'] != 'imerg' or assets[0]['version'] != '07'
            or assets[0]['acquisition_method'] != 'user_supplied_unverified'):
            return None
        total = valid = weighted = 0.0
        supports = set()
        for row in rows:
            area, fraction, value = row['analysis_area_m2'], row['valid_fraction'], row['rainfall_mm']
            if not math.isfinite(area) or area <= 0 or not math.isfinite(fraction) or not 0 <= fraction <= 1:
                return None
            total += area
            if value is not None:
                if not math.isfinite(value) or value < 0:
                    return None
                valid += area * fraction
                weighted += value * area * fraction
                supports.update(row['source_support_ids'])
            elif fraction != 0:
                return None
        if not total or not valid or not supports:
            return None
        terrain = read_pilot_terrain(root, district, latitude, longitude)
        return {'status':'prototype_unreviewed','date':meta['coverage_start'],
                'mean_mm':weighted / valid, 'coverage_fraction':valid / total,
                'native_support_count':len(supports), 'bbox_wgs84':meta['bbox_wgs84'],
                'source':'Reported GPM IMERG Final V07 daily (user supplied; unverified)', 'source_url':'https://gpm.nasa.gov/data/imerg',
                'acquisition_method':'user_supplied_unverified',
                'native_support':meta['native_support'], 'release_id':release_id,'terrain':terrain}
    except (KeyError, ValueError, TypeError, OSError, pyarrow.ArrowException):
        return None
