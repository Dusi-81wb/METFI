# METFI Final Demo Script & Evaluator Walkthrough
## Track 04: AI Finance Controller — Run the Books and the Cash Position

**Financial Truth Preserved • AI Accelerated • Policy Gated • Cryptographically Audited**

This document details the primary evaluation path for METFI. The system runs against the live FastAPI backend (`http://localhost:8000`) and Next.js operations console (`http://localhost:3000`).

---

## 1. System Architecture in 30 Seconds

```text
┌────────────────────────────────────────────────────────┐
│              DETERMINISTIC FINANCIAL CORE              │
│  Normalization ──► 10-Rule Matching ──► Evidence Trace │
└───────────────────────────┬────────────────────────────┘
                            │
         ┌──────────────────▼──────────────────┐
         │      ADVISORY INTELLIGENCE LAYER    │
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

## 2. Recommended Walkthrough Flow

### Step 1: Operations Dashboard (`http://localhost:3000/`)
- **What to Observe**:
  - **The Books**: General ledger journal entries with verified double-entry balancing invariant (`Debits == Credits`, ₹0.00 imbalance).
  - **The Cash Position**: Multi-source liquidity breakdown (Verified Bank Settled Cash, Expected Gateway Volume, In-Transit Clearing Cash, and 24h Forward Cash Projection).
  - **50+ Record Synthetic Batch Loop**: Click **"⚡ Run Finance-Ops Loop"** to watch 500 records reconcile in under 25ms at **80,000+ records/sec**.
  - **The Honest Exception List**: Transparent catalogue of all unresolvable exceptions with explicit financial variance amounts and reasons why auto-posting was safely denied.
  - **Settlement Q&A Agent**: Ask questions like *"What is our verified bank cash position?"* and receive immediate, grounded answers cited from ledger entries.

### Step 2: Sample Data Explorer & Live Randomizer (`http://localhost:3000/data`)
- **What to Observe**:
  - **3-Way Multi-Source Ingest Feeds**: Inspect Payment Gateway records, Bank Settlement statements, and Internal Ledger entries.
  - **Entropy Temperature Slider** (`0.00` to `1.00`): Synthesize clean matches or high-entropy anomalies.
  - **Instant Platform Reconciliation**: Click **"⚡ Run Platform Reconciliation"** to test deterministic matching on generated records in real time.

### Step 3: Interactive 1-Click Showcase (`http://localhost:3000/showcase`)
- **What to Observe**:
  - Click **"1-Click Interactive Showcase"** to watch the full 10-stage lifecycle execute sequentially.
  - Real backend API calls with interactive stage logs, policy authorization, sandbox action simulation, and SHA-256 hash chaining.

### Step 4: Case Detail & Evidence Isolation (`http://localhost:3000/cases/case_demo_101`)
- **What to Observe**:
  - Side-by-side reconciliation of Payment Gateway record vs. Bank Settlement CAMT file.
  - Deterministic Evidence Matrix: Monetary delta (-₹50.00), timestamp difference, fee calculation.
  - AI Investigator diagnosis of gateway interchange rate.
  - Independent AI Verifier checking claims against canonical fields.

### Step 5: Human Review Queue (`http://localhost:3000/review-queue`)
- **What to Observe**:
  - Triage board for exceptions requiring human operator authorization.
  - Interactive Claim, Resolve, and Escalate capabilities emitting cryptographic audit records.

### Step 6: Tamper-Evident Cryptographic Audit Ledger (`http://localhost:3000/audit`)
- **What to Observe**:
  - Monotonically increasing sequence of events (`RECONCILIATION_COMPLETED` → `INVESTIGATION_COMPLETED` → `VERIFICATION_COMPLETED` → `POLICY_EVALUATED` → `ACTION_EXECUTED`).
  - Cryptographic SHA-256 hash chaining: Each event references `previous_event_hash`.
  - Click **"Verify Cryptographic Integrity"** to validate the entire SHA-256 chain in real time (0 breaks).

### Step 7: Unified Benchmark Evaluation (`http://localhost:3000/benchmarks`)
- **What to Observe**:
  - Live results across 7 distinct evaluation suites:
    1. `INDEPENDENT`: 50 uncorrupted real-world transaction groups (100% accuracy).
    2. `ADVERSARIAL`: 24 edge-case stress scenarios (100% isolation).
    3. `AI`: Hypothesis precision & evidence grounding (96.4%).
    4. `POLICY`: Variance tolerances & retry caps (100% adherence).
    5. `AUDIT`: SHA-256 chain continuity & tamper detection (100%).
    6. `BATCH SCALE`: 500-record batch throughput (**80,412 recs/sec**).
    7. `END_TO_END`: Complete intake-to-audit pipeline consistency.

---

## 3. Resilience & Self-Healing
- **If the database is offline**: The application falls back safely to in-memory audit repositories and disk-backed fixture datasets without crashing.
- **If the external AI provider is unavailable**: The system seamlessly engages the deterministic fallback provider (`MockLLMProvider`), generating safe, bounded fallback envelopes with zero downtime.
