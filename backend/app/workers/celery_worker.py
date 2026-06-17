"""
Celery Worker Configuration & Task Definitions
Background task queue for async email, SMS, and call analysis.
"""

from __future__ import annotations

import uuid
from typing import Optional

from celery import Celery
from celery.utils.log import get_task_logger

from app.core.config import settings

logger = get_task_logger(__name__)

# ─── Celery App Instance ──────────────────────────────────────────────────────

celery_app = Celery(
    "sentinelx",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.celery_worker"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,                   # Reliable delivery
    worker_prefetch_multiplier=1,          # Fair task distribution
    result_expires=3600,                   # Results expire after 1 hour
    task_routes={
        "app.workers.celery_worker.analyze_email_task": {"queue": "email"},
        "app.workers.celery_worker.analyze_sms_task": {"queue": "sms"},
        "app.workers.celery_worker.analyze_call_task": {"queue": "call"},
        "app.workers.celery_worker.poll_gmail_accounts_task": {"queue": "polling"},
    },
    # ─── Beat schedule: run Gmail polling every 60 seconds ────────────────────
    beat_schedule={
        "poll-gmail-accounts": {
            "task": "app.workers.celery_worker.poll_gmail_accounts_task",
            "schedule": settings.GMAIL_POLL_INTERVAL_SECONDS,
        },
    },
)


# ─── Tasks ────────────────────────────────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="app.workers.celery_worker.analyze_email_task",
    max_retries=3,
    default_retry_delay=10,
)
def analyze_email_task(
    self,
    sender: str,
    subject: str,
    body: str,
    user_id: Optional[str] = None,
) -> dict:
    """
    Celery task: async email threat analysis.

    Args:
        sender:   Email sender address
        subject:  Email subject line
        body:     Email body text
        user_id:  UUID string of the requesting user (optional)

    Returns:
        Serialized ThreatAnalysisResponse dict
    """
    try:
        from app.database.session import SessionLocal
        from app.services.email_service import email_service
        from app.services.alert_service import alert_service
        from app.schemas.schemas import EmailAnalysisRequest
        from app.database.models.models import Threat

        logger.info(f"[Task {self.request.id}] Analyzing email from {sender}")

        request = EmailAnalysisRequest(sender=sender, subject=subject, body=body)
        db = SessionLocal()
        try:
            uid = uuid.UUID(user_id) if user_id else None
            result = email_service.analyze(request, db, user_id=uid)

            # Auto-create alert if threshold exceeded
            threat = db.query(Threat).filter(Threat.id == result.threat_id).first()
            if threat:
                alert_service.maybe_create_alert(threat, db)

            return result.model_dump(mode="json")
        finally:
            db.close()

    except Exception as exc:
        logger.error(f"[Task {self.request.id}] Email analysis failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="app.workers.celery_worker.analyze_sms_task",
    max_retries=3,
    default_retry_delay=10,
)
def analyze_sms_task(
    self,
    sender: str,
    message: str,
    user_id: Optional[str] = None,
) -> dict:
    """Celery task: async SMS threat analysis."""
    try:
        from app.database.session import SessionLocal
        from app.services.sms_service import sms_service
        from app.services.alert_service import alert_service
        from app.schemas.schemas import SMSAnalysisRequest
        from app.database.models.models import Threat

        logger.info(f"[Task {self.request.id}] Analyzing SMS from {sender}")

        request = SMSAnalysisRequest(sender=sender, message=message)
        db = SessionLocal()
        try:
            uid = uuid.UUID(user_id) if user_id else None
            result = sms_service.analyze(request, db, user_id=uid)

            threat = db.query(Threat).filter(Threat.id == result.threat_id).first()
            if threat:
                alert_service.maybe_create_alert(threat, db)

            return result.model_dump(mode="json")
        finally:
            db.close()

    except Exception as exc:
        logger.error(f"[Task {self.request.id}] SMS analysis failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="app.workers.celery_worker.analyze_call_task",
    max_retries=3,
    default_retry_delay=10,
)
def analyze_call_task(
    self,
    transcript: str,
    caller_id: Optional[str] = None,
    duration_seconds: Optional[int] = None,
    user_id: Optional[str] = None,
) -> dict:
    """Celery task: async call transcript analysis."""
    try:
        from app.database.session import SessionLocal
        from app.services.call_service import call_service
        from app.services.alert_service import alert_service
        from app.schemas.schemas import CallAnalysisRequest
        from app.database.models.models import Threat

        logger.info(f"[Task {self.request.id}] Analyzing call from {caller_id}")

        request = CallAnalysisRequest(
            transcript=transcript,
            caller_id=caller_id,
            duration_seconds=duration_seconds,
        )
        db = SessionLocal()
        try:
            uid = uuid.UUID(user_id) if user_id else None
            result = call_service.analyze_transcript(request, db, user_id=uid)

            threat = db.query(Threat).filter(Threat.id == result.threat_id).first()
            if threat:
                alert_service.maybe_create_alert(threat, db)

            return result.model_dump(mode="json")
        finally:
            db.close()

    except Exception as exc:
        logger.error(f"[Task {self.request.id}] Call analysis failed: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(
    bind=True,
    name="app.workers.celery_worker.poll_gmail_accounts_task",
    max_retries=2,
    default_retry_delay=30,
)
def poll_gmail_accounts_task(self) -> dict:
    """
    Celery periodic task: poll all active Gmail accounts for new emails.
    Scheduled by Celery Beat every GMAIL_POLL_INTERVAL_SECONDS seconds.
    Each new email is run through the full threat analysis pipeline automatically.
    """
    try:
        from app.services.polling_service import polling_service

        logger.info(f"[Task {self.request.id}] Starting Gmail polling cycle.")
        polling_service.poll_all_accounts()
        logger.info(f"[Task {self.request.id}] Gmail polling cycle complete.")
        return {"status": "done"}

    except Exception as exc:
        logger.error(f"[Task {self.request.id}] Gmail polling failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)
