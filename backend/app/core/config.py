"""
SentinelX Core Configuration
Loads all settings from environment variables or .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # ─── Application ──────────────────────────────────────────────────────────
    APP_NAME: str = "SentinelX"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENV: str = "production"

    # ─── Server ───────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # ─── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://sentinelx:sentinelx_pass@postgres:5432/sentinelx_db"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ─── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/1"

    # ─── JWT ──────────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-256-bit-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ─── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # ─── Risk Scoring Thresholds ──────────────────────────────────────────────
    RISK_THRESHOLD_LOW: float = 3.0
    RISK_THRESHOLD_MEDIUM: float = 6.0
    RISK_THRESHOLD_HIGH: float = 8.5
    ALERT_TRIGGER_THRESHOLD: float = 3.1  # Trigger alert if score >= this (flags MEDIUM+)

    # ─── Risk Scoring Weights ─────────────────────────────────────────────────
    WEIGHT_NLP: float = 0.35
    WEIGHT_BEHAVIOR: float = 0.25
    WEIGHT_URL: float = 0.20
    WEIGHT_REPUTATION: float = 0.20

    # ─── ML Models ────────────────────────────────────────────────────────────
    NLP_MODEL_NAME: str = "distilbert-base-uncased"
    WHISPER_MODEL_SIZE: str = "base"  # tiny | base | small | medium | large
    ML_CACHE_DIR: str = "/app/ml_cache"
    USE_GPU: bool = False

    # ─── External APIs (Optional) ─────────────────────────────────────────────
    VIRUSTOTAL_API_KEY: Optional[str] = None
    PHISHTANK_API_KEY: Optional[str] = None
    HF_API_TOKEN: Optional[str] = None

    # ─── Gmail (Optional) ─────────────────────────────────────────────────────
    GMAIL_CLIENT_ID: Optional[str] = None
    GMAIL_CLIENT_SECRET: Optional[str] = None
    GMAIL_REDIRECT_URI: str = "http://localhost:8000/api/v1/gmail/callback"
    FRONTEND_URL: str = "https://sentinelx-frontend-nu.vercel.app"

    # ─── Polling ──────────────────────────────────────────────────────────────
    GMAIL_POLL_INTERVAL_SECONDS: int = 60  # How often Celery polls Gmail

    # ─── Rate Limiting ────────────────────────────────────────────────────────
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # ─── Logging ──────────────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
