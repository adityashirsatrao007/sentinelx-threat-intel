"""
Email Polling Service
Orchestrates the fetch → analyze → store → alert pipeline for ALL connected email accounts.
Supports both OAuth Gmail accounts AND simple IMAP (App Password) accounts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.database.models.models import EmailAccount
from app.database.session import SessionLocal
from app.services.alert_service import alert_service

logger = get_logger(__name__)


class PollingService:
    """
    Core polling orchestrator.
    Called by APScheduler every GMAIL_POLL_INTERVAL_SECONDS.
    Handles BOTH OAuth Gmail and simple IMAP accounts.
    """

    def poll_all_accounts(self) -> None:
        """
        Main entry point for periodic polling.
        Fetches ALL active email accounts (OAuth + IMAP) and polls each one.
        """
        db: Session = SessionLocal()
        try:
            accounts: List[EmailAccount] = (
                db.query(EmailAccount)
                .filter(EmailAccount.is_active)
                .filter(EmailAccount.provider.in_(["gmail", "gmail_imap"]))
                .all()
            )

            if not accounts:
                return

            logger.info(f"Polling {len(accounts)} active email account(s).")

            for account in accounts:
                try:
                    if account.provider == "gmail_imap":
                        self._poll_imap_account(account, db)
                    else:
                        self._poll_oauth_account(account, db)
                except Exception as exc:
                    logger.error(
                        f"Error polling account {account.email_address}: {exc}",
                        exc_info=True,
                    )

        finally:
            db.close()

    # ─── IMAP Polling (App Password) ─────────────────────────────────────────

    def _poll_imap_account(self, account: EmailAccount, db: Session) -> None:
        """Fetch new emails via IMAP for simple App Password accounts."""
        from app.services.simple_gmail_service import simple_gmail_service

        if not account.access_token:
            logger.warning(f"IMAP account {account.email_address} has no app password, skipping.")
            return

        emails = simple_gmail_service.fetch_recent_emails(
            email_address=account.email_address,
            app_password=account.access_token,
            max_results=15,
            since_date=account.last_synced_at,
        )

        if not emails:
            logger.debug(f"No new emails for {account.email_address} (IMAP)")
            self._update_sync_time(account, db)
            return

        logger.info(f"Fetched {len(emails)} new emails from {account.email_address} (IMAP)")

        for email_data in emails:
            self._process_email(email_data, account, db)

        self._update_sync_time(account, db)

    # ─── OAuth Polling ────────────────────────────────────────────────────────

    def _poll_oauth_account(self, account: EmailAccount, db: Session) -> None:
        """Fetch new emails via Gmail API for OAuth accounts."""
        from app.services.gmail_service import gmail_service

        if not account.access_token:
            logger.warning(f"Account {account.email_address} has no access token, skipping.")
            return

        emails = gmail_service.fetch_new_emails(account, max_results=25)
        if not emails:
            logger.debug(f"No new emails for {account.email_address}")
            self._update_sync_time(account, db)
            return

        logger.info(f"Fetched {len(emails)} new emails from {account.email_address}")

        for email_data in emails:
            self._process_email(email_data, account, db)

        self._update_sync_time(account, db)

    # ─── Shared Processing ────────────────────────────────────────────────────

    def _process_email(
        self,
        email_data: dict,
        account: EmailAccount,
        db: Session,
    ) -> None:
        """
        Run a single fetched email through the full threat analysis pipeline.
        """
        from app.services.email_service import email_service
        from app.schemas.schemas import EmailAnalysisRequest

        try:
            request = EmailAnalysisRequest(
                sender=email_data.get("sender", "unknown@gmail.com")[:255],
                subject=email_data.get("subject", "(No Subject)")[:1000],
                body=email_data.get("body", "")[:50_000],
            )

            result = email_service.analyze(request, db, user_id=account.user_id)

            # Trigger alert if threat detected
            if result.threat_id:
                from app.database.models.models import Threat
                threat = db.query(Threat).filter(Threat.id == result.threat_id).first()
                if threat:
                    alert_service.maybe_create_alert(threat, db)

            logger.info(
                f"Polled email from {account.email_address}: "
                f"score={result.risk_score} level={result.threat_level}"
            )

        except Exception as exc:
            logger.error(
                f"Failed to process email '{email_data.get('subject')}' "
                f"from {account.email_address}: {exc}",
                exc_info=True,
            )

    def _update_sync_time(self, account: EmailAccount, db: Session) -> None:
        account.last_synced_at = datetime.now(timezone.utc)
        db.commit()


polling_service = PollingService()
