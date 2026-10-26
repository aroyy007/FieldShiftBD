"""Idempotent import of the M1 crop and variety catalog.

Rows created by this importer use deterministic UUIDs, so repeated runs bind to
the same identifiers. Rows created by anyone else are matched by name or alias
and preserved as-is: the importer never renames, deletes, or rewrites them. A
catalog crop that matches more than one existing row, or whose deterministic ID
is used by an unrelated row, is reported as a conflict and skipped.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import NAMESPACE_URL, UUID, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.core import Crop, CropVariety
from app.services.m1_reference import crop_catalog, crop_key_for_name, normalize_text, normalize_variety_name
from app.services.source_captures import read_verified_json

CATALOG_DESCRIPTION = "M1 reference crop catalog entry (app/data/m1_crop_catalog.json)."


def crop_row_id(key: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"https://fieldshiftbd.local/m1/crop/{key}")


def variety_row_id(crop_key: str, variety_name: str) -> UUID:
    return uuid5(NAMESPACE_URL, f"https://fieldshiftbd.local/m1/crop/{crop_key}/variety/{normalize_text(variety_name)}")


@dataclass
class CatalogImportReport:
    crops_created: int = 0
    crops_updated: int = 0
    crops_unchanged: int = 0
    crops_preserved: int = 0
    varieties_created: int = 0
    varieties_updated: int = 0
    varieties_unchanged: int = 0
    varieties_preserved: int = 0
    conflicts: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    crop_ids: dict[str, UUID] = field(default_factory=dict)
    # (crop key, portal variety id) -> crop_varieties.id
    variety_ids: dict[tuple[str, int], UUID] = field(default_factory=dict)


def _portal_varieties(crop: dict) -> list[tuple[int, str, int]]:
    """Return (portal variety id, official name, portal crop id) deduplicated by name."""
    seen: dict[str, tuple[int, str, int]] = {}
    for portal_crop_id in crop["portal_crop_ids"]:
        for row in read_verified_json(f"portal/variety_names_{portal_crop_id}.json"):
            name = normalize_variety_name(str(row["name"]))
            key = normalize_text(name)
            if name and key not in seen:
                seen[key] = (int(row["id"]), name, portal_crop_id)
    return list(seen.values())


def _variety_description(portal_variety_id: int, portal_crop_id: int) -> str:
    return (
        "Official variety name from the BARC Agri-Advisory Portal "
        f"(variety record {portal_variety_id}, portal crop {portal_crop_id})."
    )


def import_crop_catalog(db: Session) -> CatalogImportReport:
    report = CatalogImportReport()
    existing_crops = list(db.scalars(select(Crop)))
    for definition in crop_catalog()["crops"]:
        key = definition["key"]
        own_id = crop_row_id(key)
        matches = [row for row in existing_crops if crop_key_for_name(row.name) == key]
        id_holder = next((row for row in existing_crops if row.id == own_id), None)
        if id_holder is not None and id_holder not in matches:
            report.conflicts.append(
                f"crop {key}: deterministic id {own_id} belongs to unrelated crop {id_holder.name!r}; skipped"
            )
            continue
        if len(matches) > 1:
            names = ", ".join(sorted(repr(row.name) for row in matches))
            report.conflicts.append(f"crop {key}: several existing rows match its aliases ({names}); skipped")
            continue
        if not matches:
            crop = Crop(
                id=own_id,
                name=definition["name"],
                scientific_name=definition["scientific_name"],
                description=CATALOG_DESCRIPTION,
            )
            db.add(crop)
            db.flush()
            existing_crops.append(crop)
            report.crops_created += 1
        else:
            crop = matches[0]
            if crop.id == own_id:
                changed = False
                for attr, value in (
                    ("name", definition["name"]),
                    ("scientific_name", definition["scientific_name"]),
                    ("description", CATALOG_DESCRIPTION),
                ):
                    if getattr(crop, attr) != value:
                        setattr(crop, attr, value)
                        changed = True
                report.crops_updated += int(changed)
                report.crops_unchanged += int(not changed)
            else:
                report.crops_preserved += 1
                if crop.scientific_name and crop.scientific_name != definition["scientific_name"]:
                    report.conflicts.append(
                        f"crop {key}: existing row {crop.name!r} has scientific name "
                        f"{crop.scientific_name!r}, catalog says {definition['scientific_name']!r}; row left unchanged"
                    )
                elif crop.name != definition["name"]:
                    report.notes.append(
                        f"crop {key}: bound to existing row {crop.name!r} ({crop.id}) by alias; name left unchanged"
                    )
        report.crop_ids[key] = crop.id
        _import_varieties(db, definition, crop, report)
    db.flush()
    return report


def _import_varieties(db: Session, definition: dict, crop: Crop, report: CatalogImportReport) -> None:
    key = definition["key"]
    existing = {normalize_text(row.name): row for row in db.scalars(
        select(CropVariety).where(CropVariety.crop_id == crop.id)
    )}
    for portal_variety_id, name, portal_crop_id in _portal_varieties(definition):
        own_id = variety_row_id(key, name)
        description = _variety_description(portal_variety_id, portal_crop_id)
        row = existing.get(normalize_text(name))
        if row is None:
            holder = db.get(CropVariety, own_id)
            if holder is not None:
                report.conflicts.append(
                    f"variety {name!r}: deterministic id belongs to another row ({holder.name!r}); skipped"
                )
                continue
            row = CropVariety(id=own_id, crop_id=crop.id, name=name, description=description)
            db.add(row)
            existing[normalize_text(name)] = row
            report.varieties_created += 1
        elif row.id == own_id:
            if row.description != description or row.name != name:
                row.description = description
                row.name = name
                report.varieties_updated += 1
            else:
                report.varieties_unchanged += 1
        else:
            report.varieties_preserved += 1
        report.variety_ids[(key, portal_variety_id)] = row.id
