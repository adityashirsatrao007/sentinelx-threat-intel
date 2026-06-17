"""
Behavioral Analysis Engine
Detects social engineering tactics, urgency manipulation, authority impersonation,
emotional pressure, and other psychological attack patterns in text.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)

# ─── Behavioral Pattern Definitions ──────────────────────────────────────────

BEHAVIOR_PATTERNS: Dict[str, List[str]] = {
    "urgency": [
        r"\b(urgent(ly)?|immediately|right now|act now|as soon as possible|asap)\b",
        r"\b(expires?\s+(today|soon|in\s+\d+\s+hour))\b",
        r"\b(last\s+(chance|opportunity|warning))\b",
        r"\b(deadline|time.sensitive|limited\s+time)\b",
    ],
    "authority_impersonation": [
        r"\b(irs|fbi|cia|police|government|court|official|legal\s+action)\b",
        r"\b(paypal|amazon|apple|microsoft|google|bank\s+of\s+america)\b",
        r"\b(your\s+(bank|financial\s+institution)|customer\s+service|support\s+team)\b",
        r"\b(ceo|president|director|manager)\s+(of|at)\b",
    ],
    "emotional_pressure": [
        r"\b(don'?t\s+(panic|worry|be\s+alarmed)|please\s+help)\b",
        r"\b(desperate(ly)?|emergency|crisis|life.or.death)\b",
        r"\b(loved\s+one|family\s+member|child|daughter|son)\b",
        r"\b(scared|afraid|terrified|shocked)\b",
    ],
    "credential_request": [
        r"\b(enter|provide|confirm|verify)\b.{0,30}\b(password|pin|code|otp)\b",
        r"\b(your\s+(social\s+security|ssn|passport|id\s+number))\b",
        r"\b(credit\s+card|cvv|card\s+number|expir(y|ation))\b",
        r"\b(bank\s+(account|routing)\s+number)\b",
    ],
    "manipulation_tactics": [
        r"\b(you('ve| have) been\s+(selected|chosen|approved))\b",
        r"\b(exclusively?\s+for\s+you)\b",
        r"\b(no\s+one\s+else\s+(knows|can\s+help))\b",
        r"\b(keep\s+(this\s+)?(secret|confidential|private))\b",
    ],
    "fear_language": [
        r"\b(arrest(ed)?|jail|prison|criminal|lawsuit|prosecut\w+)\b",
        r"\b(account\s+(suspend|block|terminat|clos)\w+)\b",
        r"\b(service\s+(terminat|discontinu)\w+)\b",
        r"\b(legal\s+(proceed|action|consequence)\w*)\b",
    ],
    "reward_luring": [
        r"\b(you('ve| have)? won|winner|congratulation)\b",
        r"\b(free\s+(gift|money|prize|trip|vacation|iphone))\b",
        r"\b(claim\s+(your\s+)?(prize|reward|gift|bonus))\b",
        r"\b(\$\d[\d,]+\s+(reward|cash|bonus|prize))\b",
    ],
    "corporate_spoofing": [
        r"\b(it\s+support|help\s*desk|system\s+administrator|network\s+security)\b",
        r"\b(human\s+resources|hr\s+department|payroll\s+update|benefit\s+enrollment)\b",
        r"\b(internal\s+memo|company\s+policy|mandatory\s+training|action\s+required)\b",
        r"\b(microsoft\s+365\s+update|outlook\s+web\s+access|owa\s+login|vpn\s+credential)\b",
    ],
    "financial_coercion": [
        r"\b(invoice\s+(overdue|pending|query)|payment\s+remittance|purchase\s+order)\b",
        r"\b(wire\s+transfer|ach\s+payment|bank\s+transfer\s+request|swift\s+code)\b",
        r"\b(fiscal\s+quarter|audit\s+report|tax\s+filing|accountant)\b",
        r"\b(unpaid\s+balance|collection\s+agency|final\s+notice)\b",
    ],
}

# Weight each category contributes to behavioral score
CATEGORY_WEIGHTS: Dict[str, float] = {
    "urgency": 15.0,
    "authority_impersonation": 20.0,
    "emotional_pressure": 15.0,
    "credential_request": 25.0,
    "manipulation_tactics": 10.0,
    "fear_language": 10.0,
    "reward_luring": 5.0,
    "corporate_spoofing": 25.0,
    "financial_coercion": 20.0,
}

# Pre-compile all patterns
COMPILED_BEHAVIORS: Dict[str, List[re.Pattern]] = {
    category: [re.compile(p, re.IGNORECASE) for p in patterns]
    for category, patterns in BEHAVIOR_PATTERNS.items()
}


@dataclass
class BehaviorAnalysisResult:
    behavioral_score: float
    detected_categories: List[str] = field(default_factory=list)
    reasons: List[str] = field(default_factory=list)
    hit_counts: Dict[str, int] = field(default_factory=dict)


class BehaviorModel:
    """
    Rule-based behavioral analysis engine.

    Scores text against psychological attack patterns used in social engineering,
    phishing, and scam communications.
    """

    def analyze(self, text: str) -> BehaviorAnalysisResult:
        """
        Analyze text for behavioral threat indicators.

        Returns:
            BehaviorAnalysisResult with score (0-100) and detected categories.
        """
        total_score = 0.0
        detected: List[str] = []
        reasons: List[str] = []
        hit_counts: Dict[str, int] = {}

        for category, patterns in COMPILED_BEHAVIORS.items():
            hits = sum(1 for p in patterns if p.search(text))
            if hits > 0:
                hit_counts[category] = hits
                detected.append(category)
                weight = CATEGORY_WEIGHTS.get(category, 10.0)
                # Diminishing returns: first hit = full weight, subsequent = 50%
                contribution = weight + (hits - 1) * weight * 0.5
                total_score += contribution
                reasons.append(
                    self._format_reason(category, hits)
                )

        behavioral_score = round(min(total_score, 100.0), 2)

        return BehaviorAnalysisResult(
            behavioral_score=behavioral_score,
            detected_categories=detected,
            reasons=reasons,
            hit_counts=hit_counts,
        )

    @staticmethod
    def _format_reason(category: str, hits: int) -> str:
        """Convert internal category name to human-readable reason string."""
        mapping = {
            "urgency": "Urgency manipulation tactics detected",
            "authority_impersonation": "Authority or brand impersonation detected",
            "emotional_pressure": "Emotional pressure / distress language detected",
            "credential_request": "Credential or sensitive data request detected",
            "manipulation_tactics": "Psychological manipulation tactics detected",
            "fear_language": "Fear-inducing legal or account threat language detected",
            "reward_luring": "Reward luring / prize scam language detected",
            "corporate_spoofing": "Internal corporate impersonation (IT/HR) detected",
            "financial_coercion": "Financial coercion / fraudulent invoice language detected",
        }
        base = mapping.get(category, category.replace("_", " ").title())
        return f"{base} ({hits} indicator{'s' if hits > 1 else ''})"


behavior_model = BehaviorModel()
