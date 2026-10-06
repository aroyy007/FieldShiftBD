"""M2 source import tests leave crop ownership with Module 1."""

from copy import deepcopy
from datetime import date
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest

pytest.importorskip("sqlalchemy", reason="M2 source import tests require backend dependencies")

from app.models.core import AgriculturalKnowledge, Crop
from app.services.m2_source_import import (
    M2CropCatalogDependencyError,
    M2SourceImportConflict,
    import_barc_snapshot,
)


CROP_ID = UUID("33333333-3333-4333-8333-333333333333")


def source_snapshot():
    path = Path(__file__).resolve().parents[1] / "app" / "data" / "m2_knowledge_sources" / "barc_potato_comilla_snapshot.json"
    return json.loads(path.read_text(encoding="utf-8"))


class ImportSession:
    def __init__(self, crop=None, existing=None):
        self.crop = crop
        self.existing = existing
        self.added = []
        self.scalar_calls = 0

    def scalar(self, statement):
        entity = statement.column_descriptions[0]["entity"]
        if entity is Crop:
            return self.crop
        if entity is AgriculturalKnowledge:
            return self.existing
        return None

    def add(self, row):
        self.added.append(row)


def test_source_import_leaves_missing_m1_crop_catalog_entry_untouched():
    db = ImportSession()

    with pytest.raises(M2CropCatalogDependencyError, match="M1 crop catalog"):
        import_barc_snapshot(db, source_snapshot(), evaluated_on=date(2026, 10, 7))

    assert db.added == []


def test_source_import_is_idempotent_and_does_not_change_crop_catalog():
    crop = SimpleNamespace(id=CROP_ID, name="Potato")
    db = ImportSession(crop=crop)
    row, created = import_barc_snapshot(
        db, source_snapshot(), evaluated_on=date(2026, 10, 7)
    )
    assert created is True
    assert db.added == [row]
    assert crop.name == "Potato"

    db.existing = row
    refreshed, created_again = import_barc_snapshot(
        db, deepcopy(source_snapshot()), evaluated_on=date(2026, 10, 8)
    )

    assert refreshed is row
    assert created_again is False
    assert db.added == [row]


def test_source_import_will_not_overwrite_a_human_owned_record():
    crop = SimpleNamespace(id=CROP_ID, name="Potato")
    db = ImportSession(crop=crop)
    existing, _ = import_barc_snapshot(
        db, source_snapshot(), evaluated_on=date(2026, 10, 7)
    )
    existing.reviewed_by = uuid4()
    existing.reviewed_at = None
    db.existing = existing

    with pytest.raises(M2SourceImportConflict, match="left unchanged"):
        import_barc_snapshot(
            db, source_snapshot(), evaluated_on=date(2026, 10, 8)
        )

    assert existing.reviewed_by is not None
