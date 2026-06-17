"""
OpenAI Whisper Speech-to-Text Service
Supports both local execution and Hugging Face Inference API.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Optional, Tuple
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class WhisperService:
    """
    Wraps OpenAI Whisper for speech-to-text transcription.
    
    Prioritizes Hugging Face Inference API if HF_API_TOKEN is available,
    otherwise falls back to local execution.
    """

    def __init__(self) -> None:
        self._model = None
        self._loaded = False
        self.api_token = settings.HF_API_TOKEN
        self.hf_model_url = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"

    def _load_local(self) -> None:
        if self._loaded:
            return
        try:
            import whisper  # type: ignore

            logger.info(f"Loading local Whisper model '{settings.WHISPER_MODEL_SIZE}'…")
            self._model = whisper.load_model(
                settings.WHISPER_MODEL_SIZE,
                download_root=settings.ML_CACHE_DIR,
            )
            logger.info("Local Whisper model loaded successfully.")
        except Exception as exc:
            logger.error(f"Failed to load local Whisper model: {exc}")
        finally:
            self._loaded = True

    async def _transcribe_via_hf(self, audio_bytes: bytes) -> Optional[Tuple[str, Optional[str], Optional[float]]]:
        """Transcribe using Hugging Face Inference API."""
        if not self.api_token:
            return None

        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        try:
            logger.info(f"Transcribing via HF Inference API: {self.hf_model_url}")
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.hf_model_url,
                    headers=headers,
                    content=audio_bytes
                )
                
                if response.status_code != 200:
                    logger.error(f"HF Whisper API error: {response.status_code} - {response.text}")
                    return None
                
                result = response.json()
                transcript = result.get("text", "").strip()
                # API doesn't always return language/duration in the same format as local whisper
                return transcript, None, None

        except Exception as e:
            logger.error(f"HF Whisper inference failed: {e}")
            return None

    def transcribe_file(self, file_path: str) -> Tuple[str, Optional[str], Optional[float]]:
        """
        Transcribe an audio file (Synchronous).
        If HF token is available, it uses a sync request to the API.
        """
        if self.api_token:
            with open(file_path, "rb") as f:
                audio_bytes = f.read()
            
            # Using synchronous httpx for the sync method
            headers = {"Authorization": f"Bearer {self.api_token}"}
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(self.hf_model_url, headers=headers, content=audio_bytes)
                    if response.status_code == 200:
                        result = response.json()
                        return result.get("text", "").strip(), None, None
            except Exception as e:
                logger.error(f"HF Whisper sync inference failed: {e}")

        # Fallback to local
        self._load_local()
        if self._model is None:
            raise RuntimeError("Whisper model not available (Local load failed and API failed/skipped).")

        logger.info(f"Transcribing locally: {file_path}")
        result = self._model.transcribe(file_path, fp16=False)
        return result.get("text", "").strip(), result.get("language"), None

    async def transcribe_upload(self, audio_bytes: bytes, filename: str) -> Tuple[str, Optional[str], Optional[float]]:
        """
        Transcribe audio from uploaded bytes.
        Prioritizes HF Inference API.
        """
        # Try HF API first
        if self.api_token:
            result = await self._transcribe_via_hf(audio_bytes)
            if result:
                return result

        # Fallback to local (requires temp file)
        logger.info("Falling back to local Whisper transcription.")
        suffix = Path(filename).suffix or ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        try:
            return self.transcribe_file(tmp_path)
        finally:
            os.unlink(tmp_path)


whisper_service = WhisperService()
