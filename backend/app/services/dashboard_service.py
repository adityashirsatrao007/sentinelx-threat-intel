"""
Dashboard Analytics Service
Provides aggregated statistics and trend data for the frontend dashboard.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.database.models.models import Alert, Threat, ThreatLevel, AlertSeverity, User, UserRole
from app.schemas.schemas import (
    DashboardStats,
    ThreatSummary,
    ThreatListResponse,
    ThreatTrend,
    DashboardTrends,
)
from app.schemas.analytics import TargetAnalyticsResponse, TargetMetric
from app.core.logging import get_logger

logger = get_logger(__name__)


class DashboardService:
    """Aggregation queries for dashboard analytics endpoints."""

    def _filter_threat_query(self, query, user: User):
        if user.role == UserRole.sysadmin:
            return query
        if user.role == UserRole.soc:
            return query.join(User, Threat.created_by == User.id).filter(User.organization_id == user.organization_id)
        return query.filter(Threat.created_by == user.id)

    def _filter_alert_query(self, query, user: User):
        if user.role == UserRole.sysadmin:
            return query
        if user.role == UserRole.soc:
            return query.join(Threat).join(User, Threat.created_by == User.id).filter(User.organization_id == user.organization_id)
        return query.join(Threat).filter(Threat.created_by == user.id)

    def get_stats(self, db: Session, user: User) -> DashboardStats:
        """Return high-level KPI statistics."""
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        t_query = self._filter_threat_query(db.query(Threat), user)
        a_query = self._filter_alert_query(db.query(Alert), user)

        total_threats = t_query.count()
        phishing_attempts = (
            t_query.filter(Threat.classification_label.in_(["phishing", "credential_theft"])).count()
        )
        high_risk_alerts = (
            a_query.filter(Alert.severity.in_([AlertSeverity.high, AlertSeverity.critical])).count()
        )
        critical_alerts = (
            a_query.filter(Alert.severity == AlertSeverity.critical).count()
        )
        threats_today = (
            t_query.filter(Threat.created_at >= today_start).count()
        )
        avg_risk = (
            t_query.with_entities(func.avg(Threat.risk_score)).scalar() or 0.0
        )
        unacknowledged = (
            a_query.filter(Alert.acknowledged == False).count()
        )

        return DashboardStats(
            total_threats=total_threats,
            phishing_attempts=phishing_attempts,
            high_risk_alerts=high_risk_alerts,
            critical_alerts=critical_alerts,
            threats_today=threats_today,
            avg_risk_score=round(float(avg_risk), 2),
            unacknowledged_alerts=unacknowledged,
        )

    def get_recent_threats(
        self, db: Session, user: User, skip: int = 0, limit: int = 50
    ) -> ThreatListResponse:
        """Return paginated recent threats."""
        t_query = self._filter_threat_query(db.query(Threat), user)
        total = t_query.count()
        threats = (
            t_query
            .order_by(desc(Threat.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return ThreatListResponse(
            total=total,
            threats=[ThreatSummary.model_validate(t) for t in threats],
        )

    def get_trends(self, db: Session, user: User, days: int = 7) -> DashboardTrends:
        """
        Return daily threat counts and average risk scores per channel
        over the past N days.
        """
        since = datetime.now(timezone.utc) - timedelta(days=days)

        t_query = self._filter_threat_query(db.query(Threat), user)
        
        rows = (
            t_query.with_entities(
                func.date(Threat.created_at).label("date"),
                Threat.channel,
                func.count(Threat.id).label("count"),
                func.avg(Threat.risk_score).label("avg_score"),
            )
            .filter(Threat.created_at >= since)
            .group_by(func.date(Threat.created_at), Threat.channel)
            .order_by(func.date(Threat.created_at))
            .all()
        )

        trends: List[ThreatTrend] = []
        for row in rows:
            trends.append(
                ThreatTrend(
                    date=str(row.date),
                    count=row.count,
                    avg_risk_score=round(float(row.avg_score or 0), 2),
                    channel=row.channel,
                )
            )

        return DashboardTrends(trends=trends, period_days=days)

    def get_target_analytics(self, db: Session, user: User) -> TargetAnalyticsResponse:
        """Analyze threats by target department and role."""
        t_query = self._filter_threat_query(db.query(Threat), user)
        
        # Department stats
        dept_rows = (
            t_query.with_entities(
                Threat.target_department,
                func.count(Threat.id).label("count"),
                func.avg(Threat.risk_score).label("avg_score")
            )
            .filter(Threat.target_department != None)
            .group_by(Threat.target_department)
            .order_by(desc("count"))
            .all()
        )
        
        # Role stats
        role_rows = (
            t_query.with_entities(
                Threat.target_role,
                func.count(Threat.id).label("count"),
                func.avg(Threat.risk_score).label("avg_score")
            )
            .filter(Threat.target_role != None)
            .group_by(Threat.target_role)
            .order_by(desc("count"))
            .all()
        )
        
        return TargetAnalyticsResponse(
            departments=[
                TargetMetric(name=r.target_department, threat_count=r.count, avg_risk_score=round(float(r.avg_score), 2))
                for r in dept_rows
            ],
            roles=[
                TargetMetric(name=r.target_role, threat_count=r.count, avg_risk_score=round(float(r.avg_score), 2))
                for r in role_rows
            ]
        )


dashboard_service = DashboardService()
