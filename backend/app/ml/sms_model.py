"""
SMS Threat Detection Model
Specialised heuristics and ML classification for SMS scam/phishing detection.
Re-uses the core PhishingModel with SMS-specific keyword extensions.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from app.ml.phishing_model import phishing_model
from app.core.logging import get_logger

logger = get_logger(__name__)

# ─── SMS-specific patterns ────────────────────────────────────────────────────

SMS_SCAM_PATTERNS = [
    # OTP / 2FA fraud
    r"\b(otp|one.time.pass(word|code)?)\b",
    r"\bdo not share\b.*\b(otp|code|pin)\b",
    r"\benter.*\bcode\b.*\bbelow\b",
    # Prize / lottery
    r"\byou('ve| have) won\b",
    r"\bfree\s+(gift|prize|reward|iphone|airpods)\b",
    r"\bclaim\s+(now|today|your\s+prize)\b",
    # Fake bank / govt
    r"\bkyc\s+(update|verify|expired)\b",
    r"\bpan\s+card\b.*(block|suspend|verif)",
    r"\btax\s+refund\b",
    r"\bincome\s+tax\b",
    # Urgency
    r"\b(last\s+chance|act\s+now|expires?\s+(today|soon))\b",
    r"\byour\s+account\s+will\s+be\s+(block|suspend|clos)\w*",
    # Malicious links in SMS
    r"https?://bit\.ly/",
    r"https?://tinyurl\.com/",
    r"https?://goo\.gl/",
    r"https?://t\.co/",
]

SMS_COMPILED = [re.compile(p, re.IGNORECASE) for p in SMS_SCAM_PATTERNS]


class SMSModel:
    """SMS-specific scam detector."""

    def classify(self, message: str) -> Tuple[str, float, float]:
        """
        Classify an SMS message.

        Returns:
            (label, nlp_score_0_100, confidence_0_1)
        """
        # Run base NLP model
        label, base_nlp_score, confidence = phishing_model.classify(message)

        # Apply SMS-specific boost
        sms_hits = sum(1 for p in SMS_COMPILED if p.search(message))
        sms_boost = sms_hits * 5.0  # +5 per matched SMS pattern
        nlp_score = round(min(base_nlp_score + sms_boost, 100.0), 2)

        # Re-evaluate confidence with SMS context
        if sms_hits > 0:
            confidence = round(min(confidence + 0.1 * sms_hits, 1.0), 4)
            if label == "safe":
                label = "scam"

        return label, nlp_score, confidence

    def get_matched_patterns(self, message: str) -> List[str]:
        """Return list of matched SMS scam pattern descriptions."""
        matched = []
        descriptions = [
            "OTP/2FA fraud attempt",
            "OTP sharing request",
            "Code phishing",
            "Prize/lottery scam",
            "Free gift scam",
            "Prize claim urgency",
            "KYC verification fraud",
            "PAN card fraud",
            "Tax refund scam",
            "Income tax impersonation",
            "Urgency manipulation",
            "Account suspension threat",
            "Shortened URL (bit.ly)",
            "Shortened URL (tinyurl)",
            "Shortened URL (goo.gl)",
            "Shortened URL (t.co)",
        ]
        for pattern, desc in zip(SMS_COMPILED, descriptions):
            if pattern.search(message):
                matched.append(desc)
        return matched


sms_model = SMSModel()
