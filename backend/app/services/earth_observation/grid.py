"""Stable equal-area analysis cell identity; posting is not sensor accuracy."""
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisCell:
    column: int
    row: int
    cell_id: str
    crs: str = 'EPSG:6933'
    size_m: int = 1000


def projected_cell(x: float, y: float) -> AnalysisCell:
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError('Projected coordinates must be finite')
    col, row = math.floor(x / 1000), math.floor(y / 1000)
    return AnalysisCell(col, row, f'bd-ea-1km-v1:{col}:{row}')


def resolve_analysis_cell(lon: float, lat: float, *, boundary) -> AnalysisCell:
    """Geo-worker seam: boundary is a verified WGS84 shapely district geometry."""
    if not math.isfinite(lon) or not math.isfinite(lat) or not -180 <= lon <= 180 or not -86 <= lat <= 86:
        raise ValueError('Invalid coordinates for EPSG:6933')
    from pyproj import Transformer
    from shapely.geometry import Point
    if not boundary.is_valid or boundary.is_empty or not boundary.covers(Point(lon, lat)):
        raise ValueError('Location is outside the valid district boundary')
    x, y = Transformer.from_crs('EPSG:4326', 'EPSG:6933', always_xy=True).transform(lon, lat)
    return projected_cell(x, y)
