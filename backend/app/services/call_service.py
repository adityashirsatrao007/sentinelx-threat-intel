"""
Call Transcript Analysis Service
Analyzes phone call transcripts (or Whisper-transcribed audio) for scam patterns.
"""

from __future__ import annotations

from typing import Optional
import uuid

from sqlalchemy.orm import Session

from app.ml.phishing_model import phishing_model
from app.ml.behavior_model import behavior_model
from app.ml.url_detector import url_detector
from app.ml.risk_engine import risk_engine
from app.ml.whisper_service import whisper_service
from app.database.models.models import Threat, ThreatType, ThreatLevel
from app.schemas.schemas import CallAnalysisRequest, ThreatAnalysisResponse, TranscriptionResponse
from app.core.logging import get_logger

logger = get_logger(__name__)


class CallService:
    """Handles call transcript analysis and audio-to-text transcription."""

    def analyze_transcript(
        self,
        request: CallAnalysisRequest,
        db: Session,
        user_id: Optional[uuid.UUID] = None,
    ) -> ThreatAnalysisResponse:
        """
        Analyze a phone call transcript for scam patterns.

        Pipeline mirrors email analysis but uses caller-specific reputation scoring.
        """
        transcript = request.transcript

        # ── Step 1: NLP Classification ─────────────────────────────────────
        nlp_label, nlp_score, nlp_confidence = phishing_model.classify(transcript)

        # ── Step 2: Behavioral Analysis (high weight for calls) ────────────
        behavior_result = behavior_model.analyze(transcript)

        # ── Step 3: URL Analysis ──────────────────────────────────────────
        extracted_urls, url_score, url_reasons = url_detector.analyze_all(transcript)

        # ── Step 4: Caller Reputation ─────────────────────────────────────
        reputation_score = 0.0
        if request.caller_id:
            reputation_score = risk_engine.compute_reputation_score(
                request.caller_id, channel="sms"  # reuse phone heuristics
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

        # ── Step 6: Persist ────────────────────────────────────────────────
        threat = Threat(
            type=ThreatType.call,
            channel="call",
            sender=request.caller_id,
            content=transcript[:2000],
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
            created_by=user_id,
        )
        db.add(threat)
        db.commit()
        db.refresh(threat)

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

    async def transcribe_audio(
        self, audio_bytes: bytes, filename: str
    ) -> TranscriptionResponse:
        """Transcribe audio bytes using Whisper and return transcript."""
        transcript, language, duration = await whisper_service.transcribe_upload(
            audio_bytes, filename
        )
        return TranscriptionResponse(
            transcript=transcript,
            language=language,
            duration_seconds=duration,
        )


call_service = CallService()
