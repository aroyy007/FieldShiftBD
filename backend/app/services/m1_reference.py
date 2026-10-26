"""M1 reference vocabularies: soil texture, land type, geography, and crop aliases.

These canonical identifiers are shared by M1 profile writes, M2 knowledge
conditions, and frontend pickers. They are classification data only and carry
no agronomic claims.
"""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
VOCABULARY_PATH = DATA_DIR / "m1_profile_vocabulary.json"
GEOGRAPHY_PATH = DATA_DIR / "m1_geography_bd.json"
CROP_CATALOG_PATH = DATA_DIR / "m1_crop_catalog.json"
SUITABILITY_CAPTURE_DIR = DATA_DIR / "source_captures" / "barc_crop_zoning" / "suitability"

LAND_TYPE_CODES = ("high", "medium_high", "medium_low", "low", "very_low")


class ReferenceDataError(ValueError):
    """A profile value conflicts with the canonical reference data."""


def normalize_text(value: Any) -> str:
    """Return a comparison key that tolerates case, spacing, and Bangla spelling variants."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFC", str(value)).casefold().strip()
    text = text.replace("ঁ", "")  # chandrabindu: আঁশ / আশ
    text = text.replace("ী", "ি").replace("ূ", "ু")
    text = text.replace("ঁ", "")
    text = re.sub(r"[\-‐-―_'’.]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _strip_suffix(key: str) -> str:
    return re.sub(r"\s+(soil|মাটি|land|জমি)$", "", key).strip()


@lru_cache(maxsize=1)
def vocabulary() -> dict[str, Any]:
    return json.loads(VOCABULARY_PATH.read_text(encoding="utf-8"))


def _term_index(kind: str) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for item in vocabulary()[kind]:
        for term in (item["code"], item["label_en"], item["label_bn"], *item.get("aliases", [])):
            index[normalize_text(term)] = item
            index[_strip_suffix(normalize_text(term))] = item
    return index


@lru_cache(maxsize=1)
def _soil_index() -> dict[str, dict[str, Any]]:
    return _term_index("soil_textures")


@lru_cache(maxsize=1)
def _land_index() -> dict[str, dict[str, Any]]:
    return _term_index("land_types")


def soil_texture(value: Any) -> dict[str, Any] | None:
    key = normalize_text(value)
    if not key:
        return None
    return _soil_index().get(key) or _soil_index().get(_strip_suffix(key))


def soil_texture_code(value: Any) -> str | None:
    item = soil_texture(value)
    return item["code"] if item else None


def land_type(value: Any) -> dict[str, Any] | None:
    key = normalize_text(value)
    if not key:
        return None
    return _land_index().get(key) or _land_index().get(_strip_suffix(key))


def land_type_code(value: Any) -> str | None:
    item = land_type(value)
    return item["code"] if item else None


def canonical_soil_label(value: str | None) -> str | None:
    """Store recognized soil textures by their canonical English label; keep other text."""
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    item = soil_texture(stripped)
    return item["label_en"] if item else stripped


def canonical_land_type(value: str | None) -> str | None:
    """Return the canonical land-type code or raise for an unknown non-empty value."""
    if value is None or not str(value).strip():
        return None
    code = land_type_code(value)
    if code is None:
        raise ReferenceDataError(
            "land_type must be one of: " + ", ".join(LAND_TYPE_CODES)
        )
    return code


# ── Geography ────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class District:
    code: str
    name: str
    name_bn: str
    division_code: str
    aliases: tuple[str, ...] = ()
    upazilas: tuple["Upazila", ...] = ()


@dataclass(frozen=True)
class Upazila:
    code: str
    name: str
    name_bn: str
    district_code: str


@dataclass(frozen=True)
class Geography:
    divisions: dict[str, dict[str, Any]]
    districts: dict[str, District]
    division_index: dict[str, str]
    district_index: dict[str, str]
    upazila_index: dict[tuple[str, str], str]
    upazilas: dict[str, Upazila]


@lru_cache(maxsize=1)
def geography() -> Geography:
    config = json.loads(GEOGRAPHY_PATH.read_text(encoding="utf-8"))
    divisions = {item["code"]: item for item in config["divisions"]}
    division_index: dict[str, str] = {}
    for item in config["divisions"]:
        for term in (item["code"], item["name"], item["name_bn"], *item["aliases"]):
            division_index[normalize_text(term)] = item["code"]

    raw_districts = json.loads((SUITABILITY_CAPTURE_DIR / "districts.json").read_text(encoding="utf-8"))
    districts: dict[str, District] = {}
    district_index: dict[str, str] = {}
    upazila_index: dict[tuple[str, str], str] = {}
    upazilas: dict[str, Upazila] = {}
    aliases = config.get("district_aliases", {})
    for raw in raw_districts:
        code = str(int(raw["district_c"]))
        division_code = code[:2]
        if division_code not in divisions:
            raise ReferenceDataError(f"District {code} has an unknown division prefix")
        upazila_file = SUITABILITY_CAPTURE_DIR / f"upazilas_{code}.json"
        district_upazilas = []
        if upazila_file.exists():
            for row in json.loads(upazila_file.read_text(encoding="utf-8")):
                upazila = Upazila(
                    code=str(int(row["upazila_code"])),
                    name=str(row["thana_name"]).strip(),
                    name_bn=str(row.get("upz_name_bn") or "").strip(),
                    district_code=code,
                )
                district_upazilas.append(upazila)
                upazilas[upazila.code] = upazila
                for term in (upazila.code, upazila.name, upazila.name_bn):
                    if term:
                        upazila_index[(code, normalize_text(term))] = upazila.code
        district = District(
            code=code,
            name=str(raw["district_n"]).strip(),
            name_bn=str(raw.get("dist_name_bn") or "").strip(),
            division_code=division_code,
            aliases=tuple(aliases.get(code, [])),
            upazilas=tuple(sorted(district_upazilas, key=lambda item: item.name)),
        )
        districts[code] = district
        for term in (code, district.name, district.name_bn, *district.aliases):
            if term:
                district_index[normalize_text(term)] = code
    return Geography(divisions, districts, division_index, district_index, upazila_index, upazilas)


@dataclass(frozen=True)
class ResolvedLocation:
    country_code: str = "BD"
    division: str | None = None
    district: str | None = None
    upazila: str | None = None
    division_code: str | None = None
    district_code: str | None = None
    upazila_code: str | None = None
    notes: tuple[str, ...] = field(default_factory=tuple)

    def region_codes(self) -> set[str]:
        codes = {self.country_code} if self.country_code else set()
        if self.division_code:
            codes.add(f"BD-DIV-{self.division_code}")
        if self.district_code:
            codes.add(f"BD-DIST-{self.district_code}")
        if self.upazila_code:
            codes.add(f"BD-UPZ-{self.upazila_code}")
        return codes


def resolve_location(
    division: str | None, district: str | None, upazila: str | None, country_code: str | None = "BD"
) -> ResolvedLocation:
    """Map typed or aliased names to canonical BBS-coded names.

    Unknown names are kept as typed (without a code). A division that conflicts
    with the district's BBS division raises ``ReferenceDataError``.
    """
    country = (country_code or "BD").strip().upper()
    if country != "BD":
        return ResolvedLocation(country_code=country, division=division, district=district, upazila=upazila)
    geo = geography()
    notes: list[str] = []
    division_code = geo.division_index.get(normalize_text(division)) if division else None
    district_code = geo.district_index.get(normalize_text(district)) if district else None
    if district and district_code is None:
        notes.append("district_not_in_reference")
    if district_code is not None:
        district_division = geo.districts[district_code].division_code
        if division_code is not None and division_code != district_division:
            raise ReferenceDataError(
                f"{geo.districts[district_code].name} district is in "
                f"{geo.divisions[district_division]['name']} division, not "
                f"{geo.divisions[division_code]['name']}."
            )
        division_code = district_division
    if division and division_code is None:
        notes.append("division_not_in_reference")
    upazila_code = None
    if upazila and district_code is not None:
        upazila_code = geo.upazila_index.get((district_code, normalize_text(upazila)))
        if upazila_code is None:
            notes.append("upazila_not_in_reference")
    elif upazila:
        notes.append("upazila_without_known_district")
    return ResolvedLocation(
        country_code="BD",
        division=geo.divisions[division_code]["name"] if division_code else (division.strip() if division else None),
        district=geo.districts[district_code].name if district_code else (district.strip() if district else None),
        upazila=geo.upazilas[upazila_code].name if upazila_code else (upazila.strip() if upazila else None),
        division_code=division_code,
        district_code=district_code,
        upazila_code=upazila_code,
        notes=tuple(notes),
    )


def location_reference() -> list[dict[str, Any]]:
    geo = geography()
    result = []
    for code, division in sorted(geo.divisions.items(), key=lambda item: item[1]["name"]):
        result.append({
            "code": code,
            "region_code": f"BD-DIV-{code}",
            "name": division["name"],
            "name_bn": division["name_bn"],
            "districts": [
                {
                    "code": district.code,
                    "region_code": f"BD-DIST-{district.code}",
                    "name": district.name,
                    "name_bn": district.name_bn,
                    "aliases": list(district.aliases),
                    "upazilas": [
                        {
                            "code": upazila.code,
                            "region_code": f"BD-UPZ-{upazila.code}",
                            "name": upazila.name,
                            "name_bn": upazila.name_bn,
                        }
                        for upazila in district.upazilas
                    ],
                }
                for district in sorted(geo.districts.values(), key=lambda item: item.name)
                if district.division_code == code
            ],
        })
    return result


# ── Crop catalog aliases ─────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def crop_catalog() -> dict[str, Any]:
    return json.loads(CROP_CATALOG_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _crop_alias_index() -> dict[str, str]:
    index: dict[str, str] = {}
    for crop in crop_catalog()["crops"]:
        for term in (crop["key"], crop["name"], crop["name_bn"], *crop["aliases"]):
            key = normalize_text(term)
            existing = index.get(key)
            if existing is not None and existing != crop["key"]:
                raise ReferenceDataError(f"Crop alias {term!r} is ambiguous")
            index[key] = crop["key"]
    return index


def crop_key_for_name(name: Any) -> str | None:
    """Resolve a crop display name or alias to its catalog key."""
    return _crop_alias_index().get(normalize_text(name))


def crop_definition(key: str) -> dict[str, Any] | None:
    return next((crop for crop in crop_catalog()["crops"] if crop["key"] == key), None)


def normalize_variety_name(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip()
