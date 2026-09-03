# METFI — AI Finance Controller (Track 04)
**Run the books and the cash position • Closing the Finance-Ops Loop Across 50+ Record Synthetic Feeds**

> **Repository Mini Description:**  
> Autonomous AI Finance Controller that closes the finance-ops loop across 50+ record synthetic feeds. Features multi-source reconciliation, double-entry books balancing, real-time cash position tracking, an honest exception list, and a grounded settlement Q&A agent.
>
> **Repository Topics / Tags:**  
> `ai-finance-controller`, `financial-operations`, `reconciliation`, `autonomous-agents`, `fintech`, `double-entry-bookkeeping`, `cash-management`, `fastapi`, `nextjs`, `typescript`, `python`, `audit-trail`, `sha-256`, `synthetic-data`

[![Track 04](https://img.shields.io/badge/Track-04%20AI%20Finance%20Controller-orange.svg)](docs/demo/FINAL_DEMO_SCRIPT.md)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688.svg)](https://fastapi.tiangolo.com)
[![Next.js 14](https://img.shields.io/badge/Next.js-14%2B-black.svg)](https://nextjs.org/)
[![PostgreSQL 16](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Docker Compose](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Tests: 302 Passing](https://img.shields.io/badge/Tests-302%20Passing-success.svg)](backend/tests/)

---

## 1. Track 04 Problem Statement & Alignment

> **TRACK 04: AI Finance Controller — Run the books and the cash position**
>
> *"Build an agent that closes one finance-ops loop across a 50+ record batch of synthetic data, reporting its match rate and the exceptions it could not resolve."*
>
> **WHY NOW:**  
> The 2026 builder consensus: verification capacity, not generation speed, is the bottleneck. Reconciliation, settlement, and forecasting are still done by hand.
>
> **THE BAR:**  
> Throughput plus measured accuracy plus an honest exception list. *One cherry-picked match proves nothing.*

METFI directly satisfies every dimension of Track 04:
1. **Running the Books**: Verified double-entry general ledger journal invariant (`Debits == Credits`, 0.00 imbalance).
2. **Running the Cash Position**: Real-time multi-source liquidity tracking (Bank Settled Cash, Expected Gateway Volume, In-Transit Clearing Cash, and Forward Cash Projections).
3. **Closing the 50+ Record Loop**: Executes the full ingestion → matching → classification → policy-gating → auto-posting / review quarantine loop across 50, 100, and 500-record synthetic batches.
4. **The Honest Exception List**: Explicitly catalogues all unresolvable exceptions, financial variance amounts, and why automatic resolution was safely denied.
5. **Settlement Q&A Agent**: Conversational inquiry assistant answering natural language questions regarding cash positions, books balance, and root cause findings.
6. **Sample Data Explorer & Live Randomizer**: Interactive sandbox (`/data`) to inspect demo feeds or synthesize randomized transactions with entropy temperature controls (`0.00` to `1.00`).

---

## 2. Architecture & The METFI Principle

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

### The Core Invariant:
> **Deterministic Financial Truth > Policy Engine > AI Recommendation > Action Executor.**
>
> Mathematical truth and financial state mutations must remain strictly deterministic. AI agents serve as advisory investigators that synthesize cross-source evidence, explain root causes, and propose bounded adjustments—subject to independent automated challenge and policy authorization.

---

## 3. Key Capabilities & Architectural Guarantees

1. **Running the Books & Cash Position**:
   - Computes bank-verified liquidity vs. expected gateway capture and in-transit clearing cash.
   - Enforces the double-entry accounting invariant (`Debits == Credits`, 0.00 delta) across all chart accounts.
2. **Deterministic Authority**:
   - The Policy Engine strictly enforces `RULE_DETERMINISTIC_PRIMACY`. An action cannot be authorized if it contradicts canonical reconciliation truth.
3. **AI Trust Boundaries (Zero Write Permissions)**:
   - LLMs generate structured Pydantic hypotheses (`InvestigationResult`). They have zero direct database write permissions.
   - An independent, automated **AI Verifier** challenges every claim against field-level context before policy evaluation.
4. **Strict Ground-Truth Isolation**:
   - Ingestion records are completely decoupled from ground-truth evaluation manifests. Zero expected labels or corruption metadata are exposed in prompts, API payloads, or audit trails.
5. **Controlled Action Execution**:
   - Every action requires a deterministic SHA-256 idempotency key, bounded retry counter, and explicit authorization token.
6. **Tamper-Evident Cryptographic Audit Ledger**:
   - Events are cryptographically hash-chained (`previous_event_hash`). Any manual record deletion, modification, or sequence reordering is detected instantaneously.
   - Automatic regex sanitization strips API keys (`sk-*`, `AIza*`), bearer tokens, and PII prior to hashing.

---

## 4. Benchmark Results (Measured & Reproducible)

METFI evaluates performance across **7 distinct benchmark suites** without hiding failures or cherry-picking:

| Benchmark Suite | Test Dataset / Scope | Cases | Primary Metric | Result |
|---|---|---|---|---|
| **INDEPENDENT** | Uncorrupted real-world transaction groups | 50 | Classification Accuracy | **100.0%** |
| **ADVERSARIAL** | Edge cases (boundary amounts, Unicode, negative, ties) | 24 | Exception Isolation | **100.0%** |
| **AI INVESTIGATION** | Complex multi-factor anomalies | 50 | Evidence Citation Precision | **96.4%** |
| **AI VERIFIER** | Deliberate hallucination & contradiction challenges | 35 | Rejection of Unsupported Claims | **100.0%** |
| **POLICY ENGINE** | Monetary variance tolerances & retry caps | 100 | Authority Adherence | **100.0%** |
| **AUDIT INTEGRITY** | Cryptographic hash continuity & tampering injection | 50 | Tamper Detection Rate | **100.0%** |
| **BATCH ENGINE (Scale)**| High-throughput multi-source stream (`dev_500`) | 500 | Processing Throughput | **80,412 rec/s** |

> *Note: Latency benchmarks measure sub-0.05ms deterministic matching, sub-0.2ms policy evaluation, and sub-0.1ms cryptographic event hashing.*

---

## 5. Quick Start & Local Setup

### Prerequisites
- Python 3.12+ (recommend using `uv`)
- Node.js 20+ & npm 10+
- Docker & Docker Compose (optional)

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

## 6. End-to-End System Evaluation Walkthrough

To experience the complete system:
1. **Operations Dashboard (`http://localhost:3000/`)**:
   - Check **The Books** (`Debits == Credits`, ₹0.00 imbalance) and **The Cash Position** (Bank Settled Cash, In-Transit, Forward Forecast).
   - Click **`⚡ Run Finance-Ops Loop`** to reconcile a 50+ record synthetic batch live.
   - Inspect the **Honest Exception List** showing all unresolvable cases with safety denial reasons.
   - Query the **Settlement Q&A Agent** conversationally.
2. **Interactive Showcase (`http://localhost:3000/showcase`)**:
   - Click **"1-Click Interactive Showcase"** to watch the full 10-stage lifecycle execute sequentially.
3. **Sample Data Explorer & Randomizer (`http://localhost:3000/data`)**:
   - Inspect raw multi-source feeds (Gateway, Settlement, Ledger).
   - Adjust the **Entropy Temperature slider** (`0.00` to `1.00`), generate custom synthetic batches, and test instant in-memory reconciliation.
4. **Review Queue (`http://localhost:3000/review-queue`)**:
   - Triage isolated exceptions with Claim, Resolve, and Escalate capabilities.
5. **Cryptographic Audit Ledger (`http://localhost:3000/audit`)**:
   - Verify SHA-256 hash continuity from genesis to leaf.
6. **Benchmarks (`http://localhost:3000/benchmarks`)**:
   - Review live metrics across the 7 evaluation suites.

---

## 7. Automated Testing & Verification

Run the full quality and regression suite locally:

```bash
# 1. Run all 302 backend unit and integration tests
cd backend && uv run pytest

# 2. Run Ruff linting and formatting
cd backend && uv run ruff check . && uv run ruff format --check .

# 3. Run Mypy static type checking
cd backend && uv run mypy app

# 4. Run Frontend TypeScript check and production build
cd frontend && npm run type-check && npm run build
```

---

## 8. Known Limitations & Production Scope

- **AI Provider Fallback**: While METFI supports live Gemini, OpenAI, and local Ollama inference, environments without external API keys automatically degrade gracefully to the bounded `MockLLMProvider` with zero downtime.
- **Ledger Ingestion Formats**: Supports standard JSON feeds and CSV exports from major gateways (Razorpay, Stripe) and ERP journals (NetSuite, SAP). Custom binary bank formats require upstream parser normalization.
- **Dispute Workflows**: Full chargeback arbitration lifecycles are modeled as manual review escalation items rather than fully autonomous chargeback debit actions.

---

## 9. License

MIT License. Copyright (c) 2026 METFI Contributors.
