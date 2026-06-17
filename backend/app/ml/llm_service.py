"""
LLM Inference Service
Integrates Qwen 2.5 via Hugging Face Inference API for advanced threat analysis.
"""

from typing import Dict, Optional
import httpx
import json
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ─── Configuration ────────────────────────────────────────────────────────────
HF_INFERENCE_URL = "https://router.huggingface.co/v1/chat/completions"

SYSTEM_PROMPT = """
You are an expert cybersecurity analyst specialized in phishing and social engineering detection.
Your task is to analyze the provided text and determine if it represents a security threat.

Analyze for:
1. Phishing: Attempts to steal credentials or sensitive info.
2. Scam: Fraudulent schemes to obtain money.
3. Malicious Links: Pointers to dangerous websites.
4. Impersonation: Mimicking trusted brands or individuals.

Output your response in JSON format with the following fields:
- "label": One of ["safe", "phishing", "scam", "malicious_link", "impersonation", "credential_theft"]
- "risk_score": A number from 0 to 100
- "confidence": A number from 0 to 1
- "reason": A brief explanation of your finding (max 20 words)
"""

class LLMService:
    """
    Service to interact with LLMs via Hugging Face Inference API.
    Supports both async and sync calls.
    """

    def __init__(self) -> None:
        self.api_token = settings.HF_API_TOKEN
        self.model = "Qwen/Qwen2.5-7B-Instruct"
        self.enabled = bool(self.api_token)
        if not self.enabled:
            logger.warning("HF_API_TOKEN not set. Qwen LLM analysis will be disabled.")

    def _prepare_payload(self, text: str) -> dict:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this text: {text}"}
            ],
            "max_tokens": 500,
            "temperature": 0.1,
            "response_format": {"type": "json_object"}
        }

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    async def analyze_text_async(self, text: str) -> Optional[Dict]:
        """Async analysis using httpx.AsyncClient."""
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    HF_INFERENCE_URL,
                    headers=self._get_headers(),
                    json=self._prepare_payload(text)
                )
                return self._handle_response(response)
        except Exception as e:
            logger.error(f"LLM async inference failed: {e}")
            return None

    def analyze_text(self, text: str) -> Optional[Dict]:
        """Synchronous analysis using httpx.Client."""
        if not self.enabled:
            return None

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    HF_INFERENCE_URL,
                    headers=self._get_headers(),
                    json=self._prepare_payload(text)
                )
                return self._handle_response(response)
        except Exception as e:
            logger.error(f"LLM sync inference failed: {e}")
            return None

    def _handle_response(self, response: httpx.Response) -> Optional[Dict]:
        if response.status_code != 200:
            logger.error(f"HF API error: {response.status_code} - {response.text}")
            return None
        
        try:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            analysis = json.loads(content)
            logger.info(f"LLM analysis successful: {analysis.get('label')}")
            return analysis
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return None

# ─── Singleton ────────────────────────────────────────────────────────────────
llm_service = LLMService()
