from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.challenge.v1 import (
    CONTRACT_VERSION,
    CropPriority,
    FarmProfileSnapshot,
    FarmlandProfile,
    RotationHistoryEntry,
    SeasonSnapshot,
    SourceProvenance,
)
from app.core.time_utils import to_utc
from app.models import (
    Crop,
    Farmland,
    FarmlandCropPreference,
    GrowthStage,
    Season,
)


class FarmSnapshotNotFound(LookupError):
    """The farm is absent or is not visible to the requested farmer."""


class DatabaseFarmProfileSnapshotReader:
    """Read a farmer-scoped M1/M3 context snapshot without committing state."""

    def __init__(
        self,
        session: Session,
        *,
        clock: Callable[[], datetime] | None = None,
        district_code_resolver: Callable[[str | None], str | None] | None = None,
    ) -> None:
        self._session = session
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._district_code_resolver = district_code_resolver or (lambda _district: None)

    def get_snapshot(self, farmer_id: UUID, farmland_id: UUID) -> FarmProfileSnapshot:
        farmland = self._session.scalar(
            select(Farmland).where(
                Farmland.id == farmland_id,
                Farmland.farmer_id == farmer_id,
            )
        )
        if farmland is None:
            raise FarmSnapshotNotFound("farm was not found for this farmer")

        active_season = self._session.scalar(
            select(Season).where(
                Season.farmland_id == farmland.id,
                Season.status == "active",
            )
        )
        now = to_utc(self._clock())
        season_snapshot = self._read_season(active_season, now) if active_season else None
        priorities = self._read_priorities(farmland.id)
        rotation_history = self._read_rotation_history(farmland.id, active_season.id if active_season else None)
        recorded_at = to_utc(farmland.updated_at or farmland.created_at or now)
        provenance = SourceProvenance(
            source_id=f"fieldshift:farmland:{farmland.id}",
            source_name="Farmer-entered farm profile and recorded crop seasons",
            retrieved_at=now,
            recorded_at=recorded_at,
            method="farmer_input",
            quality_status="provisional",
        )

        return FarmProfileSnapshot(
            contract_version=CONTRACT_VERSION,
            farmland_id=farmland.id,
            farmer_id=farmland.farmer_id,
            captured_at=now,
            profile=FarmlandProfile(
                country_code=farmland.country_code,
                division=farmland.division,
                district=farmland.district,
                district_code=self._district_code_resolver(farmland.district),
                upazila=farmland.upazila,
                village_or_locality=farmland.village_or_locality,
                latitude=float(farmland.latitude) if farmland.latitude is not None else None,
                longitude=float(farmland.longitude) if farmland.longitude is not None else None,
                land_area_sqm=float(farmland.land_area_sqm),
                area_unit=farmland.land_area_display_unit,
                soil_type=farmland.soil_type,
                land_type=farmland.land_type,
                irrigation_available=farmland.irrigation_available,
                water_source=farmland.water_source,
                equipment=list(farmland.equipment or []),
                budget_amount=float(farmland.budget_amount) if farmland.budget_amount is not None else None,
                budget_currency=farmland.budget_currency,
            ),
            active_season=season_snapshot,
            crop_priorities=priorities,
            rotation_history=rotation_history,
            provenance=[provenance],
        )

    def _read_season(self, season: Season, captured_at: datetime) -> SeasonSnapshot:
        crop = self._session.get(Crop, season.crop_id)
        stage = (
            self._session.get(GrowthStage, season.current_growth_stage_id)
            if season.current_growth_stage_id
            else None
        )
        return SeasonSnapshot(
            season_id=season.id,
            crop_id=season.crop_id,
            crop_code=crop.name if crop else None,
            variety_id=season.crop_variety_id,
            variety_name=season.variety_name,
            status=season.status,
            planting_date=season.planting_date,
            expected_harvest_date=season.expected_harvest_date,
            current_growth_stage_id=stage.id if stage else None,
            current_growth_stage_name=stage.name if stage else None,
            growth_stage_as_of=captured_at.date() if stage else None,
        )

    def _read_priorities(self, farmland_id: UUID) -> list[CropPriority]:
        rows = self._session.execute(
            select(FarmlandCropPreference, Crop.name)
            .join(Crop, Crop.id == FarmlandCropPreference.crop_id)
            .where(FarmlandCropPreference.farmland_id == farmland_id)
            .order_by(FarmlandCropPreference.preference_rank.asc())
        ).all()
        return [
            CropPriority(
                crop_code=name,
                rank=preference.preference_rank,
                reason=preference.notes,
            )
            for preference, name in rows
        ]

    def _read_rotation_history(
        self, farmland_id: UUID, active_season_id: UUID | None
    ) -> list[RotationHistoryEntry]:
        query = (
            select(Season, Crop.name)
            .join(Crop, Crop.id == Season.crop_id)
            .where(
                Season.farmland_id == farmland_id,
                Season.status == "completed",
            )
            .order_by(Season.actual_harvest_date.desc(), Season.planting_date.desc())
            .limit(20)
        )
        if active_season_id is not None:
            query = query.where(Season.id != active_season_id)
        rows = self._session.execute(query).all()
        return [
            RotationHistoryEntry(
                season_id=season.id,
                crop_code=crop_name,
                planting_date=season.planting_date,
                harvest_date=season.actual_harvest_date,
                yield_amount=float(season.actual_yield) if season.actual_yield is not None else None,
                yield_unit=season.yield_unit,
                source="recorded_plan",
            )
            for season, crop_name in rows
        ]
