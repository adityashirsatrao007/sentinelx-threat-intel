"""
Threat Analysis Routes
POST /analyze/email   — Analyze email for phishing
POST /analyze/sms     — Analyze SMS for scams
POST /analyze/call    — Analyze call transcript
POST /transcribe/audio — Transcribe audio file via Whisper
"""


from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
import json
import os

from app.database.session import get_db
from app.database.models.models import User, Threat
from app.api.dependencies.auth import get_current_user
from app.services.email_service import email_service
from app.services.sms_service import sms_service
from app.services.call_service import call_service
from app.services.alert_service import alert_service
from app.schemas.schemas import (
    EmailAnalysisRequest,
    SMSAnalysisRequest,
    CallAnalysisRequest,
    ThreatAnalysisResponse,
    TranscriptionResponse,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["Threat Analysis"])

@router.post(
    "/analyze/email",
    response_model=ThreatAnalysisResponse,
    summary="Analyze an email for phishing and social engineering threats",
)
def analyze_email(
    request: Request,
    analysis_data: EmailAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ThreatAnalysisResponse:
    if analysis_data.async_processing:
        from app.workers.celery_worker import analyze_email_task
        task = analyze_email_task.apply_async(
            kwargs={
                "sender": analysis_data.sender,
                "subject": analysis_data.subject,
                "body": analysis_data.body,
                "user_id": str(current_user.id),
            }
        )
        return ThreatAnalysisResponse(
            threat_detected=False,
            risk_score=0.0,
            threat_level="PENDING",
            confidence=0.0,
            classification_label="pending",
            reasons=[],
            nlp_score=0.0,
            behavior_score=0.0,
            url_score=0.0,
            reputation_score=0.0,
            processing_mode="async",
            task_id=task.id,
        )

    result = email_service.analyze(analysis_data, db, user_id=current_user.id)

    if result.threat_id:
        threat = db.query(Threat).filter(Threat.id == result.threat_id).first()
        if threat:
            background_tasks.add_task(alert_service.maybe_create_alert, threat, db)

    return result

@router.post(
    "/analyze/sms",
    response_model=ThreatAnalysisResponse,
    summary="Analyze an SMS message for scam and phishing threats",
)
def analyze_sms(
    request: Request,
    analysis_data: SMSAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ThreatAnalysisResponse:
    if analysis_data.async_processing:
        from app.workers.celery_worker import analyze_sms_task
        task = analyze_sms_task.apply_async(
            kwargs={
                "sender": analysis_data.sender,
                "message": analysis_data.message,
                "user_id": str(current_user.id),
            }
        )
        return ThreatAnalysisResponse(
            threat_detected=False,
            risk_score=0.0,
            threat_level="PENDING",
            confidence=0.0,
            classification_label="pending",
            reasons=[],
            nlp_score=0.0,
            behavior_score=0.0,
            url_score=0.0,
            reputation_score=0.0,
            processing_mode="async",
            task_id=task.id,
        )

    result = sms_service.analyze(analysis_data, db, user_id=current_user.id)

    if result.threat_id:
        threat = db.query(Threat).filter(Threat.id == result.threat_id).first()
        if threat:
            background_tasks.add_task(alert_service.maybe_create_alert, threat, db)

    return result

@router.post(
    "/analyze/call",
    response_model=ThreatAnalysisResponse,
    summary="Analyze a phone call transcript for scam patterns",
)
def analyze_call(
    request: CallAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ThreatAnalysisResponse:
    result = call_service.analyze_transcript(request, db, user_id=current_user.id)

    if result.threat_id:
        threat = db.query(Threat).filter(Threat.id == result.threat_id).first()
        if threat:
            background_tasks.add_task(alert_service.maybe_create_alert, threat, db)

    return result

@router.post(
    "/transcribe/audio",
    response_model=TranscriptionResponse,
    summary="Transcribe an audio file using OpenAI Whisper",
)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file (wav, mp3, m4a, flac)"),
    current_user: User = Depends(get_current_user),
) -> TranscriptionResponse:
    MAX_SIZE = 25 * 1024 * 1024  # 25 MB
    audio_bytes = await file.read()
    if len(audio_bytes) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Audio file exceeds the 25 MB limit.",
        )

    try:
        return await call_service.transcribe_audio(audio_bytes, file.filename or "audio.wav")
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

@router.get(
    "/analyze/dataset-samples",
    summary="Fetch pre-scored emails from the Enron dataset from Good to Bad",
)
def get_dataset_samples(
    percentile: float = 0.5,
    current_user: User = Depends(get_current_user),
):
    """
    Returns an email from the pre-scored Enron dataset based on the requested severity percentile.
    percentile=0.0 -> Safest email (Good)
    percentile=1.0 -> Most dangerous email (Bad)
    """
    # Adjust path based on execution context
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    dataset_path = os.path.join(base_dir, "enron_scored_sample.json")
    
    if not os.path.exists(dataset_path):
        raise HTTPException(status_code=404, detail="Dataset not found. Please run prep_enron_dataset.py first.")
        
    with open(dataset_path, "r") as f:
        samples = json.load(f)
        
    if not samples:
        raise HTTPException(status_code=404, detail="Dataset is empty.")
        
    # Ensure percentile is clamped between 0 and 1
    percentile = max(0.0, min(1.0, percentile))
    
    # Calculate index based on percentile (dataset is pre-sorted from lowest to highest risk)
    target_idx = int(percentile * (len(samples) - 1))
    
    return samples[target_idx]
