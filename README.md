# 🛡️ SentinelX — AI-Powered Real-Time Threat Detection Platform

<div align="center">

![SentinelX](https://img.shields.io/badge/SentinelX-v1.0.0-blueviolet?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=for-the-badge&logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?style=for-the-badge&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?style=for-the-badge&logo=redis)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker)

**Production-grade AI cybersecurity backend detecting phishing, scams, and social engineering in real-time.**

[API Docs](#api-documentation) • [Architecture](#architecture) • [Setup](#quick-start) • [Docker](#docker-deployment)

</div>

---

## Overview

SentinelX is a modular, AI-ready backend platform that continuously monitors communication streams — email, SMS, messaging, and phone calls — to detect malicious intent before credential theft or system compromise occurs.

### Key Capabilities

| Feature | Technology |
|---------|-----------|
| NLP Phishing Detection | HuggingFace DistilBERT / Zero-Shot Classification |
| Behavioral Analysis | Rule-based social engineering pattern engine |
| URL Threat Scoring | Regex heuristics + optional VirusTotal API |
| Speech-to-Text | OpenAI Whisper (tiny → large models) |
| Risk Scoring | Weighted multi-signal composite engine |
| Async Processing | Celery + Redis task queues |
| Authentication | JWT + bcrypt + RBAC |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| Containerization | Docker + Docker Compose |

---

## Architecture

```
SentinelX Backend
│
├── app/
│   ├── api/
│   │   ├── routes/          # FastAPI route handlers
│   │   │   ├── auth.py      # POST /auth/register, /login, GET /me
│   │   │   ├── analyze.py   # POST /analyze/{email,sms,call}, /transcribe/audio
│   │   │   ├── alerts.py    # GET /alerts, POST /alerts/{id}/acknowledge
│   │   │   └── dashboard.py # GET /dashboard/{stats,threats,trends}
│   │   ├── dependencies/    # Auth dependency injectors
│   │   └── middleware/      # Request logging, tracing
│   │
│   ├── core/
│   │   ├── config.py        # Pydantic Settings (env vars)
│   │   ├── security.py      # JWT + bcrypt
│   │   └── logging.py       # Structured JSON logging
│   │
│   ├── database/
│   │   ├── base.py          # SQLAlchemy DeclarativeBase
│   │   ├── session.py       # Engine + session factory
│   │   └── models/          # User, Threat, Alert, AuditLog
│   │
│   ├── schemas/             # Pydantic request/response models
│   │
│   ├── services/            # Business logic orchestration
│   │   ├── email_service.py
│   │   ├── sms_service.py
│   │   ├── call_service.py
│   │   ├── alert_service.py
│   │   ├── risk_service.py
│   │   └── dashboard_service.py
│   │
│   ├── ml/                  # AI/ML inference layer
│   │   ├── phishing_model.py  # HuggingFace zero-shot classifier
│   │   ├── sms_model.py       # SMS-specific scam detector
│   │   ├── url_detector.py    # URL threat analysis
│   │   ├── behavior_model.py  # Social engineering pattern engine
│   │   ├── whisper_service.py # Speech-to-text
│   │   └── risk_engine.py     # Composite risk scorer
│   │
│   ├── workers/
│   │   └── celery_worker.py   # Async task definitions
│   │
│   └── main.py              # FastAPI app entry point
│
├── alembic/                 # Database migrations
├── Dockerfile
├── requirements.txt
└── .env.example
```

### Risk Scoring Formula

```
RiskScore = 0.35 × NLPScore
          + 0.25 × BehaviorScore
          + 0.20 × URLScore
          + 0.20 × ReputationScore
```

| Score Range | Threat Level |
|-------------|-------------|
| 0 – 30      | 🟢 LOW      |
| 31 – 60     | 🟡 MEDIUM   |
| 61 – 85     | 🟠 HIGH     |
| 86 – 100    | 🔴 CRITICAL |

---

## Quick Start

### Prerequisites

- Docker ≥ 24.0 + Docker Compose ≥ 2.0
- OR: Python 3.11+, PostgreSQL 16, Redis 7

### 1. Clone and Configure

```bash
git clone https://github.com/your-org/SentinelX.git
cd SentinelX

# Create environment file
cp backend/.env.example backend/.env

# IMPORTANT: Generate a secure JWT secret key
python -c "import secrets; print(secrets.token_hex(32))"
# Paste the output as SECRET_KEY in backend/.env
```

### 2. Edit `backend/.env`

```env
SECRET_KEY=your-generated-256-bit-key-here
DATABASE_URL=postgresql://sentinelx:sentinelx_pass@postgres:5432/sentinelx_db
REDIS_URL=redis://redis:6379/0
```

---

## Docker Deployment

### Start All Services

```bash
docker-compose up --build
```

This starts:
- **PostgreSQL** on port 5432
- **Redis** on port 6379
- **FastAPI backend** on port 8000
- **Celery worker** (email, sms, call queues)

### Access the API

| Interface | URL |
|-----------|-----|
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Health Check | http://localhost:8000/health |

### Start with Celery Flower monitoring

```bash
docker-compose --profile monitoring up --build
# Flower dashboard at http://localhost:5555
```

### Useful Commands

```bash
# View backend logs
docker-compose logs -f backend

# View Celery worker logs
docker-compose logs -f celery_worker

# Run database migrations
docker-compose exec backend alembic upgrade head

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## Local Development (Without Docker)

```bash
# 1. Create virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
cp .env.example .env
# Edit .env with local DATABASE_URL and REDIS_URL

# 4. Run database migrations
alembic upgrade head

# 5. Start the API server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. In a separate terminal, start Celery worker
celery -A app.workers.celery_worker.celery_app worker --loglevel=info
```

---

## API Documentation

All endpoints are prefixed with `/api/v1`.

### 🔐 Authentication

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| `POST` | `/api/v1/auth/register` | Create a new user | No |
| `POST` | `/api/v1/auth/login` | Get JWT access token | No |
| `GET` | `/api/v1/auth/me` | Get current user profile | Yes |

#### Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "SecurePass123",
    "role": "operator"
  }'
```

#### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "SecurePass123"}'
```

Response:
```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

### 🔍 Threat Analysis

All analysis endpoints require `Authorization: Bearer <token>`.

#### Analyze Email

```bash
curl -X POST http://localhost:8000/api/v1/analyze/email \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "security@paypa1-alert.xyz",
    "subject": "URGENT: Your account has been suspended",
    "body": "Click here immediately to verify your account and avoid permanent suspension."
  }'
```

Response:
```json
{
  "threat_id": "550e8400-e29b-41d4-a716-446655440000",
  "threat_detected": true,
  "risk_score": 87.4,
  "threat_level": "CRITICAL",
  "confidence": 0.92,
  "classification_label": "phishing",
  "reasons": [
    "NLP classified as 'phishing' (score: 91.0)",
    "Urgency manipulation tactics detected (2 indicators)",
    "Authority or brand impersonation detected (1 indicator)",
    "Suspicious TLD (.xyz)"
  ],
  "extracted_urls": [],
  "nlp_score": 91.0,
  "behavior_score": 78.5,
  "url_score": 25.0,
  "reputation_score": 60.0,
  "processing_mode": "sync"
}
```

#### Analyze SMS

```bash
curl -X POST http://localhost:8000/api/v1/analyze/sms \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "+91XXXXXXXXXX",
    "message": "Congratulations! You won a free iPhone. Claim now: https://bit.ly/abc123"
  }'
```

#### Analyze Call Transcript

```bash
curl -X POST http://localhost:8000/api/v1/analyze/call \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "transcript": "Hello this is IRS. You owe taxes. Pay now or you will be arrested.",
    "caller_id": "+18005551234",
    "duration_seconds": 120
  }'
```

#### Transcribe Audio File (Whisper)

```bash
curl -X POST http://localhost:8000/api/v1/transcribe/audio \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/call_recording.mp3"
```

#### Async Processing

Pass `"async_processing": true` to any analysis endpoint to queue via Celery:

```json
{
  "sender": "...",
  "subject": "...",
  "body": "...",
  "async_processing": true
}
```

Response includes `task_id` for polling via Celery result backend.

---

### 🚨 Alerts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/alerts` | List alerts (paginated) |
| `POST` | `/api/v1/alerts/{id}/acknowledge` | Acknowledge an alert |

```bash
# Get unacknowledged alerts
curl http://localhost:8000/api/v1/alerts?unacknowledged_only=true \
  -H "Authorization: Bearer <token>"

# Acknowledge an alert
curl -X POST http://localhost:8000/api/v1/alerts/550e8400.../acknowledge \
  -H "Authorization: Bearer <token>"
```

---

### 📊 Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/dashboard/stats` | KPI statistics |
| `GET` | `/api/v1/dashboard/threats` | Recent threats list |
| `GET` | `/api/v1/dashboard/trends` | Daily trends (past N days) |

```bash
# Get KPI stats
curl http://localhost:8000/api/v1/dashboard/stats \
  -H "Authorization: Bearer <token>"

# Get 14-day trends
curl "http://localhost:8000/api/v1/dashboard/trends?days=14" \
  -H "Authorization: Bearer <token>"
```

---

## Database Migrations (Alembic)

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "add_new_field"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1

# View current migration status
alembic current
```

---

## ML Models

### NLP Classifier (HuggingFace)

The system uses **DistilBERT** in zero-shot classification mode by default.

Classification labels:
- `safe` — No threat detected
- `phishing` — Phishing attempt
- `scam` — General scam
- `credential_theft` — Targeting credentials
- `malicious_link` — Contains malicious URLs
- `impersonation` — Identity spoofing

**Fallback**: If HuggingFace is unavailable, the system automatically falls back to regex keyword heuristics.

### Whisper Models

Configure model size in `.env`:

| Model | VRAM | Speed | Accuracy |
|-------|------|-------|----------|
| `tiny` | ~1 GB | ~32x | Good |
| `base` | ~1 GB | ~16x | Better |
| `small` | ~2 GB | ~6x | Great |
| `medium` | ~5 GB | ~2x | Excellent |
| `large` | ~10 GB | 1x | Best |

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | — | **Required.** 256-bit JWT signing key |
| `DATABASE_URL` | — | PostgreSQL connection string |
| `REDIS_URL` | — | Redis connection string |
| `NLP_MODEL_NAME` | `distilbert-base-uncased` | HuggingFace model name |
| `WHISPER_MODEL_SIZE` | `base` | Whisper model variant |
| `ALERT_TRIGGER_THRESHOLD` | `61` | Min risk score to generate alert |
| `VIRUSTOTAL_API_KEY` | — | Optional VirusTotal API key |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## Security Considerations

- **JWT Keys**: Always generate a unique `SECRET_KEY` per environment
- **Password Hashing**: bcrypt with 12 rounds
- **Rate Limiting**: 100 requests/minute per IP (configurable)
- **CORS**: Restricted to configured origins
- **Non-root Docker**: Container runs as `sentinelx` user (UID 1001)
- **Input Sanitization**: Pydantic v2 strict validation on all inputs
- **Content Truncation**: Email/SMS body stored as 2000-char excerpts

---

## Future Roadmap

- [ ] Kafka integration for real-time stream processing
- [ ] WebSocket push notifications for live alerts
- [ ] Multilingual support (Whisper multi-language + multilingual NLP)
- [ ] Deepfake voice detection pipeline
- [ ] MITRE ATT&CK framework mapping
- [ ] SOC integration (Splunk, Elastic SIEM)
- [ ] AI voice agent detection
- [ ] Live telecom integrations (Twilio, Vonage)

---

## License

MIT License — See [LICENSE](LICENSE) for details.

---

<div align="center">
  <strong>Built with ❤️ for cybersecurity operators worldwide.</strong>
</div>
