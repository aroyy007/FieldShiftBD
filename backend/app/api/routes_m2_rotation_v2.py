"""Owned, read-only regional evidence comparison endpoints."""
from pathlib import Path
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.auth import get_current_farmer_id
from app.core.database import get_db
from app.core.config import settings
from app.contracts.challenge.v2 import RotationCompareRequest, RotationComparisonV2
from app.services.earth_observation.provider import inventory
from app.services.profile_intake.snapshot import DatabaseFarmProfileSnapshotReader, FarmSnapshotNotFound
from app.services.rotation.service import compare_rotations

router = APIRouter(prefix='/advisor/v2', tags=['Regional rotation evidence'])


@router.get('/regions')
def regions(response: Response):
    response.headers['Cache-Control'] = 'no-store'
    return inventory(Path(settings.CLIMATE_CACHE_DIR))


@router.post('/farmlands/{farmland_id}/rotation-comparisons', response_model=RotationComparisonV2)
def compare(farmland_id: UUID, body: RotationCompareRequest, response: Response,
            farmer_id: UUID = Depends(get_current_farmer_id), db: Session = Depends(get_db)):
    response.headers['Cache-Control'] = 'no-store'
    try:
        snapshot = DatabaseFarmProfileSnapshotReader(db).get_snapshot(farmer_id, farmland_id)
    except FarmSnapshotNotFound as error:
        raise HTTPException(status_code=404, detail='Farmland not found') from error
    return compare_rotations(snapshot, body, Path(settings.CLIMATE_CACHE_DIR), Path(settings.EO_PILOT_DIR))
