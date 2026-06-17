"""
Database Session Management
Optimised for Neon serverless PostgreSQL (cloud, high-latency connections).
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import Generator

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ─── Engine ───────────────────────────────────────────────────────────────────
# Key tunables for Neon / any cloud PostgreSQL:
#
#   pool_size        = keep N connections warm at all times
#   max_overflow     = burst capacity on top of pool_size
#   pool_pre_ping    = validate connection before handing out (avoids stale-conn errors)
#   pool_recycle     = close & recreate connections older than N seconds
#                      (Neon drops idle connections after ~300s, so 280s is safe)
#   pool_timeout     = raise error if no connection available after N seconds
#   connect_args     = TCP keepalive settings to prevent Neon from killing idle sockets

connect_args = {
    "connect_timeout": 10,          # Fail fast if Neon is unreachable
    "keepalives": 1,                # Enable TCP keepalive
    "keepalives_idle": 60,          # Send keepalive after 60s of inactivity
    "keepalives_interval": 10,      # Retry keepalive every 10s
    "keepalives_count": 5,          # Drop connection after 5 failed keepalives
}

engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,                    # Neon free tier: max 5 simultaneous connections
    max_overflow=5,                 # Allow 5 extra burst connections
    pool_pre_ping=True,             # Validate connection health before use
    pool_recycle=280,               # Recycle connections before Neon times them out (300s)
    pool_timeout=15,                # Wait up to 15s for a connection from the pool
    echo=settings.DEBUG,
    connect_args=connect_args,
)

# ─── Session Factory ──────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,         # Don't re-query after commit (avoids extra round-trips)
)


# ─── Warm Up Pool on Startup ─────────────────────────────────────────────────
def warm_up_pool() -> None:
    """
    Pre-establish connections to Neon during app startup so the first
    real user request doesn't pay the TCP handshake cost.
    """
    try:
        connections = []
        for _ in range(3):          # Open 3 warm connections
            conn = engine.connect()
            connections.append(conn)
        for conn in connections:
            conn.close()            # Return them to the pool (not closed, just returned)
        logger.info("Database connection pool warmed up (3 connections).")
    except Exception as exc:
        logger.warning(f"Pool warm-up failed (non-fatal): {exc}")


# ─── Dependency ───────────────────────────────────────────────────────────────
def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and ensures cleanup.

    Usage:
        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
