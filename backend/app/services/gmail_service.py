"""
Gmail OAuth2 Service
Handles Google OAuth2 flow and Gmail API email fetching.
"""

from __future__ import annotations

import base64
import email as email_lib
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.database.models.models import EmailAccount, User

logger = get_logger(__name__)


class GmailService:
    """Handles Google OAuth2 authorization and Gmail email fetching."""

    def build_authorization_url(self, state: str) -> str:
        """
        Build the Google OAuth2 authorization URL to redirect the user to.
        The `state` parameter carries the SentinelX JWT user ID for callback binding.
        """
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise RuntimeError(
                "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be configured in .env"
            )

        flow = self._build_flow()
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",       # Force consent screen to get refresh_token every time
            state=state,
        )
        return auth_url

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange the OAuth authorization code for access + refresh tokens.
        Returns a dict with token data.
        """
        flow = self._build_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials

        return {
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_expiry": credentials.expiry,
        }

    def get_gmail_profile(self, access_token: str, refresh_token: Optional[str]) -> Dict[str, str]:
        """Fetch the Gmail user's email address using the token."""
        creds = self._build_credentials(access_token, refresh_token)
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        return {"email_address": profile.get("emailAddress", "")}

    def refresh_access_token(self, account: EmailAccount) -> Optional[str]:
        """
        Refresh the Google access token using the stored refresh_token.
        Updates the EmailAccount in-place. Returns new access_token or None if failed.
        """
        if not account.refresh_token:
            logger.warning(f"No refresh_token for EmailAccount {account.id}")
            return None

        creds = self._build_credentials(
            access_token=account.access_token or "",
            refresh_token=account.refresh_token,
        )
        try:
            creds.refresh(GoogleRequest())
            account.access_token = creds.token
            account.token_expiry = creds.expiry
            logger.info(f"Refreshed access token for EmailAccount {account.id}")
            return creds.token
        except Exception as exc:
            logger.error(f"Failed to refresh token for EmailAccount {account.id}: {exc}")
            return None

    def fetch_new_emails(
        self,
        account: EmailAccount,
        max_results: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Fetch unread emails from Gmail since last_synced_at.
        Returns a list of parsed email dicts.
        """
        try:
            creds = self._build_credentials(account.access_token, account.refresh_token)
            service = build("gmail", "v1", credentials=creds)

            # Build query: unread emails after last sync
            query = "is:unread"
            if account.last_synced_at:
                epoch = int(account.last_synced_at.timestamp())
                query += f" after:{epoch}"

            result = service.users().messages().list(
                userId="me", q=query, maxResults=max_results
            ).execute()

            messages = result.get("messages", [])
            if not messages:
                return []

            parsed_emails = []
            for msg_ref in messages:
                try:
                    msg = service.users().messages().get(
                        userId="me", id=msg_ref["id"], format="full"
                    ).execute()
                    parsed = self._parse_message(msg)
                    parsed_emails.append(parsed)
                except HttpError as e:
                    logger.warning(f"Could not fetch message {msg_ref['id']}: {e}")

            return parsed_emails

        except HttpError as exc:
            logger.error(f"Gmail API error for account {account.email_address}: {exc}")
            return []
        except Exception as exc:
            logger.error(f"Unexpected error fetching emails for {account.email_address}: {exc}")
            return []

    # ─── Private Helpers ──────────────────────────────────────────────────────

    def _build_flow(self) -> Flow:
        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }
        return Flow.from_client_config(
            client_config,
            scopes=settings.GOOGLE_SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI,
        )

    def _build_credentials(
        self, access_token: str, refresh_token: Optional[str]
    ) -> Credentials:
        return Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=settings.GOOGLE_SCOPES,
        )

    def _parse_message(self, msg: Dict) -> Dict[str, Any]:
        """Extract sender, subject, body, and URLs from a raw Gmail message."""
        headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
        body = self._extract_body(msg.get("payload", {}))

        return {
            "gmail_id": msg.get("id"),
            "thread_id": msg.get("threadId"),
            "sender": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "date": headers.get("Date", ""),
            "body": body,
        }

    def _extract_body(self, payload: Dict) -> str:
        """Recursively extract plain text body from Gmail message payload."""
        mime_type = payload.get("mimeType", "")
        body_data = payload.get("body", {}).get("data", "")

        if mime_type == "text/plain" and body_data:
            return base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")

        parts = payload.get("parts", [])
        for part in parts:
            result = self._extract_body(part)
            if result:
                return result

        return ""


gmail_service = GmailService()
