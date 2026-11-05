"""Decode bounded GPM_3IMERGDF V07 daily NetCDF4/HDF5 subsets.

This reader rejects ambiguous dimensions/units/dates. Successful decoding is not
field validation. Release publication additionally requires source provenance,
actual QA review and the intended spatial scope.
"""
from __future__ import annotations
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import math
import re
import hashlib
from app.services.earth_observation.qa import normalize_precipitation

MAX_FILE_BYTES = 64 * 1024 * 1024
MAX_SUBSET_CELLS = 50_000


def _text(value):
    if hasattr(value, 'shape'):
        if value.size != 1:
            raise ValueError('Expected one text attribute')
        value = value.item()
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return str(value)


def _observation_day(dataset) -> date:
    calendar = _text(dataset.attrs.get('calendar', 'standard'))
    if calendar not in ('standard', 'gregorian', 'proleptic_gregorian'):
        raise ValueError('Unsupported observation calendar')
    units = _text(dataset.attrs.get('units', ''))
    match = re.fullmatch(r'(seconds|hours|days) since (.+)', units)
    if not match or dataset.size != 1:
        raise ValueError('Daily granule needs one unambiguous observation date')
    base = datetime.fromisoformat(match[2].replace('Z', '+00:00').replace(' UTC', '+00:00'))
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    offset = float(dataset[0])
    if not math.isfinite(offset):
        raise ValueError('Invalid observation date')
    seconds = offset * {'seconds': 1, 'hours': 3600, 'days': 86400}[match[1]]
    return (base + timedelta(seconds=seconds)).astimezone(timezone.utc).date()


def _validate_time_bounds(file, expected_day: date) -> str:
    import h5py
    if 'time_bnds' not in file:
        return 'not_available'
    if isinstance(file.get('time_bnds', getlink=True), (h5py.ExternalLink, h5py.SoftLink)):
        raise ValueError('Linked time bounds are not supported')
    bounds, time = file['time_bnds'], file['time']
    if bounds.is_virtual or bounds.external or bounds.shape != (1,2) or bounds.dtype.kind not in 'fiu':
        raise ValueError('Invalid UTC day bounds')
    units = _text(time.attrs.get('units', ''))
    if _text(bounds.attrs.get('units', '')) != units:
        raise ValueError('UTC day bounds units do not match')
    match = re.fullmatch(r'(seconds|hours|days) since (.+)', units)
    if not match:
        raise ValueError('Invalid UTC day units')
    base = datetime.fromisoformat(match[2].replace('Z', '+00:00').replace(' UTC', '+00:00'))
    if base.tzinfo is None:
        base = base.replace(tzinfo=timezone.utc)
    factor = {'seconds':1, 'hours':3600, 'days':86400}[match[1]]
    values = bounds[0]
    if not all(math.isfinite(float(v)) for v in values):
        raise ValueError('Invalid UTC day bounds')
    start, end = (base + timedelta(seconds=float(v)*factor) for v in values)
    day_start = datetime.combine(expected_day, datetime.min.time(), tzinfo=timezone.utc)
    if abs((start-day_start).total_seconds()) > 1 or abs((end-(day_start+timedelta(days=1))).total_seconds()) > 2:
        raise ValueError('Observation bounds do not cover the expected UTC day')
    return 'verified_utc_day'


def read_daily_granule(path: Path, bbox: tuple[float, float, float, float], *, expected_day: date) -> dict:
    import h5py
    import numpy as np
    path = Path(path)
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= MAX_FILE_BYTES:
        raise ValueError('Unsafe or oversized IMERG granule')
    if len(bbox) != 4 or not all(math.isfinite(x) for x in bbox) or not (-180 <= bbox[0] < bbox[2] <= 180 and -90 <= bbox[1] < bbox[3] <= 90):
        raise ValueError('Invalid WGS84 bounding box')
    with h5py.File(path, 'r') as f:
        # Follow only internal datasets; external links/virtual arrays can read unrelated files.
        for name in ('time', 'lat', 'lon', 'precipitation'):
            if name not in f or isinstance(f.get(name, getlink=True), (h5py.ExternalLink, h5py.SoftLink)):
                raise ValueError('Missing or linked IMERG variable')
        ds, lat_ds, lon_ds = f['precipitation'], f['lat'], f['lon']
        if any(d.dtype.kind not in 'fiu' or d.dtype.itemsize > 8 for d in (ds,lat_ds,lon_ds,f['time'])):
            raise ValueError('IMERG arrays must use bounded numeric data types')
        if any(d.is_virtual or d.external for d in (ds, lat_ds, lon_ds, f['time'])):
            raise ValueError('External or virtual data is not supported')
        if _observation_day(f['time']) != expected_day:
            raise ValueError('Observation date does not match requested date')
        time_policy = _validate_time_bounds(f, expected_day)
        if lat_ds.ndim != 1 or lon_ds.ndim != 1 or not 2 <= lat_ds.size <= 1800 or not 2 <= lon_ds.size <= 3600:
            raise ValueError('Invalid coordinate dimensions')
        lat, lon = lat_ds[:].astype(float), lon_ds[:].astype(float)
        if not np.isfinite(lat).all() or not np.isfinite(lon).all() or (abs(lat) > 90).any() or (abs(lon) > 180).any():
            raise ValueError('Invalid coordinate values')
        if not np.allclose(np.diff(lat), .1, atol=1e-4) or not np.allclose(np.diff(lon), .1, atol=1e-4):
            raise ValueError('IMERG V07 coordinates must be ascending 0.1 degree cells')
        # Float32 coordinates can place neighbouring edges on top of each other.
        # Snap only coordinates that match the published global 0.1-degree grid.
        lat_index = np.rint((lat + 89.95) * 10).astype(int)
        lon_index = np.rint((lon + 179.95) * 10).astype(int)
        canonical_lat = -89.95 + lat_index * .1
        canonical_lon = -179.95 + lon_index * .1
        if (np.abs(lat - canonical_lat) > 1e-4).any() or (np.abs(lon - canonical_lon) > 1e-4).any():
            raise ValueError('IMERG coordinates do not match the expected global grid')
        lat, lon = canonical_lat, canonical_lon
        iy = np.flatnonzero((lat+.05 > bbox[1]+1e-8) & (lat-.05 < bbox[3]-1e-8))
        ix = np.flatnonzero((lon+.05 > bbox[0]+1e-8) & (lon-.05 < bbox[2]-1e-8))
        if not len(ix) or not len(iy):
            raise ValueError('No spatial overlap with requested region')
        if len(ix)*len(iy) > MAX_SUBSET_CELLS or ds.ndim != 3:
            raise ValueError('Daily subset exceeds bounds or has unexpected dimensions')
        axes = []
        for dim in ds.dims:
            scales = list(dim.values())
            if len(scales) != 1:
                raise ValueError('Ambiguous precipitation dimension scales')
            axes.append(scales[0].name.rsplit('/', 1)[-1])
        if sorted(axes) != ['lat', 'lon', 'time']:
            raise ValueError('Unrecognized precipitation dimensions')
        expected_sizes = {'time': 1, 'lat': len(lat), 'lon': len(lon)}
        if any(ds.shape[i] != expected_sizes[axis] for i, axis in enumerate(axes)):
            raise ValueError('Precipitation shape does not match coordinates')
        selection = {'time': slice(0, 1), 'lat': slice(int(iy[0]), int(iy[-1])+1), 'lon': slice(int(ix[0]), int(ix[-1])+1)}
        values = np.transpose(ds[tuple(selection[a] for a in axes)], [axes.index(a) for a in ['time','lat','lon']])[0]
        counts = None
        if 'precipitation_cnt' in f:
            if isinstance(f.get('precipitation_cnt', getlink=True), (h5py.ExternalLink, h5py.SoftLink)):
                raise ValueError('Linked precipitation counts are not supported')
            count_ds = f['precipitation_cnt']
            if count_ds.is_virtual or count_ds.external or count_ds.dtype.kind not in 'iu' or count_ds.shape != ds.shape:
                raise ValueError('Invalid precipitation count array')
            count_axes = [list(dim.values()) for dim in count_ds.dims]
            if any(len(scales) != 1 or scales[0].name.rsplit('/',1)[-1] != axes[i] for i, scales in enumerate(count_axes)):
                raise ValueError('Precipitation count dimensions do not match')
            counts = np.transpose(count_ds[tuple(selection[a] for a in axes)], [axes.index(a) for a in ['time','lat','lon']])[0]
        source_units = _text(ds.attrs.get('units', '')).strip()
        aliases = {'mm day-1': 'mm/day', 'mm d-1': 'mm/day', 'mm h-1': 'mm/hr', 'mm hr-1': 'mm/hr'}
        units = aliases.get(source_units, source_units)
        if units not in ('mm', 'mm/day', 'mm/hr', 'mm/h'):
            raise ValueError('Unsupported precipitation unit')
        fill = ds.attrs.get('_FillValue', ds.attrs.get('missing_value'))
        scale, offset = float(ds.attrs.get('scale_factor', 1)), float(ds.attrs.get('add_offset', 0))
        if not math.isfinite(scale) or scale <= 0 or not math.isfinite(offset):
            raise ValueError('Invalid precipitation scale/offset')
        rows = []
        for j, y in enumerate(lat[iy]):
            for i, x in enumerate(lon[ix]):
                raw = float(values[j,i])
                count = int(counts[j,i]) if counts is not None else None
                if count is not None and not 0 <= count <= 48:
                    raise ValueError('Invalid half-hour observation count')
                missing = not math.isfinite(raw) or (fill is not None and raw == float(np.asarray(fill).item()))
                incomplete = count is not None and count < 48
                value = None if missing or incomplete else normalize_precipitation(raw*scale+offset, units=units, interval_hours=24)
                rows.append({'date': expected_day.isoformat(), 'longitude': float(x), 'latitude': float(y),
                    'bounds_wgs84': [float(-180+lon_index[ix[i]]*.1),float(-90+lat_index[iy[j]]*.1),
                                     float(-180+(lon_index[ix[i]]+1)*.1),float(-90+(lat_index[iy[j]]+1)*.1)],
                    'rainfall_mm': value, 'source_support_id': f'imerg-v07:{x:.2f}:{y:.2f}',
                    'valid_halfhour_count':count,
                    'quality': 'incomplete_subdaily_coverage' if incomplete else ('missing_or_invalid' if value is None else ('coverage_unknown' if count is None else 'decoded_value'))})
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            digest.update(chunk)
    return {'product_id': 'imerg', 'version':'07', 'date':expected_day.isoformat(), 'units':'mm/day',
            'source_units':source_units, 'native_support':'0.1 degree', 'checksum_sha256':digest.hexdigest(),
            'quality_status':'decoded_pending_release_review', 'temporal_method':'pinned_daily_product_24h',
            'half_hour_coverage_policy':'require_48_valid_retrievals' if counts is not None else 'not_available',
            'time_bounds_policy':time_policy, 'rows':rows}
