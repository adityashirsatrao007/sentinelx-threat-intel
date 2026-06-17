"""
Risk Scoring Engine
Combines NLP, behavioral, URL, and reputation scores into a final risk score.
Scaled to a 1–10 band as per user requirements.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RiskScoreResult:
    risk_score: float          # 1–10 composite score
    threat_level: str          # LOW | MEDIUM | HIGH | CRITICAL
    threat_detected: bool
    confidence: float          # 0–1
    classification_label: str
    reasons: List[str]
    nlp_score: float
    behavior_score: float
    url_score: float
    reputation_score: float
    explanation: str


class RiskEngine:
    """
    Weighted risk scoring engine (Scaled 1–10).

    Formula:
        RawScore = 0.35 * NLP + 0.25 * Behavior + 0.20 * URL + 0.20 * Reputation
        FinalScore = RawScore / 10

    Threat Levels (Scaled):
        1.0–3.0   → LOW
        3.1–6.0   → MEDIUM
        6.1–8.5   → HIGH
        8.6–10.0  → CRITICAL
    """

    def compute(
        self,
        nlp_score: float,
        behavior_score: float,
        url_score: float,
        reputation_score: float,
        nlp_label: str,
        nlp_confidence: float,
        behavior_reasons: List[str],
        url_reasons: List[str],
    ) -> RiskScoreResult:
        """
        Compute composite risk score (1-10) and classify threat level.
        All sub-scores come in on a 0-100 scale, we scale to 1-10.
        """
        # Scale each sub-score from 0-100 to 0-10
        nlp_10 = nlp_score / 10.0
        beh_10 = behavior_score / 10.0
        url_10 = url_score / 10.0
        rep_10 = reputation_score / 10.0

        # Weighted composite (already on 0-10 scale)
        raw_score = (
            settings.WEIGHT_NLP * nlp_10
            + settings.WEIGHT_BEHAVIOR * beh_10
            + settings.WEIGHT_URL * url_10
            + settings.WEIGHT_REPUTATION * rep_10
        )

        # Boost: if ANY model flags it as dangerous, ensure minimum score
        # This prevents "2 out of 4 models say dangerous" from averaging to LOW
        max_sub = max(nlp_10, beh_10, url_10, rep_10)
        if max_sub >= 5.0 and raw_score < 4.0:
            raw_score = max(raw_score, max_sub * 0.7)
        
        # Label-based floor: known threat labels get minimum scores
        label_floors = {
            "phishing": 5.5,
            "scam": 5.0,
            "credential_theft": 7.0,
            "malicious_link": 5.0,
            "impersonation": 4.0,
            "financial_fraud": 6.5,
            "lottery_scam": 6.0,
            "kyc_scam": 6.5,
        }
        floor = label_floors.get(nlp_label, 1.0)
        raw_score = max(raw_score, floor)

        risk_score = round(max(1.0, min(raw_score, 10.0)), 2)

        # Threat level classification
        threat_level = self._classify_level(risk_score)
        threat_detected = risk_score >= settings.ALERT_TRIGGER_THRESHOLD

        # Combined confidence
        confidence = round(
            (nlp_confidence * 0.5)
            + (min(behavior_score / 100, 1.0) * 0.3)
            + (min(url_score / 100, 1.0) * 0.2),
            4,
        )

        # Merge reasons
        all_reasons: List[str] = []
        if nlp_label != "safe":
            all_reasons.append(f"NLP classified as '{nlp_label}' (score: {nlp_10:.1f}/10)")
        all_reasons.extend(behavior_reasons)
        all_reasons.extend(url_reasons)

        # Human-readable explanation
        explanation = self._generate_explanation(
            risk_score, threat_level, nlp_label, beh_10, url_10, rep_10
        )

        return RiskScoreResult(
            risk_score=risk_score,
            threat_level=threat_level,
            threat_detected=threat_detected,
            confidence=confidence,
            classification_label=nlp_label,
            reasons=all_reasons,
            nlp_score=round(nlp_10, 2),
            behavior_score=round(beh_10, 2),
            url_score=round(url_10, 2),
            reputation_score=round(rep_10, 2),
            explanation=explanation,
        )

    @staticmethod
    def _classify_level(score: float) -> str:
        if score <= settings.RISK_THRESHOLD_LOW:
            return "LOW"
        elif score <= settings.RISK_THRESHOLD_MEDIUM:
            return "MEDIUM"
        elif score <= settings.RISK_THRESHOLD_HIGH:
            return "HIGH"
        else:
            return "CRITICAL"

    @staticmethod
    def _generate_explanation(
        risk_score: float,
        threat_level: str,
        nlp_label: str,
        behavior_score: float,
        url_score: float,
        reputation_score: float,
    ) -> str:
        parts = [
            f"Overall risk level: {risk_score:.1f}/10 ({threat_level}).",
        ]
        if nlp_label != "safe":
            parts.append(f"NLP model identified content as '{nlp_label}'.")
        if behavior_score > 3.0:
            parts.append(f"Behavioral analysis detected social engineering indicators (level: {behavior_score:.1f}/10).")
        if url_score > 2.0:
            parts.append(f"Suspicious URL patterns found (level: {url_score:.1f}/10).")
        if reputation_score > 4.0:
            parts.append(f"Sender reputation is poor (level: {reputation_score:.1f}/10).")
        return " ".join(parts)

    def compute_reputation_score(self, sender: str, channel: str = "email") -> float:
        """
        Returns 0-100 internally, will be scaled by compute()
        """
        import re
        score = 0.0
        if channel == "email":
            disposable = {"tempmail.com", "guerrillamail.com", "mailinator.com", "throwaway.email", "yopmail.com", "sharklasers.com"}
            domain_match = re.search(r"@([\w.-]+)", sender)
            if domain_match:
                domain = domain_match.group(1).lower()
                if domain in disposable: score += 60.0
                local = sender.split("@")[0]
                digit_ratio = sum(c.isdigit() for c in local) / max(len(local), 1)
                if digit_ratio > 0.5: score += 20.0
                if len(local) > 20: score += 10.0
        elif channel == "sms":
            if re.match(r"^\+?[89]\d{9,}$", sender): score += 30.0
        return round(min(score, 100.0), 2)


risk_engine = RiskEngine()
