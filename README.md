# METFI — Autonomous Finance Controller

**Autonomous Multi-Source Financial Reconciliation Engine with Deterministic Grounding and Bounded AI Reasoning**

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14%2B-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Track](https://img.shields.io/badge/Razorpay%20AI%20Buildathon-Track%2004-blueviolet.svg)](https://github.com/Dusi-81wb/METFI)

---

## 1. Executive Overview

**METFI** is an enterprise-grade autonomous finance controller engineered for high-throughput, multi-source financial reconciliation across **Payment Gateways, Bank Settlement Files, and Merchant General Ledgers**.

Traditional reconciliation suffers from a critical dilemma:
- **Rule engines** are rigid and fail to handle real-world complexities like dynamic fee tier variances, cross-bank timing skews, and truncated references.
- **LLM-only systems** hallucinate financial figures, skip arithmetic constraints, lack auditability, and introduce severe security vulnerabilities.

### The METFI Principle:
> **Financial truth is deterministic. AI provides investigation, explanation, and bounded recommendations.**

METFI provides a hybrid architecture: **deterministic code owns the mathematical truth and policy gates**, while **bounded AI agents investigate anomalies, correlate cross-source evidence, and explain discrepancies** for human controllers.

```text
Synthetic Sources (Payments, Settlements, Ledger)
                    |
                    v
          [ Ingestion & Normalization ]
                    |
                    v
    [ Deterministic Reconciliation Engine ]
        /                               \
       /                                 \
  (Exact Matches)               (Discrepancies / Mismatches)
      |                                   |
      |                                   v
      |                     [ AI Investigation Layer ]
      |                     (Structured Evidence & Reasoning)
      |                                   |
      +-----------------+-----------------+
                        |
                        v
               [ Policy Engine Gate ]
               (AUTO | REVIEW | UNRESOLVED)
                        |
                        v
               [ Immutable Audit Trail ]
                        |
                        v
         [ Evaluation & Live Dashboard ]
```

---

## 2. Key Capabilities & Architectural Invariants

- **Multi-Source Reconciliation:** Ingests and cross-reconciles Payment Gateway logs, Bank Settlement feeds, and ERP Ledger journals.
- **10-Class Exception Taxonomy:** Classifies `EXACT_MATCH`, `AMOUNT_MISMATCH`, `MISSING_SETTLEMENT`, `DUPLICATE_RECORD`, `DATE_MISMATCH`, `REFERENCE_MISMATCH`, `PARTIAL_SETTLEMENT`, `FEE_DISCREPANCY`, `CURRENCY_MISMATCH`, and `AMBIGUOUS`.
- **Bounded AI Agents:** AI outputs strongly typed Pydantic structures with field-level citations; cannot mutate database state directly.
- **Strict Policy Engine:** Enforces hard mathematical invariants; decides between `AUTO_RECONCILE`, `REVIEW_REQUIRED`, and `UNRESOLVED`.
- **Zero-Leakage Evaluation:** Synthetic data generation features separate, isolated ground-truth manifests for reproducible benchmarking.
- **Append-Only Audit Trail:** Immutable decision records capturing complete evidence lineage for compliance and forensic audits.
- **Real-Time Operations Dashboard:** Interactive Next.js interface with live metrics, batch controller, and side-by-side case inspector.

---

## 3. System Architecture & Repository Structure

```text
METFI/
├── README.md                 # Primary project overview and quick start
├── AGENTS.md                 # Agent roles, invariants & review protocols
├── ARCHITECTURE.md           # 9-layer system architecture specification
├── PRODUCT_SPEC.md           # Domain data models & reconciliation rules
├── EVALUATION_SPEC.md        # Benchmark metrics & ground-truth protocol
├── TESTING.md                # QA strategy & test execution guide
├── SECURITY.md               # Safety boundaries & secret management
├── DECISIONS.md              # Architecture Decision Records (ADRs)
├── CONTRIBUTING.md           # Contribution guidelines & pre-commit checks
│
├── backend/                  # FastAPI Modular Monolith (Python 3.12+)
│   ├── app/
│   │   ├── api/              # HTTP routers & API endpoints
│   │   ├── core/             # Configuration, logging & DB sessions
│   │   ├── domain/           # Data schemas & entity models
│   │   ├── reconciliation/   # Deterministic matching & candidate engine
│   │   ├── intelligence/     # Bounded AI investigator & resolver
│   │   ├── policy/           # Deterministic policy engine
│   │   ├── audit/            # Append-only audit trail logger
│   │   ├── evaluation/       # Benchmark runner & metrics calculator
│   │   └── services/         # Orchestration & reconciliation services
│   ├── tests/                # Unit, integration & golden fixture tests
│   ├── pyproject.toml        # Backend packaging & dependencies
│   └── Dockerfile            # Container build
│
├── frontend/                 # Next.js 14+ / TypeScript / Tailwind CSS
│   ├── app/                  # App Router pages & layouts
│   ├── components/           # UI components & case inspectors
│   ├── lib/                  # Type-safe API client & utilities
│   ├── types/                # Shared TypeScript definitions
│   └── package.json
│
├── data/                     # Data plane (schemas, generators, fixtures)
│   ├── schemas/              # Input data schemas
│   ├── generators/           # Synthetic multi-source dataset generator
│   ├── fixtures/             # Deterministic test fixtures
│   └── ground_truth/         # Isolated ground-truth labels
│
├── evaluation/               # Evaluation artifacts & benchmarks
│   ├── benchmarks/           # Standardized benchmark runner
│   ├── metrics/              # Metric calculation algorithms
│   └── reports/              # Versioned evaluation benchmark reports
│
├── docs/                     # Documentation & reviews
│   ├── architecture/         # Deep-dive architecture notes
│   ├── demo/                 # Demo scripts & presentation assets
│   └── reviews/              # Phase handoffs & Prime adversarial reviews
│
├── scripts/                  # Automation scripts
├── docker-compose.yml        # Multi-service local deployment
└── .env.example              # Environment variables template
```

---

## 4. Quick Start & Local Setup

### Prerequisites
- Python 3.12+ (recommend using `uv`)
- Node.js 18+ & npm 9+
- Docker & Docker Compose (optional for containerized run)

### Option A: Running with Docker Compose (Recommended)
```bash
# 1. Clone repository
git clone https://github.com/Dusi-81wb/METFI.git
cd METFI

# 2. Copy environment file
cp .env.example .env

# 3. Launch all services (PostgreSQL, Backend, Frontend)
docker compose up --build
```
Access the application:
- **Operations Dashboard:** [http://localhost:3000](http://localhost:3000)
- **FastAPI Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Endpoint:** [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)

---

### Option B: Local Native Development

#### 1. Backend Setup
```bash
cd backend

# Create virtual environment with Python 3.12
uv venv .venv --python 3.12

# Activate virtualenv
# On Windows: .venv\Scripts\activate
# On Linux/macOS: source .venv/bin/activate

# Install dependencies
uv pip install -e ".[dev]"

# Start FastAPI development server
uv run uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install

# Start Next.js development server
npm run dev
```

---

### Option C: Synthetic Dataset Generation & Inspection
```bash
# Generate dev benchmark dataset (500 records, seed 42)
python data/generators/cli.py --size 500 --seed 42 --dataset-id dev_500

# Generate stress benchmark dataset (5,000 records, seed 1337)
python data/generators/cli.py --size 5000 --seed 1337 --dataset-id stress_5000

# Inspect dataset manifests and sample ground truth
python data/generators/inspect_dataset.py --dataset-id dev_500
```

---

## 5. Verification & Testing

Execute the complete quality test suite:

```bash
# Run backend unit, integration, and smoke tests (52+ tests)
cd backend && uv run pytest -v

# Run backend linting & formatting checks
cd backend && uv run ruff check .

# Run backend static type checking
cd backend && uv run mypy app

# Run frontend type checking & production build
cd frontend && npm run type-check && npm run build
```

---

## 6. Development Roadmap

- [x] **Phase 0:** Governance, Repository Initialization & Health Smoke Test
- [x] **Phase 1:** Domain Schemas, Normalization, Synthetic Generator & Ground Truth Isolation
- [ ] **Phase 2:** Deterministic Reconciliation Engine & Golden Fixtures
- [ ] **Phase 3:** Bounded AI Investigation Layer & Verifier
- [ ] **Phase 4:** Deterministic Policy Engine & Immutable Audit Trail
- [ ] **Phase 5:** Evaluation Engine, Benchmark Runner & Stress Testing
- [ ] **Phase 6:** Next.js Operations Dashboard & Interactive Case Inspector
- [ ] **Phase 7:** Adversarial Hardening & Prime Agent Audit
- [ ] **Phase 8:** Final Benchmark Publication & Demo Submission

---

## 7. License

MIT License. Copyright (c) 2026 METFI Contributors.
