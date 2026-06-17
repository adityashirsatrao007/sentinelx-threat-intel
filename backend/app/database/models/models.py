"""
Database ORM Models
Defines User, Threat, Alert, and AuditLog tables.
"""

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    JSON,
    String,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── Enums ────────────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    sysadmin = "sysadmin"
    soc = "soc"
    operator = "operator"
    user = "user"


class ThreatType(str, enum.Enum):
    email = "email"
    sms = "sms"
    call = "call"
    message = "message"


class ThreatLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    high = "high"
    critical = "critical"


# ─── Organization ─────────────────────────────────────────────────────────────

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    
    users = relationship("User", back_populates="organization", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Organization id={self.id} name={self.name}>"

# ─── User ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # nullable for Google OAuth users
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    picture = Column(String(500), nullable=True)
    role = Column(SAEnum(UserRole), default=UserRole.user, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="users")
    threats = relationship("Threat", back_populates="created_by_user", lazy="dynamic")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="dynamic")
    email_accounts = relationship("EmailAccount", back_populates="user", lazy="dynamic")
    devices = relationship("Device", back_populates="user", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"


# ─── Threat ───────────────────────────────────────────────────────────────────

class Threat(Base):
    __tablename__ = "threats"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(SAEnum(ThreatType), nullable=False, index=True)
    channel = Column(String(50), nullable=False, index=True)  # email / sms / call / message
    content = Column(Text, nullable=True)          # sanitized excerpt
    sender = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=True)

    # ─── Scores ────────────────────────────────────
    risk_score = Column(Float, nullable=False, default=0.0)
    nlp_score = Column(Float, nullable=True)
    behavior_score = Column(Float, nullable=True)
    url_score = Column(Float, nullable=True)
    reputation_score = Column(Float, nullable=True)

    threat_level = Column(SAEnum(ThreatLevel), nullable=False, default=ThreatLevel.LOW)
    threat_detected = Column(Boolean, default=False, nullable=False)
    confidence = Column(Float, nullable=True)

    # ─── Analysis Details ──────────────────────────
    reasons = Column(JSON, nullable=True)           # list[str]
    extracted_urls = Column(JSON, nullable=True)    # list[str]
    classification_label = Column(String(100), nullable=True, index=True)
    target_department = Column(String(100), nullable=True, index=True)
    target_role = Column(String(100), nullable=True, index=True)

    # ─── Metadata ─────────────────────────────────
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    # Relationships
    created_by_user = relationship("User", back_populates="threats")
    alert = relationship("Alert", back_populates="threat", uselist=False)

    @property
    def content_excerpt(self) -> str:
        if not self.content:
            return ""
        return self.content[:200] + ("..." if len(self.content) > 200 else "")

    def __repr__(self) -> str:
        return f"<Threat id={self.id} type={self.type} level={self.threat_level} score={self.risk_score}>"


# ─── Alert ────────────────────────────────────────────────────────────────────

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    threat_id = Column(UUID(as_uuid=True), ForeignKey("threats.id"), nullable=False)
    severity = Column(SAEnum(AlertSeverity), nullable=False, default=AlertSeverity.info)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    acknowledged = Column(Boolean, default=False, nullable=False)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    # Relationships
    threat = relationship("Threat", back_populates="alert")

    def __repr__(self) -> str:
        return f"<Alert id={self.id} severity={self.severity} acknowledged={self.acknowledged}>"


# ─── Audit Log ────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(255), nullable=False)
    resource = Column(String(100), nullable=True)
    resource_id = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action} user_id={self.user_id}>"


# ─── Email Account (Gmail OAuth) ──────────────────────────────────────────────

class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False, default="gmail")
    email_address = Column(String(255), nullable=False, index=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expiry = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="email_accounts")

    def __repr__(self) -> str:
        return f"<EmailAccount id={self.id} email={self.email_address} provider={self.provider}>"


# ─── Device ───────────────────────────────────────────────────────────────────

class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    device_name = Column(String(255), nullable=False)
    device_token = Column(String(512), nullable=True, unique=True)  # Push notification token
    platform = Column(String(50), nullable=False)   # ios / android / web
    is_active = Column(Boolean, default=True, nullable=False)
    last_seen_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="devices")

    def __repr__(self) -> str:
        return f"<Device id={self.id} name={self.device_name} platform={self.platform}>"
