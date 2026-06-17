"""
User Management Routes
GET    /users              — List users (SOC/admin scoped)
GET    /users/{id}         — Get a specific user
PATCH  /users/{id}/deactivate  — Deactivate a user
PATCH  /users/{id}/reactivate  — Reactivate a user
GET    /users/me/devices        — List my registered devices
POST   /users/me/devices        — Register a device
DELETE /users/me/devices/{id}   — Remove a device
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database.session import get_db
from app.database.models.models import User, UserRole
from app.api.dependencies.auth import get_current_user, require_role
from app.services.user_service import user_service
from app.schemas.schemas import UserResponse

logger = get_logger(__name__)

router = APIRouter(prefix="/users", tags=["User Management"])


# ─── Pydantic Schemas (local, lightweight) ───────────────────────────────────

class DeviceRegisterRequest(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=255)
    platform: str = Field(..., pattern="^(ios|android|web|desktop)$")
    device_token: Optional[str] = Field(default=None, max_length=512)


class DeviceResponse(BaseModel):
    id: uuid.UUID
    device_name: str
    platform: str
    is_active: bool
    created_at: str

    model_config = {"from_attributes": True}


# ─── User Management (SOC/Admin) ─────────────────────────────────────────────

@router.get(
    "",
    response_model=List[UserResponse],
    summary="List users in your organization",
)
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.soc, UserRole.sysadmin])),
) -> List[UserResponse]:
    """SOC admins see users in their org. Sysadmins see everyone."""
    return user_service.get_all_users(db, current_user, skip=skip, limit=limit)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a specific user by ID",
)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.soc, UserRole.sysadmin])),
) -> UserResponse:
    user = user_service.get_user_by_id(db, user_id, current_user)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    summary="Deactivate a user account",
)
def deactivate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.soc, UserRole.sysadmin])),
) -> UserResponse:
    user = user_service.deactivate_user(db, user_id, current_user)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}/reactivate",
    response_model=UserResponse,
    summary="Reactivate a deactivated user",
)
def reactivate_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.soc, UserRole.sysadmin])),
) -> UserResponse:
    user = user_service.reactivate_user(db, user_id, current_user)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserResponse.model_validate(user)


# ─── Device Management (User self-service) ───────────────────────────────────

@router.get(
    "/me/devices",
    summary="List devices registered to current user",
)
def list_my_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    devices = user_service.list_devices(db, current_user)
    return [
        {
            "id": str(d.id),
            "device_name": d.device_name,
            "platform": d.platform,
            "is_active": d.is_active,
            "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
            "created_at": d.created_at.isoformat(),
        }
        for d in devices
    ]


@router.post(
    "/me/devices",
    summary="Register a new device for push notifications",
    status_code=status.HTTP_201_CREATED,
)
def register_device(
    request: DeviceRegisterRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    device = user_service.register_device(
        db,
        current_user,
        device_name=request.device_name,
        platform=request.platform,
        device_token=request.device_token,
    )
    return {
        "id": str(device.id),
        "device_name": device.device_name,
        "platform": device.platform,
        "created_at": device.created_at.isoformat(),
    }


@router.delete(
    "/me/devices/{device_id}",
    summary="Remove a registered device",
)
def remove_device(
    device_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    removed = user_service.remove_device(db, device_id, current_user)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found or does not belong to you.",
        )
    return {"success": True, "message": "Device removed."}
