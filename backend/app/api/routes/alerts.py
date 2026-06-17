"""
Alert Management Routes
GET  /alerts                      — List all alerts (with pagination)
POST /alerts/{id}/acknowledge     — Acknowledge a specific alert
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models.models import User
from app.api.dependencies.auth import get_current_user
from app.services.alert_service import alert_service
from app.schemas.schemas import AlertListResponse, AcknowledgeAlertResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get(
    "",
    response_model=AlertListResponse,
    summary="List all alerts with optional pagination",
)
def list_alerts(
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
    unacknowledged_only: bool = Query(False, description="Filter to unacknowledged alerts"),
    db: Session = Depends(get_db),
) -> AlertListResponse:
    """
    Retrieve paginated list of alerts.
    Optionally filter to show only unacknowledged alerts.
    """
    return alert_service.list_alerts(
        db, None, skip=skip, limit=limit, unacknowledged_only=unacknowledged_only
    )


@router.post(
    "/{alert_id}/acknowledge",
    response_model=AcknowledgeAlertResponse,
    summary="Acknowledge an alert by ID",
)
def acknowledge_alert(
    alert_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AcknowledgeAlertResponse:
    """Mark an alert as acknowledged. Records which operator acknowledged it."""
    result = alert_service.acknowledge_alert(alert_id, current_user, db)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found.",
        )
    return result


@router.post(
    "/acknowledge-all",
    summary="Acknowledge all pending alerts",
)
def acknowledge_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Marks all unacknowledged alerts as acknowledged for the current user's scope."""
    count = alert_service.acknowledge_all_alerts(current_user, db)
    return {"success": True, "acknowledged_count": count}
