from uuid import UUID

from fastapi import HTTPException, Request, status


def get_current_farmer_id(request: Request) -> UUID:
    """Read the verified farmer identity installed by the authentication layer."""
    farmer_id = getattr(request.state, "current_farmer_id", None)
    if isinstance(farmer_id, UUID):
        return farmer_id
    if isinstance(farmer_id, str):
        try:
            return UUID(farmer_id)
        except ValueError:
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
