"""
Simple Email Connect Routes
Connect Gmail using just email + App Password (IMAP). No OAuth needed.

POST /email/connect    — Connect email with app password
GET  /email/accounts   — List connected email accounts
POST /email/scan       — Manually trigger email scan
DELETE /email/accounts/{id} — Disconnect email
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database.session import get_db
from app.database.models.models import EmailAccount, User
from app.api.dependencies.auth import get_current_user
from app.services.simple_gmail_service import simple_gmail_service
from app.services.email_service import email_service
from app.schemas.schemas import EmailAnalysisRequest

logger = get_logger(__name__)

router = APIRouter(prefix="/email", tags=["Email Integration (Simple)"])


class EmailConnectRequest(BaseModel):
    email_address: str
    app_password: str


@router.post(
    "/connect",
    summary="Connect a Gmail account using App Password (no OAuth needed)",
)
def connect_email(
    req: EmailConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Connect Gmail using IMAP + App Password.
    
    Steps for the user:
    1. Go to myaccount.google.com → Security → 2-Step Verification → App Passwords
    2. Generate a password for "Mail"
    3. Enter email + that app password here
    """
    # Test the connection first
    if not simple_gmail_service.connect(req.email_address, req.app_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not connect. Check your email and app password. Make sure 2FA is enabled and you're using an App Password, not your regular password.",
        )

    # Check if already connected
    existing = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.user_id == current_user.id,
            EmailAccount.email_address == req.email_address,
        )
        .first()
    )

    if existing:
        existing.access_token = req.app_password  # Store app password
        existing.is_active = True
        db.commit()
        logger.info(f"Email re-connected: {req.email_address}")
        return {"success": True, "message": f"Re-connected {req.email_address}"}
    else:
        account = EmailAccount(
            user_id=current_user.id,
            provider="gmail_imap",
            email_address=req.email_address,
            access_token=req.app_password,  # Store app password
            is_active=True,
        )
        db.add(account)
        db.commit()
        logger.info(f"Email connected: {req.email_address} → user {current_user.email}")
        return {"success": True, "message": f"Connected {req.email_address}. Emails will be scanned automatically."}


@router.get(
    "/accounts",
    summary="List connected email accounts",
)
def list_email_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    accounts = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.user_id == current_user.id,
            EmailAccount.is_active,
        )
        .all()
    )
    return [
        {
            "id": str(a.id),
            "email_address": a.email_address,
            "provider": a.provider,
            "last_synced_at": a.last_synced_at.isoformat() if a.last_synced_at else None,
            "created_at": a.created_at.isoformat(),
        }
        for a in accounts
    ]


@router.post(
    "/scan",
    summary="Manually scan connected email accounts for threats",
)
def scan_emails(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Fetches unread emails from all connected accounts and analyzes them."""
    accounts = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.user_id == current_user.id,
            EmailAccount.is_active,
        )
        .all()
    )

    if not accounts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No email accounts connected. Connect one first.",
        )

    total_scanned = 0
    threats_found = 0
    results = []

    for account in accounts:
        try:
            emails = simple_gmail_service.fetch_recent_emails(
                email_address=account.email_address,
                app_password=account.access_token,  # stored app password
                max_results=10,
                since_date=account.last_synced_at,
            )

            for em in emails:
                try:
                    analysis = email_service.analyze(
                        EmailAnalysisRequest(
                            sender=em.get("sender", "unknown"),
                            subject=em.get("subject", ""),
                            body=em.get("body", ""),
                        ),
                        db=db,
                        user_id=current_user.id,
                    )
                    total_scanned += 1
                    if analysis.threat_detected:
                        threats_found += 1
                        results.append({
                            "sender": em.get("sender"),
                            "subject": em.get("subject"),
                            "risk_score": analysis.risk_score,
                            "threat_level": analysis.threat_level,
                        })
                except Exception as e:
                    logger.warning(f"Failed to analyze email: {e}")

            # Update last synced
            account.last_synced_at = datetime.now(timezone.utc)
            db.commit()

        except Exception as exc:
            logger.error(f"Failed to scan {account.email_address}: {exc}")

    return {
        "success": True,
        "emails_scanned": total_scanned,
        "threats_found": threats_found,
        "threats": results,
    }


@router.delete(
    "/accounts/{account_id}",
    summary="Disconnect an email account",
)
def disconnect_email(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    account = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.id == account_id,
            EmailAccount.user_id == current_user.id,
        )
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found.")

    account.is_active = False
    account.access_token = None  # Clear stored password
    db.commit()
    return {"success": True, "message": "Email disconnected."}
