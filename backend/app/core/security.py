"""
SentinelX Security Utilities
Handles JWT creation/verification and bcrypt password hashing.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ─── Password Hashing ─────────────────────────────────────────────────────────
# rounds=10 → ~100ms per hash (still very secure, OWASP recommends ≥10).
# Default passlib rounds=12 → ~400ms, which on a cloud-latency path compounds
# to multiple seconds.  10 rounds provides 2^10 = 1024 iterations.
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=10,
)


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password using bcrypt (10 rounds)."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its bcrypt hash."""
    return pwd_context.verify(plain_password, hashed_password)


# ─── JWT Tokens ───────────────────────────────────────────────────────────────

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Payload to encode (must include 'sub').
        expires_delta: Custom expiry duration; defaults to settings value.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.

    Returns:
        Decoded payload dict, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None
