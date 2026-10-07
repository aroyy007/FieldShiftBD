from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer

# This single line tells Swagger UI to show the green "Authorize" button!
http_bearer = HTTPBearer(auto_error=False)


def get_current_farmer_id(request: Request, _token=Depends(http_bearer)) -> UUID:
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
