"""
OpenAI Whisper Speech-to-Text Service
Uses Hugging Face Inference API exclusively (no local models).
"""

from __future__ import annotations

from typing import Optional, Tuple
import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class WhisperService:
    """
    Wraps OpenAI Whisper for speech-to-text transcription.
    Uses Hugging Face Inference API exclusively — no local model loading.
    """

    def __init__(self) -> None:
        self.api_token = settings.HF_API_TOKEN
        self.hf_model_url = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"

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
                return transcript, None, None

        except Exception as e:
            logger.error(f"HF Whisper inference failed: {e}")
            return None

    def transcribe_file(self, file_path: str) -> Tuple[str, Optional[str], Optional[float]]:
        """
        Transcribe an audio file (Synchronous).
        Requires HF API token.
        """
        if not self.api_token:
            raise RuntimeError("HF_API_TOKEN not configured. Cannot transcribe without Hugging Face Inference API.")

        with open(file_path, "rb") as f:
            audio_bytes = f.read()

        headers = {"Authorization": f"Bearer {self.api_token}"}
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(self.hf_model_url, headers=headers, content=audio_bytes)
                if response.status_code == 200:
                    result = response.json()
                    return result.get("text", "").strip(), None, None
                raise RuntimeError(f"HF Whisper API error: {response.status_code} - {response.text}")
        except Exception as e:
            logger.error(f"HF Whisper sync inference failed: {e}")
            raise

    async def transcribe_upload(self, audio_bytes: bytes, filename: str) -> Tuple[str, Optional[str], Optional[float]]:
        """
        Transcribe audio from uploaded bytes via HF Inference API.
        """
        if not self.api_token:
            raise RuntimeError("HF_API_TOKEN not configured. Cannot transcribe without Hugging Face Inference API.")

        result = await self._transcribe_via_hf(audio_bytes)
        if result:
            return result

        raise RuntimeError("Whisper transcription failed via HF Inference API.")


whisper_service = WhisperService()
