"""Area-weighted intensive-variable summaries without inventing spatial samples."""
import math
from collections.abc import Iterable


def aggregate_samples(samples: Iterable[tuple[float | None, float, str]]) -> dict:
    total = valid = weighted = 0.0
    supports = set()
    for value, area, support in samples:
        if not math.isfinite(area) or area < 0:
            raise ValueError('Overlap area must be finite and nonnegative')
        total += area
        if value is not None and math.isfinite(value) and area > 0:
            valid += area
            weighted += value * area
            supports.add(support)
    return {'value': weighted / valid if valid else None,
            'valid_fraction': valid / total if total else 0.0,
            'independent_support_count': len(supports), 'source_support_ids': sorted(supports)}


def grid_daily_precipitation(decoded: dict, boundary_wgs84, *, max_cells: int = 50_000) -> list[dict]:
    """Conservative intensive-depth join on 1 km cells, clipped to an explicit mask.

    The caller owns geometry provenance and release approval. A district polygon
    alone is not a cropland/ocean mask. Support count means unique native cells,
    not proof of statistical independence between neighboring retrievals.
    """
    if decoded.get('product_id') != 'imerg' or decoded.get('units') != 'mm/day':
        raise ValueError('Unexpected product or precipitation units')
    from pyproj import Transformer
    from shapely.geometry import box
    from shapely.ops import transform
    from shapely.strtree import STRtree
    from app.services.earth_observation.grid import projected_cell
    if boundary_wgs84.is_empty or not boundary_wgs84.is_valid:
        raise ValueError('A valid analysis boundary is required')
    project = Transformer.from_crs('EPSG:4326', 'EPSG:6933', always_xy=True).transform
    region = transform(project, boundary_wgs84)
    west,south,east,north = region.bounds
    if not all(math.isfinite(v) for v in region.bounds):
        raise ValueError('Invalid projected boundary')
    c0,c1 = math.floor(west/1000),math.ceil(east/1000)
    r0,r1 = math.floor(south/1000),math.ceil(north/1000)
    if not 1 <= max_cells <= 50_000 or (c1-c0)*(r1-r0) > max_cells:
        raise ValueError('Analysis grid exceeds cell budget')
    rows = decoded.get('rows', [])
    if len(rows) > 50_000 or len({r['source_support_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate or excessive native supports')
    geometries = []
    for row in rows:
        bounds = row['bounds_wgs84']
        if len(bounds) != 4 or not all(math.isfinite(v) for v in bounds) or bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
            raise ValueError('Invalid native bounds')
        geometries.append(transform(project,box(*bounds)))
    tree = STRtree(geometries)
    output = []
    for r in range(r0,r1):
        for c in range(c0,c1):
            cell = box(c*1000,r*1000,(c+1)*1000,(r+1)*1000).intersection(region)
            if cell.area <= 0:
                continue
            samples = []
            covered_area = 0.0
            for index in tree.query(cell):
                area = cell.intersection(geometries[index]).area
                if area > 0:
                    row = rows[index]
                    samples.append((row['rainfall_mm'],area,row['source_support_id']))
                    covered_area += area
            if covered_area > cell.area * (1+1e-7):
                raise ValueError('Overlapping native source cells')
            # Unobserved parts remain part of the coverage denominator.
            samples.append((None,max(0,cell.area-covered_area),'outside_acquired_coverage'))
            result = aggregate_samples(samples)
            output.append({'cell_id':projected_cell(c*1000,r*1000).cell_id,'date':decoded['date'],
                'rainfall_mm':result['value'],'valid_fraction':result['valid_fraction'],
                'source_support_ids':result['source_support_ids'],
                'independent_support_count':result['independent_support_count'],
                'analysis_area_m2':cell.area,'native_support':'0.1 degree','grid_id':'bd-ea-1km-v1'})
    return output
