# METFI System Architecture

**Project:** METFI (Autonomous Finance Controller)  
**Track:** Razorpay AI Buildathon, Track 04 — AI Finance Controller  
**Architecture Style:** Modular Monolith with Strict Layer Boundaries  

---

## 1. Architectural Philosophy & Separation of Concerns

The central thesis of METFI is:
> **Financial truth is deterministic. AI provides investigation, explanation, and bounded recommendations.**

Traditional spreadsheet or LLM-only approaches fail in financial control because LLMs can hallucinate calculations, skip reference constraints, and lack mathematical guarantees. Conversely, pure rule-based engines fail when dealing with complex, multi-party discrepancies, ambiguous ledger entries, or settlement timing skews.

METFI bridges this by strictly delineating responsibilities:

```text
+-------------------------------------------------------------------------+
|                        METFI SYSTEM ARCHITECTURE                         |
+-------------------------------------------------------------------------+
|                                                                         |
|  [ LAYER A: Data Plane ]                                                |
|  Synthetic Generator | Ground Truth Isolator | Fixtures                 |
|                               |                                         |
|                               v                                         |
|  [ LAYER B: Ingestion ]                                                 |
|  Raw Payments (CSV/JSON) | Settlements (CSV/JSON) | Ledger (CSV/JSON)   |
|                               |                                         |
|                               v                                         |
|  [ LAYER C: Normalization ]                                             |
|  Canonical Schemas | Decimal Monetary Units | ISO Timestamps            |
|                               |                                         |
|                               v                                         |
|  [ LAYER D: Deterministic Reconciliation Engine ]                       |
|  Candidate Matcher | Exact Rule Evaluator | Hard Invariants             |
|                               |                                         |
|               +---------------+---------------+                         |
|               |                               |                         |
|      (Exact Match / Rules Pass)        (Ambiguous / Mismatch)           |
|               |                               |                         |
|               |                               v                         |
|               |                 [ LAYER E: Intelligence Layer ]         |
|               |                 AI Investigator | Structured Evidence   |
|               |                 Bounded Resolver Recommendation         |
|               |                               |                         |
|               +---------------+---------------+                         |
|                               |                                         |
|                               v                                         |
|  [ LAYER F: Policy Engine ]                                             |
|  Hard Constraint Verifier | AUTO_RECONCILE / REVIEW_REQUIRED / UNRESOLVED|
|                               |                                         |
|                               v                                         |
|  [ LAYER G: Audit Layer ]                                               |
|  Append-Only Event Store | Evidence Links | Decision Proofs             |
|                               |                                         |
|                               v                                         |
|  [ LAYER H: Evaluation Engine ]                                         |
|  Hidden Ground-Truth Evaluator | Metrics Harness | Latency & Accuracy   |
|                               |                                         |
|                               v                                         |
|  [ LAYER I: Presentation Layer (Next.js) ]                              |
|  Operations Dashboard | Case Inspector | Realtime Benchmark Stream      |
+-------------------------------------------------------------------------+
```

---

## 2. Nine-Layer System Design

### Layer A — Data Plane
- **Purpose:** Generates synthetic, realistic 3-way financial records with known corruption distributions and paired ground-truth labels.
- **Components:** Generator modules, seed controllers, golden fixtures.
- **Boundary Rule:** Ground truth is strictly segregated into `data/ground_truth/` and is never passed to Layer B, C, D, E, or F.

### Layer B — Ingestion
- **Purpose:** Ingests raw multi-source financial feeds (Payment gateway logs, Bank settlement files, Merchant general ledger entries).
- **Validation:** Pydantic schema validation at entry; rejects unparseable records with structured errors.

### Layer C — Normalization
- **Purpose:** Transforms disparate raw data into canonical internal data structures.
- **Rules:**
  - Amounts represented via `Decimal` (no floating-point rounding errors).
  - Currency codes normalized to ISO 4217 uppercase strings.
  - Timestamps normalized to UTC ISO 8601.
  - Identifiers and references cleaned and trimmed.

### Layer D — Deterministic Reconciliation Engine
- **Purpose:** High-speed candidate matching and rule evaluation across the normalized tri-source records.
- **Responsibilities:**
  - Identifies candidate matches across Order IDs, Payment IDs, and Settlement IDs.
  - Evaluates hard financial rules: Exact amount matching, settlement window verification, currency compatibility, duplicate detection.
  - Labels cases that satisfy all deterministic rules as `EXACT_MATCH`.
  - Emits exception cases into the Intelligence pipeline.

### Layer E — Intelligence Layer (AI Investigation & Bounded Reasoning)
- **Purpose:** Analyzes discrepancies, correlates cross-record evidence, and explains anomalies.
- **Agents/Roles:**
  - **Investigator:** Extracts evidence from payment metadata, settlement fee breakdowns, and ledger balance deltas; identifies root causes (e.g., unexpected fee deductions, timing mismatch, partial capture).
  - **Resolver:** Proposes bounded recommendation (`AUTO_RECONCILE`, `REVIEW_REQUIRED`, `UNRESOLVED`).
  - **Verifier:** Performs self-consistency check on AI findings against deterministic inputs.
- **Contract:** Outputs validated Pydantic JSON structures with explicit citations to record fields. Cannot directly mutate database records.

### Layer F — Policy Engine
- **Purpose:** The deterministic gatekeeper that evaluates AI recommendations against organizational financial policy.
- **Decision Outcomes:**
  - `AUTO_RECONCILE`: Discrepancy is within strict automated tolerance (e.g., fee schedule matches known contract variance, all hard constraints verified).
  - `REVIEW_REQUIRED`: Discrepancy requires human controller review (e.g., large amount variance, customer reference typo).
  - `UNRESOLVED`: Insufficient evidence or conflicting signals.

### Layer G — Audit Trail
- **Purpose:** Complete, immutable, append-only traceability of all reconciliation decisions.
- **Payload:** Case ID, deterministic findings, AI reasoning transcript, policy outcome, confidence score, timestamps, software version.

### Layer H — Evaluation Engine
- **Purpose:** Quantitative assessment of METFI's performance against hidden ground truth.
- **Metrics:** Accuracy, Precision, Recall, F1, False-Match Rate (must be 0 on golden sets), False-Unresolved Rate, Processing Throughput (records/sec), Latency percentiles (P50, P95, P99).

### Layer I — Presentation Layer
- **Purpose:** Real-time web interface for finance operations controllers and hackathon evaluators.
- **Stack:** Next.js, TypeScript, Tailwind CSS, shadcn/ui.
- **Views:** Executive Metrics Summary, Reconciliation Batch Runner, Deep-Dive Case Inspector with side-by-side evidence diffs, Audit Log Explorer.

---

## 3. Technology Stack Baseline

- **Backend:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic, PostgreSQL 16
- **Data Processing:** Polars (high-speed tabular analysis) + Python Standard Library (Decimal, datetime)
- **Frontend:** Next.js (App Router), TypeScript, Tailwind CSS, Lucide React
- **Testing & Quality:** Pytest, pytest-asyncio, HTTPX, Ruff (linting & formatting), Mypy (strict type checking)
- **Infrastructure:** Docker, Docker Compose

---

## 4. API Surface Contract

| Method | Route | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Subsystem readiness and health check |
| `POST` | `/api/v1/datasets/generate` | Trigger synthetic dataset generation with seed |
| `POST` | `/api/v1/reconciliation/run` | Execute batch reconciliation run |
| `GET` | `/api/v1/runs/{run_id}` | Retrieve status and summary of reconciliation run |
| `GET` | `/api/v1/cases/{case_id}` | Retrieve deep-dive case details and evidence |
| `GET` | `/api/v1/cases/{case_id}/audit` | Retrieve complete audit trail for a case |
| `GET` | `/api/v1/metrics/{run_id}` | Retrieve ground-truth evaluation metrics |

---

## 5. Security & Isolation Architecture

1. **Model Isolation:** AI models interact exclusively through structured API contracts; no database write connections or execution privileges are granted to LLM runtimes.
2. **Environment Configuration:** All credentials and secrets are managed via environment variables (`.env`).
3. **Audit Immutability:** Audit records are write-only from the operational application layer.
