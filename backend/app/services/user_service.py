"""
User Management Service
Admin/SOC-level operations for managing users within an organization.
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database.models.models import Device, EmailAccount, User, UserRole
from app.schemas.schemas import UserResponse

logger = get_logger(__name__)


class UserService:

    def get_all_users(
        self, db: Session, requesting_user: User, skip: int = 0, limit: int = 100
    ) -> List[UserResponse]:
        """
        Admin/SOC-scoped user listing.
        - sysadmin: sees all users
        - soc:      sees only users in their org
        """
        query = db.query(User)
        if requesting_user.role != UserRole.sysadmin:
            query = query.filter(User.organization_id == requesting_user.organization_id)

        users = query.order_by(User.created_at.desc()).offset(skip).limit(limit).all()
        result = []
        for u in users:
            try:
                result.append(UserResponse.model_validate(u))
            except Exception as e:
                logger.warning(f"Skipping user {u.email} due to invalid data: {e}")
        return result

    def get_user_by_id(
        self, db: Session, user_id: uuid.UUID, requesting_user: User
    ) -> Optional[User]:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return None
        # Scope check: soc can only see their own org
        if requesting_user.role not in (UserRole.sysadmin,):
            if user.organization_id != requesting_user.organization_id:
                return None
        return user

    def deactivate_user(
        self, db: Session, user_id: uuid.UUID, requesting_user: User
    ) -> Optional[User]:
        user = self.get_user_by_id(db, user_id, requesting_user)
        if not user:
            return None
        user.is_active = False
        db.commit()
        db.refresh(user)
        logger.info(f"User {user.email} deactivated by {requesting_user.email}")
        return user

    def reactivate_user(
        self, db: Session, user_id: uuid.UUID, requesting_user: User
    ) -> Optional[User]:
        user = self.get_user_by_id(db, user_id, requesting_user)
        if not user:
            return None
        user.is_active = True
        db.commit()
        db.refresh(user)
        logger.info(f"User {user.email} reactivated by {requesting_user.email}")
        return user

    def register_device(
        self,
        db: Session,
        user: User,
        device_name: str,
        platform: str,
        device_token: Optional[str] = None,
    ) -> Device:
        """Register or update a device for a user."""
        # Upsert by device_token if provided
        existing = None
        if device_token:
            existing = db.query(Device).filter(Device.device_token == device_token).first()

        if existing:
            existing.device_name = device_name
            existing.platform = platform
            existing.is_active = True
            db.commit()
            db.refresh(existing)
            return existing

        device = Device(
            user_id=user.id,
            device_name=device_name,
            platform=platform,
            device_token=device_token,
        )
        db.add(device)
        db.commit()
        db.refresh(device)
        logger.info(f"Device '{device_name}' registered for user {user.email}")
        return device

    def list_devices(self, db: Session, user: User) -> List[Device]:
        return db.query(Device).filter(Device.user_id == user.id, Device.is_active).all()

    def remove_device(self, db: Session, device_id: uuid.UUID, user: User) -> bool:
        device = db.query(Device).filter(Device.id == device_id, Device.user_id == user.id).first()
        if not device:
            return False
        device.is_active = False
        db.commit()
        logger.info(f"Device {device_id} removed for user {user.email}")
        return True

    def list_email_accounts(self, db: Session, user: User) -> List[EmailAccount]:
        return (
            db.query(EmailAccount)
            .filter(EmailAccount.user_id == user.id, EmailAccount.is_active)
            .all()
        )

    def disconnect_email_account(
        self, db: Session, account_id: uuid.UUID, user: User
    ) -> bool:
        account = (
            db.query(EmailAccount)
            .filter(EmailAccount.id == account_id, EmailAccount.user_id == user.id)
            .first()
        )
        if not account:
            return False
        account.is_active = False
        db.commit()
        logger.info(f"Email account {account.email_address} disconnected for user {user.email}")
        return True


user_service = UserService()
