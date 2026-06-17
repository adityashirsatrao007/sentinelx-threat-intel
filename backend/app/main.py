"""
SentinelX — AI-Powered Threat Detection Platform
FastAPI Application Entry Point
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
# from app.core.limiter import limiter
from app.core.logging import setup_logging, get_logger
from app.database.base import Base
from app.database.session import engine, warm_up_pool
from app.api.routes import auth, analyze, alerts, dashboard, gmail, users, remote, simple_email
from app.api.middleware.logging import RequestLoggingMiddleware

# ─── Initialise logging first ─────────────────────────────────────────────────
setup_logging()
logger = get_logger(__name__)


# ─── In-Process Gmail Polling Scheduler ──────────────────────────────────────

_scheduler = None

def _start_gmail_scheduler() -> None:
    """Start APScheduler for periodic Gmail polling (no Redis needed)."""
    global _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from app.services.polling_service import polling_service

        _scheduler = BackgroundScheduler(daemon=True)
        interval = getattr(settings, 'GMAIL_POLL_INTERVAL_SECONDS', 60)
        _scheduler.add_job(
            polling_service.poll_all_accounts,
            'interval',
            seconds=int(interval),
            id='gmail_poll',
            replace_existing=True,
            max_instances=1,
        )
        _scheduler.start()
        logger.info(f"Gmail polling scheduler started (every {interval}s, no Redis needed).")
    except Exception as exc:
        logger.warning(f"Could not start Gmail scheduler: {exc}. Gmail polling disabled.")


# ─── Lifespan (startup / shutdown) ───────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Create database tables on startup (idempotent)."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables verified / created.")
    warm_up_pool()   # Pre-establish connections so the first request isn't slow
    _start_gmail_scheduler()
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)
    logger.info(f"Shutting down {settings.APP_NAME}")


# ─── FastAPI Application ──────────────────────────────────────────────────────

app = FastAPI(
    title="SentinelX — AI Threat Detection API",
    description=(
        "Real-time AI-powered cybersecurity threat detection platform. "
        "Detects phishing, scam, social engineering, and malicious communications "
        "across email, SMS, messaging apps, and phone call transcripts."
    ),
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ─── Rate Limiting ────────────────────────────────────────────────────────────
# app.state.limiter = limiter
# app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins including mobile clients
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Allow all hosts including mobile devices on LAN
)

# ─── Request Logging ──────────────────────────────────────────────────────────
app.add_middleware(RequestLoggingMiddleware)

# ─── Security Headers ─────────────────────────────────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Content-Security-Policy (Permissive enough for development/docs but baseline security)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' cdn.jsdelivr.net fonts.googleapis.com; font-src 'self' fonts.gstatic.com; img-src 'self' data: https:;"
    return response

# ─── Global Exception Handler ─────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"success": False, "error": "Internal server error.", "detail": str(exc)},
    )


# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/api/v1")
app.include_router(analyze.router, prefix="/api/v1")
app.include_router(alerts.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(gmail.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(remote.router, prefix="/api/v1")
app.include_router(simple_email.router, prefix="/api/v1")


# ─── Health Check ─────────────────────────────────────────────────────────────

@app.get("/health", tags=["Health"], summary="Health check endpoint")
def health_check() -> dict:
    """Returns service health status."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENV,
    }


@app.get("/", include_in_schema=False)
def root() -> dict:
    return {"message": f"Welcome to {settings.APP_NAME}. Visit /docs for API documentation."}
