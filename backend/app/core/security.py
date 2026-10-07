
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings

ALGORITHM = "HS256"

# Long-lived tokens (90 days) so farmers don't get logged out frequently.
# Mobile farmers in rural areas shouldn't be forced to re-authenticate constantly.
ACCESS_TOKEN_EXPIRE_DAYS = 90


def create_access_token(farmer_id: UUID) -> str:
    """Create a signed JWT token that encodes the farmer's identity.

    The token contains:
      - 'sub': the farmer's UUID (who this token belongs to)
      - 'exp': expiry timestamp (90 days from now)

    The token is signed with SECRET_KEY so it cannot be forged.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(farmer_id),
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> UUID | None:
    """Decode a JWT and return the farmer_id UUID.

    Returns None (instead of raising) if the token is:
      - expired
      - tampered with / invalid signature
      - malformed
      - missing the 'sub' claim

    The caller (middleware) decides what to do with None.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        farmer_id_str: str | None = payload.get("sub")
        if not farmer_id_str:
            return None
        return UUID(farmer_id_str)
    except (InvalidTokenError, ValueError):
        return None
