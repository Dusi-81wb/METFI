# Contributing to METFI

Thank you for contributing to **METFI (Autonomous Finance Controller for Razorpay AI Buildathon, Track 04)**.

---

## 1. Development Workflow

1. **Read Governance First:** Review `METFI_MASTER_SPEC_v1.0.md`, `AGENTS.md`, `ARCHITECTURE.md`, and `DECISIONS.md`.
2. **Branch Naming:**
   - Features: `feat/phase-<number>-<description>`
   - Bugfixes: `fix/<issue-description>`
   - Audits/Tests: `test/<description>`
3. **Commit Messages:** Follow Conventional Commits:
   - `feat: add deterministic amount matching rule`
   - `fix: correct GST rounding on fee calculation`
   - `test: add golden fixtures for missing settlement`
   - `docs: update evaluation spec with benchmark results`

---

## 2. Local Development Environment

### Prerequisites
- Python 3.12+ (recommend using `uv`)
- Node.js 18+ & npm 9+
- Docker & Docker Compose

### Backend Setup
```bash
cd backend
uv venv .venv --python 3.12
# Activate virtualenv:
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
uv pip install -e ".[dev]"
uv run uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Docker Compose
```bash
docker compose up --build
```

---

## 3. Pre-Commit Verification Checklist

Before creating a commit or submitting a pull request, ensure all gates pass:

```bash
# 1. Run backend tests
cd backend && uv run pytest -v

# 2. Run backend linter & type checks
cd backend && uv run ruff check . && uv run mypy app

# 3. Run frontend type check & build
cd frontend && npm run type-check && npm run build
```

---

## 4. Architectural Rules for Contributors

1. **Never bypass the Policy Engine:** AI reasoning cannot directly mark a record as reconciled without passing deterministic policy validation.
2. **Decimal-safe arithmetic:** Never use standard binary floats for monetary calculations; always use `Decimal`.
3. **Isolate Ground Truth:** Do not write ground truth fixtures into ingestion folders or runtime inference code.
4. **No dead code or unverified placeholders:** Every module must have clear responsibilities, explicit types, and automated test coverage.

---

## 5. Multi-Agent Phase Review Protocol

After completing an implementation phase, execute the adversarial review runner against the active working tree:

```bash
# Auto mode (Prime primary with Kilo fallback)
python scripts/review/run_prime_review.py --phase <PHASE_NUMBER> --verbose

# Specialized Kilo Code pipeline review
python scripts/review/run_prime_review.py --phase <PHASE_NUMBER> --engine kilo --kilo-pipeline --verbose
```
Review artifacts are saved in `docs/reviews/prime/`. Address all CRITICAL and HIGH findings before closing the phase.
