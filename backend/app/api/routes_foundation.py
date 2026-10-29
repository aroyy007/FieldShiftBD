"""Safe, read-only status for the shared challenge foundation."""

from fastapi import APIRouter, Request

router = APIRouter(prefix="/challenge/foundation", tags=["Challenge foundation"])


@router.get("/availability")
def get_foundation_availability(request: Request):
    runtime = request.app.state.challenge_runtime
    return {
        "contract_version": "1.0.0",
        "offline_mode": runtime.offline_mode,
        "features": runtime.availability(),
    }
