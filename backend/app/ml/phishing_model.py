"""
NLP Phishing Detection Model
Enhanced heuristic classifier with comprehensive scam/phishing pattern detection.
Covers SMS scams, UPI fraud, KYC phishing, lottery scams, and more.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)

# ─── Label mapping (score when label is detected) ────────────────────────────
LABEL_SCORES: Dict[str, float] = {
    "safe": 0.0,
    "phishing": 85.0,
    "scam": 75.0,
    "credential_theft": 95.0,
    "malicious_link": 80.0,
    "impersonation": 70.0,
    "financial_fraud": 90.0,
    "lottery_scam": 85.0,
    "kyc_scam": 88.0,
}

# ─── Comprehensive phishing/scam keyword patterns ────────────────────────────
PHISHING_KEYWORDS = [
    # Account & Credential theft
    r"\bverify\s+your\s+(account|identity|email)\b",
    r"\bconfirm\s+your\b",
    r"\byour\s+password\b",
    r"\bupdate\s+your\s+(billing|payment|credit|details|info)\b",
    r"\baccount\s+(suspend|lock|block|limit|terminat|deactivat|hold|restrict|freez)\w*\b",
    r"\blogin\s+attempt\b",
    r"\bunusual\s+(activity|sign.in|transaction)\b",
    r"\bsuspicious\s+(activity|login|transaction)\b",
    r"\bunauthori[sz]ed\s+(access|transaction|activity)\b",

    # Urgency & Action
    r"\b(urgent(ly)?|immediately|right\s+now|act\s+now)\b",
    r"\b(click\s+here|tap\s+here|open\s+this|visit\s+this)\b",
    r"\b(expires?\s+(today|soon|in\s+\d+\s+(hour|minute|day)))\b",
    r"\b(last\s+(chance|opportunity|warning|reminder))\b",
    r"\b(action\s+required|response\s+required|immediate\s+action)\b",
    r"\b(within\s+\d+\s+(hour|minute|hr|min))\b",
    r"\b(before\s+it'?s?\s+too\s+late)\b",

    # Prize/Lottery/Reward scams
    r"\b(you('ve|\s+have)?\s+won)\b",
    r"\b(winner|congratulation|selected\s+as\s+winner)\b",
    r"\b(won\s+a?\s*(prize|lottery|jackpot|reward|gift))\b",
    r"\b(claim\s+(your\s+)?(prize|reward|gift|bonus|cash|money|amount))\b",
    r"\b(free\s+(gift|money|prize|trip|vacation|iphone|voucher|coupon))\b",
    r"\b(lucky\s+(draw|winner|customer|number))\b",
    r"\b(cash\s+prize|gift\s+card|bonus\s+offer)\b",
    r"[₹$£€]\s*\d+[\d,]*\s*(prize|reward|cash|won|bonus|cr|lakh|crore)",
    r"\b\d+[\d,]*\s*(rupees?|rs\.?|inr)\b",

    # KYC/UPI/Bank Scams (Indian context)
    r"\b(kyc|know\s+your\s+customer)\b.{0,40}(expir|update|verify|complet|mandator|suspend|fail)",
    r"\b(upi|paytm|phonepe|gpay|google\s*pay|bhim).{0,40}(block|suspend|verify|update|expir|fail|limit)",
    r"\b(pan\s*card|aadh?ar|aadhaar).{0,40}(link|verify|update|expir|mandator|fail)",
    r"\b(sbi|icici|hdfc|axis|kotak|pnb|bob|canara|union\s*bank).{0,30}(block|suspend|alert|verify|update)",
    r"\b(dear\s+customer|dear\s+user|valued\s+customer|dear\s+member)\b",
    r"\b(bank\s+(account|details|info))\b",

    # URL/Link patterns
    r"https?://bit\.ly/\S+",
    r"https?://tinyurl\.\S+",
    r"https?://\S+\.xyz\b",
    r"https?://\S+\.tk\b",
    r"https?://\S+\.ml\b",
    r"https?://\S+\.top\b",
    r"https?://\S+\.buzz\b",
    r"https?://\S+\.click\b",
    r"https?://\S+\.link\b",
    r"https?://\d+\.\d+\.\d+\.\d+",  # IP-based URLs

    # OTP/Code theft
    r"\b(otp|one.time.password|verification\s+code)\b",
    r"\bshare\s+(your\s+)?(otp|code|pin)\b",
    r"\b(do\s+not|don'?t)\s+share\s+(this|your)\s+(otp|code|pin)\b",

    # Job/Offer scams
    r"\b(work\s+from\s+home|earn\s+from\s+home)\b.{0,30}(per\s+day|daily|monthly|weekly)",
    r"\b(earn\s+[₹$]\s*\d+|income\s+[₹$]\s*\d+)\b",
    r"\b(part.time\s+job|home.based\s+job)\b.{0,30}(earn|income|salary)",
    r"\b(guaranteed\s+(income|return|profit))\b",
    r"\b(investment\s+opportunity|double\s+your\s+money)\b",

    # Generic scam patterns
    r"\b(limited\s+time\s+offer|exclusive\s+offer|special\s+offer)\b",
    r"\b(act\s+fast|hurry\s+up|don'?t\s+miss)\b",
    r"\b(call\s+(this|now|us|me)\s*(at|on)?\s*[\d\-\+]+)\b",
    r"\b(whatsapp\s*(us|me|now|on)\s*[\d\-\+]+)\b",
    r"\b(send\s+money|transfer\s+money|pay\s+now)\b",
    r"\b(refund|cashback).{0,30}(click|link|verify|process)\b",
    r"\b(delivery\s+(fail|attempt)|package\s+(held|stuck|returned))\b",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in PHISHING_KEYWORDS]


class PhishingModel:
    """
    Enhanced phishing/scam NLP classifier with comprehensive pattern matching.
    Catches SMS scams, UPI fraud, KYC phishing, lottery scams, and more.
    """

    def classify(self, text: str) -> Tuple[str, float, float]:
        """Classify text into a threat label with score and confidence."""
        return self._classify_with_heuristics(text)

    def _classify_with_heuristics(self, text: str) -> Tuple[str, float, float]:
        """Enhanced keyword-regex heuristic classifier."""
        matches = sum(1 for p in COMPILED_PATTERNS if p.search(text))
        total_patterns = len(COMPILED_PATTERNS)

        # Aggressive scoring: even 1 match should flag as suspicious
        # 1 match = medium risk, 2+ = high, 4+ = critical
        if matches >= 6:
            nlp_score = min(98.0, 70.0 + matches * 4.0)
        elif matches >= 4:
            nlp_score = min(90.0, 60.0 + matches * 6.0)
        elif matches >= 2:
            nlp_score = min(80.0, 45.0 + matches * 10.0)
        elif matches >= 1:
            nlp_score = 50.0
        else:
            nlp_score = 0.0

        nlp_score = round(nlp_score, 2)
        confidence = round(min(matches / 3.0, 1.0), 4)

        # Determine label based on which patterns matched
        label = self._determine_label(text, nlp_score)

        logger.info(
            f"NLP heuristic: matches={matches}/{total_patterns}, "
            f"score={nlp_score}, label={label}"
        )

        return label, nlp_score, confidence

    def _determine_label(self, text: str, score: float) -> str:
        """Determine the most specific threat label based on content."""
        text_lower = text.lower()

        if score < 10:
            return "safe"

        # Check for specific scam types
        if re.search(r"(kyc|pan\s*card|aadh?ar|aadhaar).{0,30}(expir|update|verify|suspend)", text_lower):
            return "kyc_scam"
        if re.search(r"(won|winner|prize|lottery|lucky\s+draw|claim\s+your)", text_lower):
            return "lottery_scam"
        if re.search(r"(upi|paytm|phonepe|gpay|bank).{0,30}(block|suspend|verify|transfer)", text_lower):
            return "financial_fraud"
        if re.search(r"(password|otp|pin|code|credential).{0,30}(verify|confirm|share|enter|provide)", text_lower):
            return "credential_theft"
        if re.search(r"https?://\S+", text_lower) and score >= 30:
            return "malicious_link"
        if re.search(r"(verify|confirm|update).{0,30}(account|identity|details)", text_lower):
            return "phishing"

        if score >= 60:
            return "scam"
        elif score >= 30:
            return "impersonation"
        else:
            return "safe"


# ─── Singleton ────────────────────────────────────────────────────────────────
phishing_model = PhishingModel()
