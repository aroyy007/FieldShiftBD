"""Explicit product pins and pilot geography; registration is not ingestion."""
import json
from pathlib import Path
from app.contracts.challenge.v2 import ProductDefinition, RegionDefinition

DATA = Path(__file__).resolve().parents[3] / 'data' / 'earth_observation'


def product_registry() -> dict[str, ProductDefinition]:
    return {p.product_id: p for p in (ProductDefinition.model_validate(x) for x in json.loads((DATA / 'products.json').read_text()))}


def region_registry() -> dict[str, RegionDefinition]:
    return {r.code: r for r in (RegionDefinition.model_validate(x) for x in json.loads((DATA / 'regions.json').read_text()))}
