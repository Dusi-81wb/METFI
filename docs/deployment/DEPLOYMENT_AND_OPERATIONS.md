# METFI Deployment & Operational Runbook
**Production Configuration, Container Architecture & Operations**

## 1. Container Architecture

METFI is deployed as a 3-tier containerized stack orchestrated via Docker Compose:

```text
┌─────────────────────────────────────────────────────────────┐
│                       METFI CLUSTER                         │
├─────────────────┬─────────────────────┬─────────────────────┤
│ 1. Frontend     │ Next.js 14 (Node20) │ Port 3000 (UI/UX)   │
│ 2. Backend      │ FastAPI (Python 3.12)│ Port 8000 (APIs)   │
│ 3. Database     │ PostgreSQL 16 Alpine│ Port 5432 (Data)    │
└─────────────────┴─────────────────────┴─────────────────────┘
```

---

## 2. Quick Start & Local Run

### Prerequisites
- Docker & Docker Compose (v2.20+)
- Python 3.12+ (with `uv`)
- Node.js 20+ (with `npm`)

### Running with Docker Compose
```bash
# 1. Clone & enter repository
git clone https://github.com/Dusi-81wb/METFI.git
cd METFI

# 2. Copy environment template
cp .env.example .env

# 3. Build & start all services
docker compose up --build -d

# 4. Verify healthcheck
curl http://localhost:8000/api/v1/health
```

---

## 3. Environment Variables Reference

| Variable | Description | Default | Production Requirement |
|---|---|---|---|
| `ENVIRONMENT` | Runtime environment | `development` | Set to `production` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` | Secure vault injected |
| `AI_PROVIDER` | AI reasoning provider | `mock` | `gemini` or `openai` |
| `GEMINI_API_KEY` | Google Gemini API key | None | Injected securely |
| `BACKEND_CORS_ORIGINS`| Allowed browser origins | `["http://localhost:3000"]` | Production domain whitelist |
