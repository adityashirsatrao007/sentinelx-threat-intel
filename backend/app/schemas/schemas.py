"""
Pydantic Schemas
Request/response models for all API endpoints.
"""


import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# ──────────────────────────────────────────────────────────────────────────────
# Auth Schemas
# ──────────────────────────────────────────────────────────────────────────────

class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="user", pattern="^(sysadmin|soc|operator|user)$")
    organization_name: Optional[str] = Field(default=None, description="Provide when registering as a new SOC to create an org")

class UserInviteRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: str = Field(default="user", pattern="^(operator|user)$")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    id: uuid.UUID
    organization_id: Optional[uuid.UUID]
    name: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}

class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────────────────────
# Email Analysis Schemas
# ──────────────────────────────────────────────────────────────────────────────

class EmailAnalysisRequest(BaseModel):
    sender: str = Field(..., max_length=255)
    subject: str = Field(..., max_length=1000)
    body: str = Field(..., max_length=50_000)
    attachments: Optional[List[str]] = Field(default=None, description="Attachment filenames")
    target_department: Optional[str] = Field(default=None, max_length=100)
    target_role: Optional[str] = Field(default=None, max_length=100)
    async_processing: bool = Field(default=False, description="Process via Celery task queue")
    force_risk_score: Optional[float] = None


# ──────────────────────────────────────────────────────────────────────────────
# SMS Analysis Schemas
# ──────────────────────────────────────────────────────────────────────────────

class SMSAnalysisRequest(BaseModel):
    sender: str = Field(..., max_length=50)
    message: str = Field(..., max_length=5000)
    target_department: Optional[str] = Field(default=None, max_length=100)
    target_role: Optional[str] = Field(default=None, max_length=100)
    async_processing: bool = False
    force_risk_score: Optional[float] = None


# ──────────────────────────────────────────────────────────────────────────────
# Call / Audio Analysis Schemas
# ──────────────────────────────────────────────────────────────────────────────

class CallAnalysisRequest(BaseModel):
    transcript: str = Field(..., max_length=100_000)
    caller_id: Optional[str] = Field(default=None, max_length=50)
    duration_seconds: Optional[int] = None


class TranscriptionResponse(BaseModel):
    transcript: str
    language: Optional[str] = None
    duration_seconds: Optional[float] = None


# ──────────────────────────────────────────────────────────────────────────────
# Threat Analysis Response (shared)
# ──────────────────────────────────────────────────────────────────────────────

class ThreatAnalysisResponse(BaseModel):
    threat_id: Optional[uuid.UUID] = None
    threat_detected: bool
    risk_score: float = Field(..., description="Overall risk score (1-10)")
    threat_level: str
    confidence: float = Field(..., ge=0, le=1)
    classification_label: str
    reasons: List[str]
    extracted_urls: List[str] = []
    nlp_score: float
    behavior_score: float
    url_score: float
    reputation_score: float
    target_department: Optional[str] = None
    target_role: Optional[str] = None
    processing_mode: str = "sync"  # sync | async
    task_id: Optional[str] = None  # set when async_processing=True


# ──────────────────────────────────────────────────────────────────────────────
# Dashboard & Summary Schemas
# ──────────────────────────────────────────────────────────────────────────────

class ThreatSummary(BaseModel):
    id: uuid.UUID
    type: str
    channel: str
    risk_score: float
    threat_level: str
    threat_detected: bool
    sender: Optional[str]
    classification_label: Optional[str] = None
    target_department: Optional[str] = None
    target_role: Optional[str] = None
    reasons: List[str] = []
    content_excerpt: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}

class DashboardStats(BaseModel):
    total_threats: int
    phishing_attempts: int
    high_risk_alerts: int
    critical_alerts: int
    threats_today: int
    avg_risk_score: float
    unacknowledged_alerts: int


# ──────────────────────────────────────────────────────────────────────────────
# Alert Schemas
# ──────────────────────────────────────────────────────────────────────────────

class AlertResponse(BaseModel):
    id: uuid.UUID
    threat_id: uuid.UUID
    severity: str
    title: str
    description: Optional[str]
    acknowledged: bool
    acknowledged_at: Optional[datetime]
    created_at: datetime
    threat: Optional[ThreatSummary] = None

    model_config = {"from_attributes": True}


class AlertListResponse(BaseModel):
    total: int
    alerts: List[AlertResponse]


class AcknowledgeAlertResponse(BaseModel):
    id: uuid.UUID
    acknowledged: bool
    acknowledged_at: datetime


class ThreatListResponse(BaseModel):
    total: int
    threats: List[ThreatSummary]


class ThreatTrend(BaseModel):
    date: str
    count: int
    avg_risk_score: float
    channel: str


class DashboardTrends(BaseModel):
    trends: List[ThreatTrend]
    period_days: int


# ──────────────────────────────────────────────────────────────────────────────
# Generic API Responses
# ──────────────────────────────────────────────────────────────────────────────

class SuccessResponse(BaseModel):
    success: bool = True
    message: str


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None

# Rebuild models to resolve forward references (Pydantic v2)
UserResponse.model_rebuild()
AlertResponse.model_rebuild()
ThreatSummary.model_rebuild()
ThreatAnalysisResponse.model_rebuild()
