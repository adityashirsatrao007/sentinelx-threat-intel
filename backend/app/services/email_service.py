"""
Email Threat Analysis Service
Orchestrates NLP, behavioral, URL, and reputation analysis for email inputs.
"""

from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.ml.phishing_model import phishing_model
from app.ml.behavior_model import behavior_model
from app.ml.url_detector import url_detector
from app.ml.risk_engine import risk_engine
from app.ml.llm_service import llm_service
from app.database.models.models import Threat, ThreatType, ThreatLevel
from app.schemas.schemas import EmailAnalysisRequest, ThreatAnalysisResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmailService:
    """Coordinates end-to-end email threat analysis pipeline."""

    def analyze(
        self,
        request: EmailAnalysisRequest,
        db: Session,
        user_id: Optional[uuid.UUID] = None,
    ) -> ThreatAnalysisResponse:
        """
        Analyze an email for phishing/scam threats.

        Pipeline:
          1. Combine subject + body for NLP classification
          2. Behavioral pattern analysis on full email text
          3. URL extraction and threat scoring
          4. Sender reputation scoring
          5. Weighted risk score computation
          6. Persist Threat record to DB
        """
        full_text = f"{request.subject}\n\n{request.body}"

        # ── Step 1: NLP Classification ─────────────────────────────────────
        nlp_label, nlp_score, nlp_confidence = phishing_model.classify(full_text)
        logger.info(f"Email NLP result: label={nlp_label}, score={nlp_score}")

        # ── Step 2: Behavioral Analysis ───────────────────────────────────
        behavior_result = behavior_model.analyze(full_text)

        # ── Step 3: URL Analysis ──────────────────────────────────────────
        extracted_urls, url_score, url_reasons = url_detector.analyze_all(full_text)

        # ── Step 4: Sender Reputation ─────────────────────────────────────
        reputation_score = risk_engine.compute_reputation_score(
            request.sender, channel="email"
        )

        # ── Step 5: Risk Score ────────────────────────────────────────────
        risk_result = risk_engine.compute(
            nlp_score=nlp_score,
            behavior_score=behavior_result.behavioral_score,
            url_score=url_score,
            reputation_score=reputation_score,
            nlp_label=nlp_label,
            nlp_confidence=nlp_confidence,
            behavior_reasons=behavior_result.reasons,
            url_reasons=url_reasons,
        )

        # ── Step 5b: LLM Deep Analysis (non-blocking) ────────────────
        try:
            llm_result = llm_service.analyze_threat(
                text=full_text,
                channel="email",
                sender=request.sender,
            )
            if llm_result and llm_result.get("assessment"):
                risk_result.reasons.append(f"AI Assessment: {llm_result['assessment']}")
                logger.info(f"LLM analysis added for email from {request.sender}")
        except Exception as llm_exc:
            logger.warning(f"LLM analysis skipped: {llm_exc}")

        # Override for Red Team manual demo attacks
        if getattr(request, 'force_risk_score', None) is not None:
            risk_result.risk_score = request.force_risk_score
            risk_result.threat_detected = True
            risk_result.threat_level = "CRITICAL" if request.force_risk_score >= 8.5 else ("HIGH" if request.force_risk_score >= 6.1 else "MEDIUM")
            risk_result.classification_label = "RED_TEAM_ATTACK"

        # ── Step 6: Persist Threat ────────────────────────────────────────
        threat = Threat(
            type=ThreatType.email,
            channel="email",
            sender=request.sender,
            subject=request.subject[:500],
            content=request.body[:2000],  # store excerpt only
            risk_score=risk_result.risk_score,
            nlp_score=nlp_score,
            behavior_score=behavior_result.behavioral_score,
            url_score=url_score,
            reputation_score=reputation_score,
            threat_level=ThreatLevel[risk_result.threat_level],
            threat_detected=risk_result.threat_detected,
            confidence=risk_result.confidence,
            reasons=risk_result.reasons,
            extracted_urls=extracted_urls,
            classification_label=nlp_label,
            target_department=request.target_department,
            target_role=request.target_role,
            created_by=user_id,
        )
        db.add(threat)
        db.commit()
        db.refresh(threat)

        logger.info(
            f"Email analysis complete: threat_id={threat.id}, "
            f"risk_score={risk_result.risk_score}, level={risk_result.threat_level}"
        )

        return ThreatAnalysisResponse(
            threat_id=threat.id,
            threat_detected=risk_result.threat_detected,
            risk_score=risk_result.risk_score,
            threat_level=risk_result.threat_level,
            confidence=risk_result.confidence,
            classification_label=nlp_label,
            reasons=risk_result.reasons,
            extracted_urls=extracted_urls,
            nlp_score=nlp_score,
            behavior_score=behavior_result.behavioral_score,
            url_score=url_score,
            reputation_score=reputation_score,
            processing_mode="sync",
        )


email_service = EmailService()
