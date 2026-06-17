"""
Gmail OAuth2 Routes
GET  /gmail/connect     — Redirect user to Google OAuth
GET  /gmail/callback    — Handle OAuth callback, store tokens
GET  /gmail/accounts    — List connected Gmail accounts
DELETE /gmail/accounts/{id} — Disconnect a Gmail account
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.database.session import get_db
from app.database.models.models import EmailAccount, User, UserRole
from app.api.dependencies.auth import get_current_user, require_role
from app.services.gmail_service import gmail_service
from app.core.security import create_access_token, decode_access_token

logger = get_logger(__name__)

router = APIRouter(prefix="/gmail", tags=["Gmail Integration"])


@router.get(
    "/connect",
    summary="Start Gmail OAuth2 flow — redirects to Google consent screen",
)
def gmail_connect(
    current_user: User = Depends(get_current_user),
) -> RedirectResponse:
    """
    Initiates the Google OAuth2 authorization flow.
    The user's ID is encoded as the OAuth state parameter so we can
    bind the returned tokens to the correct account in /callback.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured on this server.",
        )

    # Encode user ID as the state so the callback can identify the user
    state = str(current_user.id)

    try:
        auth_url = gmail_service.build_authorization_url(state=state)
        return RedirectResponse(url=auth_url)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))


@router.get(
    "/callback",
    summary="OAuth2 callback — exchanges code for tokens and stores them",
)
def gmail_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="User ID encoded in state parameter"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Google redirects here after the user grants permission.
    - Exchanges the authorization code for access + refresh tokens.
    - Fetches the authorized Gmail address.
    - Stores/updates the EmailAccount record in the database.
    """
    # Validate state → must be a valid UUID (user_id)
    try:
        user_id = uuid.UUID(state)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    # Exchange code for tokens
    try:
        tokens = gmail_service.exchange_code_for_tokens(code)
    except Exception as exc:
        logger.error(f"Token exchange failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to exchange authorization code. Please try again.",
        )

    # Fetch the Gmail address that was authorized
    try:
        profile = gmail_service.get_gmail_profile(
            tokens["access_token"], tokens.get("refresh_token")
        )
        gmail_address = profile["email_address"]
    except Exception as exc:
        logger.error(f"Failed to fetch Gmail profile: {exc}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not fetch Gmail profile after authorization.",
        )

    # Upsert EmailAccount
    existing = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.user_id == user_id,
            EmailAccount.email_address == gmail_address,
        )
        .first()
    )

    if existing:
        existing.access_token = tokens["access_token"]
        existing.refresh_token = tokens.get("refresh_token") or existing.refresh_token
        existing.token_expiry = tokens.get("token_expiry")
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        logger.info(f"Gmail account re-linked: {gmail_address} → user {user.email}")
    else:
        account = EmailAccount(
            user_id=user_id,
            provider="gmail",
            email_address=gmail_address,
            access_token=tokens["access_token"],
            refresh_token=tokens.get("refresh_token"),
            token_expiry=tokens.get("token_expiry"),
        )
        db.add(account)
        db.commit()
        db.refresh(account)
        logger.info(f"Gmail account linked: {gmail_address} → user {user.email}")

    return HTMLResponse(
        content=f"""
        <html>
            <head>
                <title>Gmail Connected</title>
                <style>
                    body {{ font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; background: #121212; color: white; text-align: center; }}
                    .card {{ background: #1e1e1e; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
                    h1 {{ color: #4ade80; }}
                    p {{ color: #a1a1aa; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <h1>Success!</h1>
                    <p>Gmail account <b>{gmail_address}</b> has been connected to SentinelX.</p>
                    <p>You can now safely close this window and return to the app.</p>
                </div>
            </body>
        </html>
        """
    )


@router.get(
    "/accounts",
    summary="List all connected Gmail accounts for the current user",
)
def list_gmail_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list:
    """Returns all active Gmail accounts linked to the authenticated user."""
    accounts = (
        db.query(EmailAccount)
        .filter(
            EmailAccount.user_id == current_user.id,
            EmailAccount.is_active == True,
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


@router.delete(
    "/accounts/{account_id}",
    summary="Disconnect a linked Gmail account",
)
def disconnect_gmail_account(
    account_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Marks the EmailAccount as inactive (soft delete)."""
    from app.services.user_service import user_service

    success = user_service.disconnect_email_account(db, account_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gmail account not found or does not belong to you.",
        )
    return {"success": True, "message": "Gmail account disconnected."}


@router.post(
    "/poll/trigger",
    summary="Manually trigger a Gmail poll (SOC/admin only)",
)
def trigger_poll(
    current_user: User = Depends(require_role([UserRole.soc, UserRole.sysadmin])),
) -> dict:
    """
    Manually enqueues a Celery task to poll all Gmail accounts immediately.
    Useful for testing without waiting for the scheduled interval.
    """
    from app.workers.celery_worker import poll_gmail_accounts_task
    task = poll_gmail_accounts_task.apply_async()
    return {"success": True, "task_id": task.id, "message": "Gmail poll task enqueued."}
