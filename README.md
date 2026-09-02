# METFI — Autonomous Finance Controller
**Multi-Source Financial Reconciliation with Deterministic Truth, Bounded AI Investigation, Policy-Gated Action & Cryptographic Auditability**

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14%2B-black.svg)](https://nextjs.org/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Docker Compose](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 284 Passing](https://img.shields.io/badge/Tests-284%20Passing-success.svg)](backend/tests/)

---

## 1. Executive Overview

**METFI** is an enterprise-grade autonomous finance controller designed for high-throughput, multi-source financial reconciliation across **Payment Gateways, Bank Settlement Files, and Merchant General Ledgers**.

Traditional reconciliation suffers from a fundamental tension:
- **Rigid Rule Engines**: Brittle, high maintenance, and unable to explain complex multi-factor variances (e.g. gateway tier fee deductions, timing delays, settlement batch truncations).
- **Pure LLM Approaches**: Prone to arithmetic hallucination, lack determinism, non-auditable, and dangerously grant direct financial write access to probabilistic models.

### The METFI Principle:
> **Deterministic Financial Truth > Policy Engine > AI Recommendation > Action Executor.**
> 
> Mathematical truth and financial state mutations must remain strictly deterministic. AI agents serve as advisory investigators that synthesize cross-source evidence, explain root causes, and propose bounded adjustments—subject to independent automated challenge and policy authorization.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                      1. MULTI-SOURCE INGESTION                          │
│         Payment Gateway Feeds ── Bank Settlement ── General Ledger      │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│              2. DETERMINISTIC RECONCILIATION ENGINE                     │
│   Canonical Normalization ── 10-Class Classification ── Evidence Matrix │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                   ┌─────────────────┴─────────────────┐
                   │                                   │
             [Exact Matches]                 [Exceptions / Anomaly]
                   │                                   │
                   │                 ┌─────────────────▼─────────────────┐
                   │                 │     3. ADVISORY AI INVESTIGATOR   │
                   │                 │   Root Cause Diagnosis & Evidence │
                   │                 └─────────────────┬─────────────────┘
                   │                                   │
                   │                 ┌─────────────────▼─────────────────┐
                   │                 │     4. INDEPENDENT AI VERIFIER    │
                   │                 │   Grounding Check & Truth Defense │
                   │                 └─────────────────┬─────────────────┘
                   │                                   │
                   └─────────────────┬─────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                    5. DETERMINISTIC POLICY ENGINE                       │
│    Variance Tolerances ── Retry Limits ── Authority Hierarchy Enforced  │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                   ┌─────────────────┴─────────────────┐
                   │                                   │
              [Authorized]                    [Review Required]
                   │                                   │
┌──────────────────▼──────────────────┐  ┌─────────────▼──────────────────┐
│     6. CONTROLLED ACTION EXECUTOR   │  │    7. HUMAN OPERATIONS QUEUE   │
│   Idempotent SHA-256 Execution Token│  │   Operator Claim & Resolution  │
└──────────────────┬──────────────────┘  └─────────────┬──────────────────┘
                   │                                   │
                   └─────────────────┬─────────────────┘
                                     │
┌────────────────────────────────────▼────────────────────────────────────┐
│                 8. TAMPER-EVIDENT AUDIT & OBSERVABILITY                 │
│    Cryptographic SHA-256 Hash Chaining ── Automated Secret Redaction    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Key Capabilities & Architectural Guarantees

1. **Deterministic Authority**:
   - The Policy Engine strictly enforces `RULE_DETERMINISTIC_PRIMACY`. An action cannot be authorized if it contradicts canonical reconciliation truth.
2. **AI Trust Boundaries (Zero Write Permissions)**:
   - LLM models generate structured Pydantic hypotheses (`InvestigationResult`). They have zero direct database write permissions.
   - An independent, automated **AI Verifier** challenges every claim against field-level context before policy evaluation.
3. **Strict Ground-Truth Isolation**:
   - Ingestion records are completely decoupled from ground-truth evaluation manifests. Zero expected labels or corruption metadata are exposed in prompts, API payloads, or audit trails.
4. **Controlled Action Execution**:
   - Every action requires a deterministic SHA-256 idempotency key, bounded retry counter, and explicit authorization token.
5. **Tamper-Evident Cryptographic Audit Ledger**:
   - Events are cryptographically hash-chained (`previous_event_hash`). Any manual record deletion, modification, or sequence reordering is detected instantaneously.
   - Automatic regex sanitization strips API keys (`sk-*`, `AIza*`), bearer tokens, and PII prior to hashing.

---

## 3. Verified Benchmark Results (Measured)

METFI evaluates performance across **7 distinct benchmark suites** without hiding failures or exaggerating claims:

| Benchmark Suite | Test Dataset / Scope | Cases | Primary Metric | Result |
|---|---|---|---|---|
| **INDEPENDENT** | Uncorrupted real-world transaction groups | 50 | Classification Accuracy | **100.0%** |
| **ADVERSARIAL** | Edge cases (boundary amounts, Unicode, negative, ties) | 24 | Exception Isolation | **100.0%** |
| **AI INVESTIGATION** | Complex multi-factor anomalies | 50 | Evidence Citation Precision | **96.4%** |
| **AI VERIFIER** | Deliberate hallucination & contradiction challenges | 35 | Rejection of Unsupported Claims | **100.0%** |
| **POLICY ENGINE** | Monetary variance tolerances & retry caps | 100 | Authority Adherence | **100.0%** |
| **AUDIT INTEGRITY** | Cryptographic hash continuity & tampering injection | 50 | Tamper Detection Rate | **100.0%** |
| **SYNTHETIC (Scale)**| High-throughput multi-source stream (`dev_500`) | 500 | Throughput (Records/Sec) | **2,200 rec/s** |

> *Note: Latency benchmarks measure sub-0.5ms deterministic matching, sub-0.2ms policy evaluation, and sub-0.1ms cryptographic event hashing.*

---

## 4. Quick Start & Local Setup

### Prerequisites
- Python 3.12+ (recommend using `uv`)
- Node.js 20+ & npm 10+
- Docker & Docker Compose (v2.20+)

### Option A: Complete Stack via Docker Compose (Recommended)
```bash
# 1. Clone repository
git clone https://github.com/Dusi-81wb/METFI.git
cd METFI

# 2. Copy environment configuration
cp .env.example .env

# 3. Build & start all containers (Postgres, Backend, Frontend)
docker compose up --build -d

# 4. Open applications
# Frontend Dashboard:  http://localhost:3000
# Backend API Docs:    http://localhost:8000/docs
# System Health Probe: http://localhost:8000/api/v1/health
```

---

### Option B: Local Native Development

#### 1. Backend Service
```bash
cd backend

# Create virtual environment and install dependencies
uv venv .venv --python 3.12
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# Launch development server
uv run uvicorn app.main:app --reload --port 8000
```

#### 2. Frontend Operations Console
```bash
cd frontend

# Install dependencies and launch Next.js
npm install
npm run dev -- -p 3000
```

---

## 5. Primary Judge Evaluation Walkthrough

To experience the end-to-end system in 3 minutes:
1. **Interactive Showcase**: Navigate to [`http://localhost:3000/showcase`](http://localhost:3000/showcase) and click **"Execute Live Showcase Pipeline"** to watch the 10-step lifecycle execute live.
2. **Reconciliation Batch**: Navigate to [`/reconciliation`](http://localhost:3000/reconciliation), select `dev_500`, and observe 500 records matched in < 250ms.
3. **Exception Inspection**: Open [`/exceptions`](http://localhost:3000/exceptions) and click into case `CASE_ORD_10029` to inspect the side-by-side evidence diff.
4. **AI & Verifier**: Trigger the AI investigation and note how the independent verifier validates field grounding.
5. **Policy & Action**: Review the policy authorization decision under [`/actions`](http://localhost:3000/actions).
6. **Audit Verification**: Navigate to [`/audit`](http://localhost:3000/audit) and click **"Verify Cryptographic Integrity"** to validate the live SHA-256 chain.
7. **Benchmarks**: View the 7 evaluation suites under [`/benchmarks`](http://localhost:3000/benchmarks).

*For detailed evaluation notes, refer to [docs/demo/FINAL_DEMO_SCRIPT.md](docs/demo/FINAL_DEMO_SCRIPT.md).*

---

## 6. Automated Testing & Verification

Run the full quality and regression suite locally:

```bash
# 1. Run all 284 backend unit and integration tests
cd backend && uv run pytest

# 2. Run Ruff linting and formatting
cd backend && uv run ruff check . && uv run ruff format --check .

# 3. Run Mypy static type checking
cd backend && uv run mypy app

# 4. Run Frontend TypeScript check and production build
cd frontend && npm run type-check && npm run build

# 5. Run Unified Benchmark Suite
python -m backend.app.evaluation.unified_benchmark_runner
```

---

## 7. Known Limitations & Production Scope

- **AI Provider Fallback**: While METFI supports live Gemini and OpenAI inference, production deployments without external API keys automatically degrade gracefully to the bounded `MockLLMProvider` with zero downtime.
- **Ledger Ingestion Formats**: Currently supports standard JSON feeds and CSV exports from major gateways (Razorpay, Stripe) and ERP journals (NetSuite, SAP). Custom binary bank formats require upstream parser normalization.
- **Dispute Workflows**: Full chargeback arbitration lifecycles are modeled as manual review escalation items rather than fully autonomous chargeback debit actions.

---

## 8. License

MIT License. Copyright (c) 2026 METFI Contributors.
