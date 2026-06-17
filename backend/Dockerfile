# ─── SentinelX Backend Dockerfile ────────────────────────────────────────────
# Multi-stage build for smaller production image

FROM python:3.11-slim AS base

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ─── Dependencies layer (cached unless requirements.txt changes) ───────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ─── Application source ───────────────────────────────────────────────────
COPY . .

# Create ML model cache directory
RUN mkdir -p /app/ml_cache

# Create non-root user for security
RUN useradd -m -u 1001 sentinelx && chown -R sentinelx:sentinelx /app
USER sentinelx

# ─── Expose port ──────────────────────────────────────────────────────────
EXPOSE 8000

# ─── Default command: start Uvicorn ───────────────────────────────────────
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2 --no-access-log"]
