"""
Alert Service
Automatically creates alerts when risk scores exceed configured thresholds,
and handles alert acknowledgment.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database.models.models import Alert, Threat, AlertSeverity, ThreatLevel, User, UserRole
from app.schemas.schemas import AlertResponse, AlertListResponse, AcknowledgeAlertResponse
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Map threat level → alert severity
LEVEL_TO_SEVERITY = {
    ThreatLevel.LOW: AlertSeverity.info,
    ThreatLevel.MEDIUM: AlertSeverity.warning,
    ThreatLevel.HIGH: AlertSeverity.high,
    ThreatLevel.CRITICAL: AlertSeverity.critical,
}


class AlertService:
    """Manages alert creation and lifecycle."""

    def maybe_create_alert(self, threat: Threat, db: Session) -> Optional[Alert]:
        """
        Create an alert for a threat if risk score exceeds the configured threshold.

        Returns the created Alert or None if threshold not met.
        """
        if threat.risk_score < settings.ALERT_TRIGGER_THRESHOLD:
            return None

        # Avoid duplicate alerts for the same threat
        existing = db.query(Alert).filter(Alert.threat_id == threat.id).first()
        if existing:
            return existing

        severity = LEVEL_TO_SEVERITY.get(threat.threat_level, AlertSeverity.info)
        title = self._build_title(threat)
        description = self._build_description(threat)

        alert = Alert(
            threat_id=threat.id,
            severity=severity,
            title=title,
            description=description,
            acknowledged=False,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

        logger.warning(
            f"Alert created: id={alert.id}, severity={severity.value}, "
            f"threat_id={threat.id}, score={threat.risk_score}"
        )
        return alert

    def list_alerts(
        self,
        db: Session,
        user: User,
        skip: int = 0,
        limit: int = 50,
        unacknowledged_only: bool = False,
    ) -> AlertListResponse:
        """List alerts, optionally filtered to unacknowledged only."""
        query = db.query(Alert)
        
        if user:
            if user.role != UserRole.sysadmin:
                if user.role == UserRole.soc:
                    query = query.join(Threat).join(User, Threat.created_by == User.id).filter(User.organization_id == user.organization_id)
                else:
                    query = query.join(Threat).filter(Threat.created_by == user.id)

        if unacknowledged_only:
            query = query.filter(not Alert.acknowledged)
        total = query.count()
        alerts = query.order_by(desc(Alert.created_at)).offset(skip).limit(limit).all()
        return AlertListResponse(
            total=total,
            alerts=[AlertResponse.model_validate(a) for a in alerts],
        )

    def acknowledge_alert(
        self,
        alert_id: uuid.UUID,
        user: User,
        db: Session,
    ) -> Optional[AcknowledgeAlertResponse]:
        """Mark an alert as acknowledged by a user."""
        query = db.query(Alert).filter(Alert.id == alert_id)
        if user.role != UserRole.sysadmin:
            if user.role == UserRole.soc:
                query = query.join(Threat).join(User, Threat.created_by == User.id).filter(User.organization_id == user.organization_id)
            else:
                query = query.join(Threat).filter(Threat.created_by == user.id)
                
        alert = query.first()
        if not alert:
            return None

        alert.acknowledged = True
        alert.acknowledged_by = user.id
        alert.acknowledged_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(alert)

        logger.info(f"Alert {alert_id} acknowledged by user {user.id}")
        return AcknowledgeAlertResponse(
            id=alert.id,
            acknowledged=alert.acknowledged,
            acknowledged_at=alert.acknowledged_at,
        )

    @staticmethod
    def _build_title(threat: Threat) -> str:
        channel = threat.channel.upper()
        level = threat.threat_level.value
        label = (threat.classification_label or "Unknown").replace("_", " ").title()
        return f"[{level}] {channel} Threat — {label} Detected"

    @staticmethod
    def _build_description(threat: Threat) -> str:
        reasons = threat.reasons or []
        reasons_str = "; ".join(reasons[:3])
        return (
            f"Risk Score: {threat.risk_score:.1f}/100. "
            f"Top indicators: {reasons_str}."
        )


    def acknowledge_all_alerts(self, user: User, db: Session) -> int:
        """Mark all unacknowledged alerts as acknowledged for the user's scope."""
        query = db.query(Alert).filter(not Alert.acknowledged)
        
        if user.role != UserRole.sysadmin:
            if user.role == UserRole.soc:
                query = query.join(Threat).join(User, Threat.created_by == User.id).filter(User.organization_id == user.organization_id)
            else:
                query = query.join(Threat).filter(Threat.created_by == user.id)
        
        alerts = query.all()
        count = 0
        now = datetime.now(timezone.utc)
        for alert in alerts:
            alert.acknowledged = True
            alert.acknowledged_by = user.id
            alert.acknowledged_at = now
            count += 1
            
        db.commit()
        logger.info(f"Bulk acknowledge: {count} alerts acknowledged by user {user.id}")
        return count


alert_service = AlertService()
