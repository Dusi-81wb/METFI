# METFI Final Demo Script & Evaluator Walkthrough
**Financial Truth Preserved. AI Accelerated. Policy Gated. Cryptographically Audited.**

This document details the primary judge-facing evaluation path for METFI. The system runs against the live FastAPI backend (`localhost:8000`) and Next.js operations console (`localhost:3000`).

---

## 1. System Architecture in 30 Seconds

```text
               ┌────────────────────────────────────────────────────────┐
               │              DETERMINISTIC FINANCIAL CORE              │
               │  Normalization ──► 10-Rule Matching ──► Evidence Trace │
               └───────────────────────────┬────────────────────────────┘
                                           │
                        ┌──────────────────▼──────────────────┐
                        │      ADVISORY INTELLIGENCE LAYER     │
                        │   AI Hypothesis ──► AI Verifier Gate│
                        └──────────────────┬──────────────────┘
                                           │
               ┌───────────────────────────▼────────────────────────────┐
               │              GOVERNANCE & AUDIT CONTROLS               │
               │  Deterministic Policy ──► Action ──► SHA-256 Hash Chain│
               └────────────────────────────────────────────────────────┘
```

**Core Principle:**
AI investigates anomalies and proposes root causes, but **NEVER** overrides deterministic truth, **NEVER** directly writes to financial ledgers, and **CANNOT** bypass policy authorization gates.

---

## 2. Recommended 10-Step Judge Walkthrough

### Step 1: Operations Dashboard (`http://localhost:3000/`)
- **What to Observe**:
  - Real-time engine health indicators (Deterministic Matcher, AI Verifier, Policy Engine, Audit Ledger).
  - High-level KPIs computed deterministically from real database cases.
  - Zero placeholder values or fabricated metrics.

### Step 2: Batch Financial Reconciliation (`http://localhost:3000/reconciliation`)
- **Action**: Select the `dev_500` dataset and click **"Run Reconciliation"**.
- **What to Observe**:
  - Processing speed: 500 transaction groups reconciled deterministically in < 250ms.
  - Category breakdown: Exact matches vs. Amount discrepancies, Fee deductions, Missing settlements, and Ambiguous records.
  - Zero AI involvement in this layer: 100% pure mathematical and rule-based truth.

### Step 3: Exception Queue (`http://localhost:3000/exceptions`)
- **Action**: Filter by `FEE_DISCREPANCY` or `AMOUNT_MISMATCH`.
- **What to Observe**:
  - Isolated exception records with exact monetary variances and delta percentages.
  - Click on any case (e.g. `CASE_ORD_10029` or `case_demo_101`) to inspect details.

### Step 4: Case Detail & Evidence Isolation (`http://localhost:3000/cases/[caseId]`)
- **What to Observe**:
  - Side-by-side reconciliation of Payment Gateway record vs. Internal General Ledger.
  - Deterministic Evidence Matrix: Monetary delta, timestamp discrepancy, fee calculation match.
  - Authoritative classification that is immutable and locked against LLM hallucination.

### Step 5: Evidence-Grounded AI Investigation
- **Action**: On the Case Detail page, click **"Run AI Investigation"**.
- **What to Observe**:
  - AI analyzes evidence fields without seeing ground truth.
  - Structured output identifies the root cause (e.g. `PROCESSING_FEE_DEDUCTION` at 2.0% contractual rate).
  - Explicit evidence citations linking claims directly to fields (`monetary.amount_delta`).

### Step 6: Independent AI Verifier Gate
- **What to Observe**:
  - The independent Verifier automatically checks the AI's claims.
  - Validates that citations exist in the context, contains zero contradictions, and does not dispute deterministic truth.
  - Verification outcome: `VERIFIED` (or `REJECTED` if hallucinations occur).

### Step 7: Deterministic Policy Gating (`http://localhost:3000/actions`)
- **What to Observe**:
  - The Policy Engine evaluates corporate rules: Authority Hierarchy (`Deterministic Truth > Policy > AI > Action`).
  - Checks if the ₹100 fee discrepancy is within the corporate ₹150 variance tolerance.
  - Verdict: `AUTHORIZED` for autonomous adjustment, or routed to `MANUAL_REVIEW_REQUIRED`.

### Step 8: Human Review Queue (`http://localhost:3000/review-queue`)
- **Action**: Open the review queue to inspect cases flagged for human operator sign-off.
- **What to Observe**:
  - Operator claim and resolution flow with notes and immutable audit event emission.
  - Unsafe cases or ambiguous ties cannot be auto-executed by AI.

### Step 9: Tamper-Evident Cryptographic Audit Trail (`http://localhost:3000/audit`)
- **Action**: Enter the case ID and inspect the lifecycle timeline.
- **What to Observe**:
  - Monotonically increasing sequence of events (`RECONCILIATION_COMPLETED` → `INVESTIGATION_COMPLETED` → `VERIFICATION_COMPLETED` → `POLICY_EVALUATED` → `ACTION_EXECUTED`).
  - Cryptographic SHA-256 hash chaining: Each event references `previous_event_hash`.
  - Click **"Verify Cryptographic Integrity"** to validate the entire SHA-256 chain in real time.
  - Zero sensitive secrets or API tokens exposed (automatically sanitized).

### Step 10: Unified Benchmark Evaluation (`http://localhost:3000/benchmarks`)
- **Action**: Click **"Run Full Benchmark Suite"**.
- **What to Observe**:
  - Live results across 7 distinct evaluation suites:
    1. `INDEPENDENT`: 50 uncorrupted real-world transaction groups.
    2. `ADVERSARIAL`: 24 edge-case stress scenarios (boundary amounts, Unicode, negative values).
    3. `AI`: Hypothesis precision, evidence grounding, and verifier challenge accuracy.
    4. `POLICY`: Rule adherence, tolerance enforcement, and deterministic authority.
    5. `AUDIT`: SHA-256 chain continuity and tamper detection rate (100%).
    6. `SYNTHETIC`: Large-scale statistical generalization.
    7. `END_TO_END`: Complete intake-to-audit pipeline consistency.
  - Clear reporting of limitations, metrics, and dataset scopes.

---

## 3. Dedicated Interactive Guided Showcase (`http://localhost:3000/showcase`)
For an accelerated 2-minute demonstration:
1. Navigate to `/showcase`.
2. Click **"Execute Live Showcase Pipeline"**.
3. Watch the 10 stages execute sequentially with real API responses, interactive stage logs, and cryptographic verification.

---

## 4. Demo Recovery & Resilience
- **If the backend is not yet started**: Frontend displays a clear connection banner with the exact retry command (`cd backend && uv run uvicorn app.main:app --port 8000`).
- **If the database is offline**: The application falls back safely to in-memory audit repositories and disk-backed fixture datasets without crashing.
- **If the external AI provider is unavailable**: The system seamlessly engages the deterministic fallback provider (`MockLLMProvider`), generating safe, bounded fallback envelopes.
