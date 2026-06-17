"""
Simple Gmail IMAP Service
Connects to Gmail via IMAP using App Passwords (no OAuth needed).
User just provides email + app password.
"""

from __future__ import annotations

import imaplib
import email as email_lib
from email.header import decode_header
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class SimpleGmailService:
    """Fetch emails from Gmail using IMAP + App Password. Zero OAuth setup."""

    IMAP_HOST = "imap.gmail.com"
    IMAP_PORT = 993

    def connect(self, email_address: str, app_password: str) -> bool:
        """Test the connection. Returns True if credentials work."""
        try:
            mail = imaplib.IMAP4_SSL(self.IMAP_HOST, self.IMAP_PORT)
            mail.login(email_address, app_password)
            mail.logout()
            return True
        except imaplib.IMAP4.error as exc:
            logger.warning(f"IMAP login failed for {email_address}: {exc}")
            return False
        except Exception as exc:
            logger.error(f"IMAP connection error: {exc}")
            return False

    def fetch_recent_emails(
        self,
        email_address: str,
        app_password: str,
        max_results: int = 20,
        since_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch recent unread emails via IMAP.
        Returns list of dicts with sender, subject, body, date.
        """
        emails = []
        try:
            mail = imaplib.IMAP4_SSL(self.IMAP_HOST, self.IMAP_PORT)
            mail.login(email_address, app_password)
            mail.select("INBOX")

            # Build search query
            if since_date:
                date_str = since_date.strftime("%d-%b-%Y")
                search_query = f'(UNSEEN SINCE {date_str})'
            else:
                search_query = "(UNSEEN)"

            _, message_ids = mail.search(None, search_query)

            if not message_ids[0]:
                mail.logout()
                return []

            ids = message_ids[0].split()
            # Get the most recent ones
            ids = ids[-max_results:]

            for msg_id in ids:
                try:
                    _, msg_data = mail.fetch(msg_id, "(RFC822)")
                    raw_email = msg_data[0][1]
                    msg = email_lib.message_from_bytes(raw_email)

                    parsed = self._parse_email(msg)
                    if parsed:
                        emails.append(parsed)
                except Exception as e:
                    logger.warning(f"Failed to parse email {msg_id}: {e}")

            mail.logout()
            return emails

        except imaplib.IMAP4.error as exc:
            logger.error(f"IMAP error for {email_address}: {exc}")
            return []
        except Exception as exc:
            logger.error(f"Unexpected IMAP error: {exc}")
            return []

    def _parse_email(self, msg: email_lib.message.Message) -> Optional[Dict[str, Any]]:
        """Parse an email.message.Message into a clean dict."""
        try:
            # Decode subject
            subject = ""
            raw_subject = msg.get("Subject", "")
            if raw_subject:
                decoded_parts = decode_header(raw_subject)
                subject = " ".join(
                    part.decode(charset or "utf-8", errors="replace") if isinstance(part, bytes) else str(part)
                    for part, charset in decoded_parts
                )

            # Get sender
            sender = msg.get("From", "")

            # Get date
            date_str = msg.get("Date", "")

            # Extract body
            body = self._extract_body(msg)

            return {
                "sender": sender,
                "subject": subject,
                "body": body[:3000],  # Limit body size
                "date": date_str,
            }
        except Exception as e:
            logger.warning(f"Email parse error: {e}")
            return None

    def _extract_body(self, msg: email_lib.message.Message) -> str:
        """Extract plain text body from email."""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        charset = part.get_content_charset() or "utf-8"
                        return part.get_payload(decode=True).decode(charset, errors="replace")
                    except Exception:
                        continue
        else:
            try:
                charset = msg.get_content_charset() or "utf-8"
                return msg.get_payload(decode=True).decode(charset, errors="replace")
            except Exception:
                pass
        return ""


simple_gmail_service = SimpleGmailService()
