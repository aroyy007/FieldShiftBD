"""Response schemas for the M1 crop catalog."""

from uuid import UUID

from pydantic import BaseModel


class CropVarietyItem(BaseModel):
    crop_variety_id: UUID
    name: str
    description: str | None = None


class CropCatalogItem(BaseModel):
    crop_id: UUID
    name: str
    name_bn: str | None = None
    scientific_name: str | None = None
    catalog_key: str | None = None
    aliases: list[str] = []
    varieties: list[CropVarietyItem] = []
