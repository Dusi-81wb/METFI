# METFI Phase 2 — Deterministic Reconciliation Engine Specification

**Project:** METFI (Autonomous Finance Controller for Razorpay AI Buildathon, Track 04)  
**Phase:** Phase 2 — Deterministic Reconciliation Engine  
**Status:** Frozen Foundation / Canonical Engine Reference  
**Version:** 2.0.0  

---

## 1. Executive Summary & Core Principle

The Phase 2 Deterministic Reconciliation Engine constitutes the authoritative financial source of truth in METFI. 

> **Core Principle:** Financial truth is strictly deterministic. AI provides investigation, explanation, and bounded recommendations. No LLM is involved in Layer D candidate generation, arithmetic verification, or exception classification.

The engine executes in $O(N)$ time, operates on immutable data structures, guarantees exact `Decimal` precision (zero floating-point math), and enforces strict physical and semantic ground-truth isolation.

---

## 2. Architecture & Processing Pipeline

The reconciliation engine is structured into five decoupled, independently testable stages:

```text
[ Canonical Ingest Feeds ]
(Payments, Settlements, Ledger)
               │
               ▼
┌──────────────────────────────────────┐
│     1. Candidate Generation          │
│   Hash Indexing (O(N)) + Levenshtein │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│     2. Evidence Construction         │
│   Exact Monetary, Timing, Reference  │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│  3. Deterministic Classification     │
│   10-Class Domain Precedence Engine  │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│       4. Policy Gate Mapping         │
│    AUTO_RECONCILE / REVIEW / UNRES   │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│     5. Result Construction           │
│   Immutable ReconciliationResult     │
└──────────────────────────────────────┘
```

### 2.1 Component Responsibilities
1. **Candidate Matcher (`CandidateMatcher`):**
   - Builds primary hash maps on `payment_id` and `order_id`.
   - Performs primary grouping around authorized payments.
   - Secondary pass resolves mutated order references (e.g. `REFERENCE_MISMATCH`) using monetary, currency, and timing proximity combined with bounded Levenshtein edit distance ($d \le 3$).
   - Tertiary and quaternary passes capture orphaned settlements and orphaned ledger postings.
2. **Evidence Extractor (`EvidenceExtractor`):**
   - Evaluates monetary deltas (`settlement_amount_delta`, `fee_variance`, `is_ledger_balanced`).
   - Evaluates currency parity (`is_currency_matched`).
   - Evaluates timing windows (`hours_to_settlement`, `is_settlement_preceding_payment`, `is_within_sla_window`).
   - Evaluates cross-source reference integrity (`is_payment_id_matched`, `is_order_id_matched`).
   - Evaluates cardinality (`payment_count`, `settlement_count`, `ledger_entry_count`).
3. **Deterministic Classifier (`DeterministicClassifier`):**
   - Maps evidence into one of 10 canonical classes using an authoritative precedence hierarchy.
4. **Policy Engine (`DeterministicPolicyEngine`):**
   - Deterministic policy gatekeeper that maps classifications to `AUTO_RECONCILE`, `REVIEW_REQUIRED`, or `UNRESOLVED`.
5. **Reconciliation Service (`ReconciliationService`):**
   - Application orchestrator managing batch runs, disk loading, and telemetry profiling.

---

## 3. Authoritative Hard Constraints for EXACT_MATCH

A transaction group is classified as `EXACT_MATCH` **if and only if all of the following hard constraints hold**:

1. **Cardinality Hard Constraint:** Exactly 1 Payment record, exactly 1 Settlement record, and at least 2 Ledger records.
2. **Monetary Hard Constraint:** `settlement_amount_delta == Decimal("0.00")` (Gross Payment equals Net Settled plus Fee plus Fee Tax).
3. **Fee Arithmetic Hard Constraint:** `fee_variance == Decimal("0.00")` (Fee equals standard 2.00% of gross, Fee Tax equals 18.00% GST on fee).
4. **Ledger Balance Hard Constraint:** Sum of Debits equals Sum of Credits (`is_ledger_balanced == True`).
5. **Currency Hard Constraint:** Payment currency, settlement currency, and ledger currency match identically (`is_currency_matched == True`).
6. **Reference Hard Constraint:** `payment_id` and `order_id` match across all three sources (`is_order_id_matched == True`, `is_payment_id_matched == True`).
7. **Timing Hard Constraint:** Settlement payout timestamp is strictly on or after payment authorization timestamp (`is_settlement_preceding_payment == False`) and within 30-day SLA window ($0 \le \Delta t \le 720\text{h}$).

---

## 4. Classification Precedence Policy

When multiple discrepancy conditions occur simultaneously, the engine resolves classification through an explicit, domain-grounded priority hierarchy:

| Priority | Exception Class | Trigger Condition | Rationale |
|---|---|---|---|
| **1** | `DUPLICATE_RECORD` | `settlement_count > 1` | Multiplicity violation invalidates 1-to-1 financial arithmetic comparisons. |
| **2** | `MISSING_SETTLEMENT` | `settlement_count == 0` | Missing mandatory settlement stream prevents net payout reconciliation. |
| **3** | `CURRENCY_MISMATCH` | `is_currency_matched == False` | Cross-currency reconciliation cannot proceed without authoritative FX tables. |
| **4** | `REFERENCE_MISMATCH` | `is_order_id_matched == False` or `is_payment_id_matched == False` | Broken identity linkage across ledger/gateway precedes timing or fee analysis. |
| **5** | `DATE_MISMATCH` | `is_settlement_preceding_payment == True` or `hours > 720` | Chronological violation or SLA breach invalidates standard settlement cycle. |
| **6** | `PARTIAL_SETTLEMENT` | Net settled amount is exact ~50% fraction ($0.50 \times \text{expected}$) with standard fee structure | Explicit fractional payout pattern distinct from arbitrary fee or amount delta. |
| **7** | `FEE_DISCREPANCY` | Gross equals Settled plus Deductions, but fee rate deviates from 2.0% schedule | Explains entire monetary difference as a contract pricing dispute rather than missing capital. |
| **8** | `AMBIGUOUS` | Small unexplained delta (e.g. $\pm ₹12.50$) or multi-factor conflict | Requires AI investigation and LLM root-cause reasoning. |
| **9** | `AMOUNT_MISMATCH` | Unexplained net delta between settled amount and expected gross minus deductions | Capital variance requiring manual audit. |
| **10** | `EXACT_MATCH` | All hard constraints verified | Clean 3-way match. |

---

## 5. Policy Engine Mapping

| Classification | Authorized Policy Outcome | Human Intervention |
|---|---|---|
| `EXACT_MATCH` | `AUTO_RECONCILE` | Zero (Automated) |
| `AMOUNT_MISMATCH` | `REVIEW_REQUIRED` | Controller sign-off required |
| `DUPLICATE_RECORD` | `REVIEW_REQUIRED` | Controller sign-off required |
| `DATE_MISMATCH` | `REVIEW_REQUIRED` | Controller sign-off required |
| `REFERENCE_MISMATCH` | `REVIEW_REQUIRED` | Controller sign-off required |
| `PARTIAL_SETTLEMENT` | `REVIEW_REQUIRED` | Controller sign-off required |
| `FEE_DISCREPANCY` | `REVIEW_REQUIRED` | Controller sign-off required |
| `MISSING_SETTLEMENT` | `UNRESOLVED` | Escalated / Incomplete evidence |
| `CURRENCY_MISMATCH` | `UNRESOLVED` | Escalated / FX investigation |
| `AMBIGUOUS` | `UNRESOLVED` | Escalated to AI Investigation (Phase 3) |

---

## 6. Evaluation & Benchmark Methodology

The independent evaluator (`BenchmarkEvaluator`) loads ground truth exclusively during benchmark evaluation and computes:
1. **Overall Micro-Accuracy:** Correct classifications divided by total records.
2. **Macro-Averaged F1:** Unweighted arithmetic mean of per-class F1 scores across all 10 classes.
3. **Per-Class Metrics:** True Positives, False Positives, False Negatives, Precision, Recall, and F1.
4. **False-Match Rate (FMR):** Proportion of exception cases incorrectly classified as `EXACT_MATCH` (Target: **0.0%**).
5. **False-Unresolved Rate (FUR):** Proportion of clean `EXACT_MATCH` cases incorrectly marked as `UNRESOLVED`.
6. **10x10 Confusion Matrix:** Exact cross-classification matrix.
7. **Failure Diagnosis Report:** Full diagnostic dump of any misclassified cases.

---

## 7. Performance & Latency Benchmarks

| Tier | Size | Total Latency | Throughput | P50 Latency | P95 Latency | P99 Latency | Accuracy | Macro F1 | FMR |
|---|---|---|---|---|---|---|---|---|---|
| **Development (`dev_500`)** | 500 | 21.21 ms | 94,041 rec/s | 0.035 ms | 0.045 ms | 0.056 ms | **100.0%** | **1.0000** | **0.00%** |
| **Stress (`stress_5000`)** | 5,000 | 258.82 ms | 77,080 rec/s | 0.035 ms | 0.059 ms | 0.119 ms | **100.0%** | **1.0000** | **0.00%** |
| **Large-Batch (`stress_10000`)** | 10,000 | 614.86 ms | 64,893 rec/s | 0.036 ms | 0.076 ms | 0.148 ms | **100.0%** | **1.0000** | **0.00%** |
