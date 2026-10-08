"""Module 1 — crop catalog and profile reference data (read-only).

  GET /crops                         Crop catalog with aliases and varieties
  GET /crops/{crop_id}               One crop with its varieties
  GET /reference/locations           Division → district → upazila (BBS geocodes)
  GET /reference/profile-vocabulary  Soil textures, land types, area units

The catalog rows are seeded by ``python -m scripts.import_reference_data``.
These responses contain identifiers and names only, never agronomic claims,
so they are readable without a farmer session.
"""

import re
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.core import Crop, CropVariety
from app.schemas.catalog import CropCatalogItem, CropVarietyItem
from app.services.m1_reference import crop_definition, crop_key_for_name, location_reference, vocabulary

router = APIRouter(tags=["Crop Catalog & Reference — Module 1"])
DbSession = Annotated[Session, Depends(get_db)]


def _natural_key(name: str) -> list:
    """Sort "BARI Alu-7" before "BARI Alu-13"."""
    return [int(part) if part.isdigit() else part.casefold() for part in re.split(r"(\d+)", name)]


def _catalog_item(crop: Crop, varieties: list[CropVariety]) -> CropCatalogItem:
    key = crop_key_for_name(crop.name)
    definition = crop_definition(key) if key else None
    return CropCatalogItem(
        crop_id=crop.id,
        name=crop.name,
        name_bn=definition["name_bn"] if definition else None,
        scientific_name=crop.scientific_name,
        catalog_key=key,
        aliases=list(definition["aliases"]) if definition else [],
        varieties=[
            CropVarietyItem(crop_variety_id=variety.id, name=variety.name, description=variety.description)
            for variety in sorted(varieties, key=lambda item: _natural_key(item.name))
        ],
    )


@router.get("/crops", response_model=list[CropCatalogItem], summary="List the crop catalog")
def list_crops(db: DbSession) -> list[CropCatalogItem]:
    crops = list(db.scalars(select(Crop).order_by(Crop.name)))
    varieties = list(db.scalars(select(CropVariety)))
    by_crop: dict[UUID, list[CropVariety]] = {}
    for variety in varieties:
        by_crop.setdefault(variety.crop_id, []).append(variety)
    return [_catalog_item(crop, by_crop.get(crop.id, [])) for crop in crops]


@router.get("/crops/{crop_id}", response_model=CropCatalogItem, summary="Get one crop")
def get_crop(crop_id: UUID, db: DbSession) -> CropCatalogItem:
    crop = db.get(Crop, crop_id)
    if crop is None:
        raise HTTPException(status_code=404, detail="Crop not found")
    varieties = list(db.scalars(select(CropVariety).where(CropVariety.crop_id == crop.id)))
    return _catalog_item(crop, varieties)


@router.get("/reference/locations", summary="Bangladesh divisions, districts, and upazilas")
def get_locations() -> list[dict]:
    return location_reference()


@router.get("/reference/profile-vocabulary", summary="Canonical farm-profile vocabularies")
def get_profile_vocabulary() -> dict:
    data = vocabulary()
    return {
        "soil_textures": data["soil_textures"],
        "land_types": data["land_types"],
        "area_units": data["area_units"],
    }
