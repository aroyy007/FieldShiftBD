"""Read existing validated POWER point bundles; never imply area coverage."""
from pathlib import Path
from app.services.climate.cache import ClimateBundleCache, CorruptClimateCache
from app.contracts.challenge.ports import ArtifactNotFound, AdapterConflict, StaleArtifact
from app.services.earth_observation.registry import product_registry, region_registry


def load_power_context(root: Path, district_code: str):
    if district_code not in region_registry():
        return None, 'missing'
    try:
        bundle = ClimateBundleCache(root).load_bundle(district_code)
        if (not bundle.manifest.sampling_point or bundle.manifest.quality_status == 'synthetic'
                or not any(p.method == 'nasa_power' for p in bundle.manifest.provenance)
                or any(p.quality_status in {'synthetic', 'unavailable', 'stale'} for p in bundle.manifest.provenance)):
            return None, 'corrupt'
        return bundle, 'hit'
    except ArtifactNotFound:
        return None, 'missing'
    except (OSError, ValueError, CorruptClimateCache, AdapterConflict, StaleArtifact):
        return None, 'corrupt'


def inventory(root: Path) -> dict:
    regions = []
    for region in region_registry().values():
        bundle, state = load_power_context(root, region.code)
        regions.append({**region.model_dump(), 'power_cache_status': state,
                        'coverage_start': str(bundle.manifest.coverage_start) if bundle else None,
                        'coverage_end': str(bundle.manifest.coverage_end) if bundle else None,
                        'scope': 'reference_point' if bundle else None})
    return {'contract_version': '2.0.0', 'regions': regions,
            'products': [{**p.model_dump(), 'state': 'existing_point_cache' if p.product_id == 'power' and any(r['power_cache_status'] == 'hit' for r in regions) else 'not_acquired'} for p in product_registry().values()]}
