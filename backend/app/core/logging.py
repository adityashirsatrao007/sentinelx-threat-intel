"""
SentinelX Logging Configuration
Structured JSON-format logging for production observability.
"""

import logging
import sys
import json
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Emit log records as single-line JSON for log aggregators."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging() -> None:
    """Configure root logger with appropriate handler and formatter."""
    handler = logging.StreamHandler(sys.stdout)

    if settings.LOG_FORMAT == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        )

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(level=log_level, handlers=[handler])

    # Quiet noisy third-party loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger instance."""
    return logging.getLogger(name)
