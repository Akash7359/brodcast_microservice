# 📬 s2s-service-brodcast

> **Outbound Communications Microservice** — Email (SMTP) + SMS (Gupshup) via a single authenticated REST API.
> Python 3.11 · FastAPI 0.115 · PostgreSQL · Redis · Docker

[![CI](https://github.com/your-org/s2s-service-smtp/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/s2s-service-smtp/actions)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📑 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Request Flow](#request-flow)
- [Database Schema](#database-schema)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Local Setup (Docker)](#local-setup-docker)
  - [Local Setup (Manual)](#local-setup-manual)
- [Environment Variables](#environment-variables)
- [Running Tests](#running-tests)
- [Hash Authentication](#hash-authentication)
- [Rate Limiting](#rate-limiting)
- [Email Templates](#email-templates)
- [SMS Templates](#sms-templates)
- [Deployment](#deployment)
- [Comparison with Laravel Lumen Origin](#comparison-with-laravel-lumen-origin)
- [Contributing](#contributing)

---

## Overview

`s2s-service-brodcast` is an **async FastAPI microservice** for outbound communications. It consolidates email and SMS delivery behind a single authenticated endpoint, with full audit logging, HMAC request verification, and per-IP rate limiting.

It is a Python rewrite of an original Laravel Lumen service, preserving all functional behaviour while adopting modern async-first patterns.

---

## Features

| Feature | Detail |
|---|---|
| 📧 Email delivery | SMTP via `fastapi-mail` + dynamic Jinja2 HTML templates |
| 📱 SMS delivery | Gupshup REST API with config-driven `{#var#}` templates |
| 🔀 Dual-channel | Email + SMS dispatched in a single request |
| 🔐 HMAC auth | SHA-256 payload signing with timestamp expiry |
| ⏱ Rate limiting | Redis-backed, 10 req/min per IP (configurable) |
| 📋 Audit logging | Full request + response stored in `smtp_details` table |
| ⚡ Async I/O | asyncpg, httpx, redis.asyncio — non-blocking throughout |
| 📖 Auto docs | Swagger UI at `/docs`, ReDoc at `/redoc` |
| 🐳 Docker ready | `docker-compose up` starts API + Postgres + Redis |
| ✅ Tested | pytest-asyncio unit + integration test suite |

---

## Architecture

```
Client
  │
  ├─► GET  /test                         → Health check
  │
  └─► POST /v1/send-smtp
        │
        ├── [Middleware] RateLimitMiddleware   (Redis per-IP)
        ├── [Middleware] VerifyRequestHash     (HMAC-SHA256)
        │
        └── SMTPController.send_smtp()
              │
              ├── Validate payload (Pydantic v2)
              ├── Persist smtp_details (status=PENDING)
              ├── Lookup product_category_template_mapping
              │
              ├── channel=1 or 3 ──► EmailService
              │                        └── Jinja2 render → fastapi-mail → SMTP
              │
              ├── channel=2 or 3 ──► SMSService
              │                        └── resolve template → httpx → Gupshup API
              │
              ├── Update smtp_details (status=SENT|FAILED)
              └── Return JSON response
```

---

## Project Structure

```
s2s-service-brodcast/
│
├── app/
│   ├── main.py                          # FastAPI app factory, CORS, lifespan
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── router.py                # Aggregates all v1 endpoints
│   │       └── endpoints/
│   │           └── smtp.py              # send_smtp, generate_hash, categories
│   │
│   ├── core/
│   │   ├── config.py                    # Pydantic Settings (reads .env)
│   │   └── security.py                  # HMAC generate / verify / expiry
│   │
│   ├── db/
│   │   └── session.py                   # AsyncEngine, AsyncSession, get_db
│   │
│   ├── middleware/
│   │   ├── rate_limit.py                # Starlette middleware — Redis sliding window
│   │   └── hash_verify.py               # FastAPI dependency for hash auth
│   │
│   ├── models/
│   │   └── models.py                    # SQLAlchemy ORM models (4 tables)
│   │
│   ├── schemas/
│   │   └── schemas.py                   # Pydantic v2 request/response models
│   │
│   ├── services/
│   │   ├── email_service.py             # Jinja2 + fastapi-mail dispatch
│   │   ├── sms_service.py               # Gupshup async HTTP integration
│   │   └── s3_service.py                # AWS S3 auxiliary (upload/presign)
│   │
│   ├── utils/
│   │   └── response_helper.py           # Uniform { success, message, data } envelope
│   │
│   └── templates/
│       └── emails/                      # Jinja2 HTML email templates
│           ├── otp_verification.html
│           └── forgot_password.html
│
├── alembic/
│   ├── env.py                           # Async Alembic configuration
│   └── versions/
│       └── 0001_initial.py              # Initial schema migration
│
├── tests/
│   └── test_smtp.py                     # pytest-asyncio unit + integration tests
│
├── .github/
│   └── workflows/
│       └── ci.yml                       # GitHub Actions CI (test + lint)
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## API Reference

### `GET /test`
Health check. No authentication required.

**Response**
```json
{
  "status": "ok",
  "service": "s2s-service-brodcast",
  "version": "1.0.0"
}
```

---

### `POST /v1/send-smtp`
Primary dispatch endpoint. Protected by HMAC hash verification and rate limiting.

**Request Body**

| Field | Type | Required | Description |
|---|---|---|---|
| `project_id` | int | ✅ | Project identifier |
| `category_type_id` | int | ✅ | Message category |
| `broadcast_channel_type` | int | ✅ | `1`=Email, `2`=SMS, `3`=Both |
| `hash` | string | ✅ | HMAC-SHA256 of payload |
| `timestamp` | int | ✅ | Unix timestamp (for expiry) |
| `to_email` | string | if channel 1 or 3 | Recipient email |
| `cc_email` | string | ❌ | CC email |
| `bcc_email` | string | ❌ | BCC email |
| `mobile` | string | if channel 2 or 3 | Indian mobile (`[6-9]\d{9}`) |
| `data` | object | ❌ | Template variables (e.g. `{ "otp": "123456" }`) |

**Example Request**
```json
{
  "project_id": 1,
  "category_type_id": 1,
  "broadcast_channel_type": 3,
  "hash": "a3f9c2...",
  "timestamp": 1720000000,
  "to_email": "user@example.com",
  "mobile": "9876543210",
  "data": { "otp": "482910", "name": "Ravi" }
}
```

**Success Response**
```json
{
  "success": true,
  "message": "Message dispatched successfully",
  "request_id": 42,
  "email_status": "sent",
  "sms_status": "sent"
}
```

**Error Responses**

| HTTP | Reason |
|---|---|
| `400` | Invalid or expired hash |
| `404` | No template mapping found |
| `422` | Validation error (missing required field) |
| `429` | Rate limit exceeded |

---

### `POST /v1/generate-hash`
Utility endpoint to generate a valid HMAC hash for a payload. Use during integration / testing.

**Request Body**
```json
{
  "payload": {
    "project_id": 1,
    "category_type_id": 1,
    "broadcast_channel_type": 1,
    "timestamp": 1720000000
  }
}
```

**Response**
```json
{
  "hash": "a3f9c2d8e1...",
  "message": "Hash generated successfully"
}
```

---

### `GET /v1/get-categories-list`
Returns all category types available in the system.

**Response**
```json
[
  { "id": 1, "name": "OTP Verification", "code": "otp_verification", "description": null },
  { "id": 2, "name": "Forgot Password",  "code": "forgot_password",  "description": null }
]
```

---

## Request Flow

```
POST /v1/send-brodcast
      │
      ▼
┌─────────────────────────────┐
│  RateLimitMiddleware        │──── over limit ──► 429 Too Many Requests
│  Redis key: rate_limit:{ip} │
└─────────────────────────────┘
      │ within limit
      ▼
┌─────────────────────────────┐
│  VerifyRequestHash          │──── mismatch / expired ──► 400 Bad Request
│  HMAC-SHA256 + timestamp    │
└─────────────────────────────┘
      │ valid
      ▼
┌─────────────────────────────┐
│  Pydantic Validation        │──── invalid ──► 422 Unprocessable Entity
└─────────────────────────────┘
      │ valid
      ▼
  Persist brodcast_details (status = 1 PENDING)
      │
      ▼
  Lookup product_category_template_mapping
      │──── not found ──► 404 Not Found
      │ found
      ▼
  ┌───────────────────────────────────────────────────┐
  │  channel = 1 or 3  ──►  EmailService              │
  │    • Render Jinja2 template                        │
  │    • Send via fastapi-mail (SMTP)                  │
  │                                                    │
  │  channel = 2 or 3  ──►  SMSService                │
  │    • Resolve SMS template from config              │
  │    • POST to Gupshup REST API (async httpx)        │
  └───────────────────────────────────────────────────┘
      │
      ▼
  Update smtp_details (status = 2 SENT | 3 FAILED)
      │
      ▼
  JSON Response ──► Client
```

---

## Database Schema

```
┌─────────────┐       ┌──────────────┐
│  projects   │       │ category_type│
│─────────────│       │──────────────│
│ id (PK)     │       │ id (PK)      │
│ name        │       │ name         │
│ slug        │       │ code         │
│ created_at  │       │ description  │
└──────┬──────┘       └──────┬───────┘
       │                     │
       └──────┬──────────────┘
              │
     ┌────────▼────────────────────────┐
     │  product_category_template_     │
     │  mapping                        │
     │─────────────────────────────────│
     │  id (PK)                        │
     │  project_id (FK)                │
     │  category_type_id (FK)          │
     │  broadcast_channel_type         │  1=Email 2=SMS 3=Both
     │  template_path                  │  e.g. "otp_verification"
     │  subject                        │
     └─────────────────────────────────┘

     ┌─────────────────────────────────┐
     │  brodcast_details                   │  (audit log)
     │─────────────────────────────────│
     │  id (PK)                        │
     │  project_id                     │
     │  category_type_id               │
     │  broadcast_channel_type         │
     │  recipient_email                │
     │  recipient_mobile               │
     │  request_payload  (JSON)        │
     │  response_payload (JSON)        │
     │  status          1|2|3          │  pending|sent|failed
     │  request_ip                     │
     │  created_date                   │
     └─────────────────────────────────┘
```

---

## Getting Started

### Prerequisites

- Docker & Docker Compose **or** Python 3.11+, PostgreSQL 14+, Redis 7+

### Local Setup (Docker)

```bash
# 1. Clone the repo
git clone https://github.com/your-org/s2s-service-brodcast.git
cd s2s-service-brodcast

# 2. Copy and configure environment
cp .env.example .env
# Edit .env with your SMTP, Gupshup, and secret values

# 3. Start all services
docker compose up --build

# 4. Run database migrations
docker compose exec api alembic upgrade head

# 5. Open API docs
open http://localhost:8000/docs
```

### Local Setup (Manual)

```bash
# 1. Create virtualenv
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit DATABASE_URL, REDIS_URL, MAIL_*, SMS_* in .env

# 4. Run migrations
alembic upgrade head

# 5. Start the server
uvicorn app.main:app --reload --port 8000
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | `postgresql+asyncpg://user:pass@host/db` |
| `REDIS_URL` | — | `redis://localhost:6379` |
| `SECRET_KEY_HASH` | — | HMAC signing secret — **change in production** |
| `HASH_EXPIRATION_TIME` | `300` | Max hash age in seconds |
| `RATE_LIMIT` | `10` | Max requests per window per IP |
| `RATE_LIMIT_WINDOW` | `60` | Rate limit window in seconds |
| `MAIL_HOST` | — | SMTP server hostname |
| `MAIL_PORT` | `587` | SMTP server port |
| `MAIL_USERNAME` | — | SMTP username |
| `MAIL_PASSWORD` | — | SMTP password |
| `MAIL_FROM` | — | Sender email address |
| `MAIL_FROM_NAME` | `Notifications` | Sender display name |
| `MAIL_USE_TLS` | `true` | Enable STARTTLS |
| `SMS_API_URL` | — | Gupshup REST endpoint |
| `SMS_USERID` | — | Gupshup user ID |
| `SMS_PASSWORD` | — | Gupshup password |
| `SMS_SEND_TO_COUNTRY` | `91` | Country code prefix for mobile |
| `AWS_ACCESS_KEY_ID` | — | AWS credentials (S3, optional) |
| `AWS_SECRET_ACCESS_KEY` | — | AWS credentials (S3, optional) |
| `AWS_REGION` | `ap-south-1` | AWS region |
| `AWS_BUCKET` | — | S3 bucket name |
| `DEBUG` | `false` | Enable SQLAlchemy echo + debug logs |

> ⚠️ Never commit `.env` to version control. Use `.env.example` as the template.

---

## Running Tests

```bash
# Install dev dependencies (already in requirements.txt)
pip install -r requirements.txt

# Run all tests with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Run a specific test
pytest tests/test_smtp.py::test_generate_hash_endpoint -v
```

**Test coverage includes:**
- Hash generation determinism
- Hash tamper detection
- Hash expiry logic
- `GET /test` health check
- `POST /v1/generate-hash` endpoint
- `POST /v1/send-smtp` with invalid hash → 400

---

## Hash Authentication

Every request to `POST /v1/send-smtp` must include a `hash` field.

**How the hash is computed:**

```python
import hmac, hashlib, time
from urllib.parse import urlencode

SECRET = "your-secret-key"

payload = {
    "project_id": 1,
    "category_type_id": 1,
    "broadcast_channel_type": 1,
    "timestamp": int(time.time()),
    # ... other fields (exclude 'hash' itself)
}

sorted_payload = dict(sorted(payload.items()))
query_string   = urlencode(sorted_payload)
hash_value     = hmac.new(SECRET.encode(), query_string.encode(), hashlib.sha256).hexdigest()
```

Or use the built-in utility endpoint:

```bash
curl -X POST http://localhost:8000/v1/generate-hash \
  -H "Content-Type: application/json" \
  -d '{"payload": {"project_id": 1, "category_type_id": 1, "broadcast_channel_type": 1, "timestamp": 1720000000}}'
```

**Rules:**
- Excluded from hash: `hash`, `token`
- Hash expires after `HASH_EXPIRATION_TIME` seconds (default 300s)
- Mismatch or expired hash returns `HTTP 400`

---

## Rate Limiting

- Applied only to `POST /v1/send-smtp`
- Keyed by client IP: `rate_limit:{ip}`
- Default: **10 requests per 60 seconds**
- Implemented with Redis `INCR` + `EXPIRE` (atomic sliding window)
- Returns `HTTP 429` with `retry_after` seconds on breach

Configure via `.env`:
```env
RATE_LIMIT=10
RATE_LIMIT_WINDOW=60
```

---

## Email Templates

Templates live in `app/templates/emails/` as Jinja2 HTML files.

**Adding a new template:**

1. Create `app/templates/emails/my_template.html`:
```html
<p>Hello {{ name }}, your code is <strong>{{ code }}</strong>.</p>
```

2. Insert a mapping row in `product_category_template_mapping`:
```sql
INSERT INTO product_category_template_mapping
  (project_id, category_type_id, broadcast_channel_type, template_path, subject)
VALUES
  (1, 5, 1, 'my_template', 'Your verification code');
```

3. Send with `data: { "name": "Priya", "code": "99123" }` in the request.

**Bundled templates:**

| File | Purpose |
|---|---|
| `otp_verification.html` | OTP / one-time password emails |
| `forgot_password.html` | Password reset link emails |

---

## SMS Templates

SMS templates are config-driven in `app/services/sms_service.py`:

```python
SMS_TEMPLATES: dict[int, str] = {
    1: "Your OTP is {#var#}. Valid for 10 minutes. Do not share.",
    2: "Your password reset OTP is {#var#}.",
    3: "Your payout of Rs.{#var#} has been processed.",
}
```

- `{#var#}` is replaced with `data.otp` from the request payload
- Mobile numbers must match `^[6-9]\d{9}$` (Indian format)
- Add new templates by extending the dict and mapping `category_type_id` → template

---

## Deployment

### Docker (recommended)

```bash
docker compose up -d --build
docker compose exec api alembic upgrade head
```

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Rotate `SECRET_KEY_HASH` to a strong random value
- [ ] Use a managed PostgreSQL (AWS RDS, Cloud SQL, Supabase)
- [ ] Use a managed Redis (AWS ElastiCache, Upstash, Redis Cloud)
- [ ] Configure a transactional SMTP provider (AWS SES, SendGrid, Mailgun)
- [ ] Set `SMS_USERID` / `SMS_PASSWORD` from your Gupshup dashboard
- [ ] Mount secrets via environment or a secrets manager — never commit `.env`
- [ ] Run `alembic upgrade head` before first boot

### Environment-specific `DATABASE_URL` examples

```env
# Local Docker
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/smtp_service

# AWS RDS
DATABASE_URL=postgresql+asyncpg://admin:password@mydb.xxxx.rds.amazonaws.com:5432/smtp_service

# Supabase
DATABASE_URL=postgresql+asyncpg://postgres:password@db.xxxx.supabase.co:5432/postgres
```

---

## Comparison with Laravel Lumen Origin

| Aspect | Laravel Lumen (original) | FastAPI (this service) |
|---|---|---|
| Language | PHP 8.1 | Python 3.11 |
| I/O Model | Synchronous | Async (asyncio) |
| Framework | Lumen 10 | FastAPI 0.115 |
| ORM | Eloquent | SQLAlchemy 2 (async) |
| Migrations | Laravel Migrations | Alembic (async) |
| Mail | illuminate/mail + Blade | fastapi-mail + Jinja2 |
| SMS HTTP | cURL (sync) | httpx (async) |
| Validation | Laravel Validator | Pydantic v2 |
| Rate Limiting | Custom Redis trait | Starlette middleware |
| API Docs | None | Auto Swagger / ReDoc |
| Tests | PHPUnit (minimal) | pytest-asyncio |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Write tests for your changes
4. Ensure all tests pass: `pytest tests/ -v`
5. Open a pull request against `main`

**Code style:** `black` + `isort` + `ruff` (add to `requirements.txt` for dev)

---

## License

[MIT](LICENSE) © Your Organization
