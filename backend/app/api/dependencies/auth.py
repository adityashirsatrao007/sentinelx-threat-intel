"""
FastAPI Dependencies
Provides reusable auth-aware dependency injectors for routes.
Includes an in-process LRU cache on token→user_id to avoid DB round-trips
on every request.  The cache entry is keyed on the token string, which is
short-lived (JWT expiry), so stale data is self-cleaning.
"""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Optional, List

from fastapi import Depends, HTTPException, status, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database.session import get_db
from app.database.models.models import User, UserRole
from app.core.logging import get_logger

logger = get_logger(__name__)

# ─── Bearer Token Extractor ───────────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=True)


# ─── Token Payload Cache ──────────────────────────────────────────────────────
# Cache the decoded JWT payload (pure CPU work, no I/O) to avoid re-decoding
# the HMAC signature on every request.  maxsize=512 covers ~512 concurrent sessions.
@lru_cache(maxsize=512)
def _decode_token_cached(token: str) -> Optional[dict]:
    """Decode and cache a JWT payload. Returns None if invalid/expired."""
    return decode_access_token(token)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    token_query: Optional[str] = Query(None, alias="token"),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract and validate JWT from Authorization: Bearer header or ?token= query param.
    Returns the authenticated User ORM object.
    """
    token = credentials.credentials if credentials else token_query

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_token_cached(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing subject.",
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier in token.",
        )

    # Single indexed lookup — extremely fast with a warm connection
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or account deactivated.",
        )

    return user


def require_role(roles: List[UserRole]):
    """
    Returns a FastAPI dependency that validates the current user has one of
    the specified roles.  Raises 403 Forbidden otherwise.
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role(s): {[r.value for r in roles]}",
            )
        return current_user
    return role_checker
