"""
Dashboard Analytics Routes
GET /dashboard/stats   — KPI statistics
GET /dashboard/threats — Recent threats list
GET /dashboard/trends  — Daily threat trends
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models.models import User
from app.api.dependencies.auth import get_current_user
from app.services.dashboard_service import dashboard_service
from app.schemas.schemas import DashboardStats, ThreatListResponse, DashboardTrends
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/stats",
    response_model=DashboardStats,
    summary="Retrieve high-level threat and alert KPIs",
)
def get_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardStats:
    return dashboard_service.get_stats(db, current_user)


@router.get(
    "/threats",
    response_model=ThreatListResponse,
    summary="Retrieve paginated recent threats",
)
def get_threats(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ThreatListResponse:
    return dashboard_service.get_recent_threats(db, current_user, skip=skip, limit=limit)


from app.schemas.analytics import TargetAnalyticsResponse


@router.get(
    "/trends",
    response_model=DashboardTrends,
    summary="Retrieve daily threat trends over the past N days",
)
def get_trends(
    days: int = Query(7, ge=1, le=90, description="Number of past days to include"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardTrends:
    return dashboard_service.get_trends(db, current_user, days=days)


@router.get(
    "/targets",
    response_model=TargetAnalyticsResponse,
    summary="Retrieve threat analytics by target department and role",
)
def get_targets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TargetAnalyticsResponse:
    return dashboard_service.get_target_analytics(db, current_user)
