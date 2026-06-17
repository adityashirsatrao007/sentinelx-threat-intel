"""
Request Logging Middleware
Logs every HTTP request/response with timing for observability.
"""

from __future__ import annotations

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger("sentinelx.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs structured request/response data for every API call.

    Fields logged:
        - request_id (UUID)
        - method, path, status_code
        - response time (ms)
        - client IP
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())
        start = time.perf_counter()

        # Attach request_id so handlers can log it
        request.state.request_id = request_id

        response: Response = await call_next(request)

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        logger.info(
            {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": request.client.host if request.client else "unknown",
            }
        )

        # Expose request ID in response headers for tracing
        response.headers["X-Request-ID"] = request_id
        return response
