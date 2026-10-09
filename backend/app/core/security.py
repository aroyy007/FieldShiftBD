
from datetime import datetime, timedelta, timezone
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
import jwt
from jwt.exceptions import InvalidTokenError

from app.core.config import settings

ALGORITHM = "HS256"

# Long-lived tokens (90 days) so farmers don't get logged out frequently.
# Mobile farmers in rural areas shouldn't be forced to re-authenticate constantly.
ACCESS_TOKEN_EXPIRE_DAYS = 90

# argon2-cffi defaults to Argon2id with a memory-hard work factor suitable for
# password storage. Hashes are versioned, salted, and self-describing.
_password_hasher = PasswordHasher()
_DUMMY_PASSWORD_HASH = _password_hasher.hash("FieldShift invalid account timing sentinel")


def hash_password(password: str) -> str:
    """Return an Argon2id hash; callers must never persist the raw password."""
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Verify a password, doing a dummy hash check for missing/invalid hashes."""
    candidate = password_hash or _DUMMY_PASSWORD_HASH
    try:
        verified = _password_hasher.verify(candidate, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False
    return bool(password_hash) and verified


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
