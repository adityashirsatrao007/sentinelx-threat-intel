"""
Risk Analysis Service
High-level orchestration entry point for risk computation (used by Celery tasks).
"""

from __future__ import annotations

from app.ml.risk_engine import risk_engine, RiskScoreResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class RiskService:
    """Thin wrapper around risk_engine for service-layer consistency."""

    def score(
        self,
        nlp_score: float,
        behavior_score: float,
        url_score: float,
        reputation_score: float,
        nlp_label: str,
        nlp_confidence: float,
        behavior_reasons: list,
        url_reasons: list,
    ) -> RiskScoreResult:
        return risk_engine.compute(
            nlp_score=nlp_score,
            behavior_score=behavior_score,
            url_score=url_score,
            reputation_score=reputation_score,
            nlp_label=nlp_label,
            nlp_confidence=nlp_confidence,
            behavior_reasons=behavior_reasons,
            url_reasons=url_reasons,
        )


risk_service = RiskService()
