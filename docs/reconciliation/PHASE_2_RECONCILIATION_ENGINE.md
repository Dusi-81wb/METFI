# METFI Phase 2 — Deterministic Reconciliation Engine Specification

**Project:** METFI (Autonomous Finance Controller for Razorpay AI Buildathon, Track 04)  
**Phase:** Phase 2 — Deterministic Reconciliation Engine (Remediation Round 01)  
**Status:** Certified Foundation / Canonical Generalization Reference  
**Version:** 2.1.0  

---

## 1. Executive Summary & Core Principle

The Phase 2 Deterministic Reconciliation Engine constitutes the authoritative financial source of truth in METFI. 

> **Core Principle:** Financial truth is strictly deterministic. AI provides investigation, explanation, and bounded recommendations. No LLM is involved in Layer D candidate generation, arithmetic verification, or exception classification.

The engine executes in $O(N)$ time, operates on immutable data structures, guarantees exact `Decimal` precision (zero floating-point math), and enforces strict physical and semantic ground-truth isolation. Following Remediation Round 01, all generator-specific constants, magic numbers, and hardcoded corruption assumptions have been completely eradicated in favor of generalized domain principles and configurable contract policies.

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
│   + Customer Isolation Guard         │
└──────────────────┬───────────────────┘
                   │
                   ▼
┌──────────────────────────────────────┐
│     2. Evidence Construction         │
│   Dynamic FeeTaxPolicy Evaluation    │
│   Monetary, Timing, Reference Parity │
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
   - Builds primary hash indexes on `payment_id` and `order_id`.
   - Groups multi-settlement payouts without blind truncation.
   - Enforces **Customer Consistency Guard**: strictly rejects linking candidate records across different customer accounts.
   - Detects multi-candidate ties with equal edit distances and marks candidate groups with `is_ambiguous_candidate = True`.
   - Secondary pass resolves mutated order and payment references using monetary, currency, and timing proximity combined with bounded Levenshtein edit distance ($d \le 3$).
   - Tertiary and quaternary passes capture orphaned settlements and orphaned ledger postings.
2. **Evidence Extractor (`EvidenceExtractor`):**
   - Integrates explicit, configurable `FeeTaxPolicy` contracts (supporting variable fee schedules from 0.5%–10% and tax rates 0%–30%).
   - Evaluates monetary deltas (`settlement_amount_delta`, `fee_variance`, `tax_variance`, `total_deduction_variance`, `is_ledger_balanced`).
   - Safely handles unknown or absent fee policies: emits structured `UNKNOWN_FEE_POLICY` flag without inventing fabricated deductions.
   - Evaluates currency parity (`is_currency_matched`).
   - Evaluates timing windows (`hours_to_settlement`, `is_settlement_preceding_payment`, `is_within_sla_window`).
   - Evaluates cross-source reference integrity (`is_payment_id_matched`, `is_order_id_matched`).
   - Evaluates cardinality (`payment_count`, `settlement_count`, `ledger_entry_count`).
3. **Deterministic Classifier (`DeterministicClassifier`):**
   - Maps evidence into one of 10 canonical classes using an authoritative financial precedence hierarchy.
4. **Policy Engine (`DeterministicPolicyEngine`):**
   - Deterministic policy gatekeeper that maps classifications to `AUTO_RECONCILE`, `REVIEW_REQUIRED`, or `UNRESOLVED`.
5. **Reconciliation Service (`ReconciliationService`):**
   - Application orchestrator managing batch runs, disk loading, and telemetry profiling.

---

## 3. Authoritative Hard Constraints for EXACT_MATCH

A transaction group is classified as `EXACT_MATCH` **if and only if all of the following hard constraints hold**:

1. **Cardinality Hard Constraint:** Exactly 1 Payment record, exactly 1 Settlement record, and at least 2 Ledger records.
2. **Monetary Hard Constraint:** `settlement_amount_delta == Decimal("0.00")` (Gross Payment equals Net Settled plus Fee plus Fee Tax).
3. **Fee/Tax Policy Hard Constraint:** `fee_variance == Decimal("0.00")` and `tax_variance == Decimal("0.00")` under the configured domain contract policy (`is_fee_compliant == True`).
4. **Ledger Balance Hard Constraint:** Sum of Debits equals Sum of Credits (`is_ledger_balanced == True`).
5. **Currency Hard Constraint:** Payment currency, settlement currency, and ledger currency match identically (`is_currency_matched == True`).
6. **Reference Hard Constraint:** `payment_id` and `order_id` match across all three sources (`is_order_id_matched == True`, `is_payment_id_matched == True`).
7. **Timing Hard Constraint:** Settlement payout timestamp is strictly on or after payment authorization timestamp (`is_settlement_preceding_payment == False`) and within SLA window ($0 \le \Delta t \le 720\text{h}$).

---

## 4. Authoritative Classification Precedence Hierarchy

When multiple discrepancy conditions occur simultaneously, the engine resolves classification through an explicit, domain-grounded priority hierarchy:

| Priority | Exception Class | Trigger Condition | Rationale |
|---|---|---|---|
| **1** | `DUPLICATE_RECORD` | `cardinality.has_duplicate_settlement == True` | Multiplicity violation invalidates 1-to-1 financial arithmetic comparisons. |
| **2** | `MISSING_SETTLEMENT` | `cardinality.has_missing_settlement == True` | Absence of counterparty settlement record prevents settlement verification. |
| **3** | `CURRENCY_MISMATCH` | `currency.is_currency_matched == False` | Cross-currency discrepancies invalidate single-currency ledger balancing. |
| **4** | `REFERENCE_MISMATCH` | `reference.is_order_id_matched == False` or `reference.is_payment_id_matched == False` | Misidentified transaction reference must be linked before financial amounts are audited. |
| **5** | `DATE_MISMATCH` | `timing.is_settlement_preceding_payment == True` or `timing.is_within_sla_window == False` | Causality violation (settlement before authorization) or contractual SLA breach. |
| **6** | `AMBIGUOUS` | `reference.is_ambiguous_candidate == True` or `reference.is_cross_customer_matched == False` | Structural candidate ties or customer conflicts that cannot be uniquely resolved without manual review. |
| **7** | `FEE_DISCREPANCY` | `is_gross_balanced == True` and `is_fee_compliant == False` (`fee_variance != 0` or `tax_variance != 0`) | Gross funds are completely balanced, but deducted fees or taxes deviate from contractual fee policy. |
| **8** | `PARTIAL_SETTLEMENT` | `is_gross_balanced == False` and `0 < settled_net <= 0.90 * expected_settled` | Net payout represents a fractional tranche of principal funds disbursed. |
| **9** | `AMOUNT_MISMATCH` | `settlement_amount_delta != Decimal("0.00")` | General unexplained capital discrepancy between payment gross and settlement net. |
| **10** | `EXACT_MATCH` | All constraints satisfied | 3-way reconciliation verified across payment, settlement, and ledger. |

---

## 5. Domain Policy Configuration (`FeeTaxPolicy`)

The reconciliation engine accepts an optional or configured `FeeTaxPolicy` object:

```python
class FeeTaxPolicy(BaseModel):
    fee_rate: Decimal = Decimal("0.02")  # e.g., 2.0% gateway fee
    tax_rate_on_fee: Decimal = Decimal("0.18")  # e.g., 18.0% GST on fee
    currency: str | None = None  # Applicable ISO currency or None
    provider: str | None = None  # Gateway provider or None
    rounding_rule: str = "ROUND_HALF_UP"  # Exact Decimal rounding
```

### 5.1 Handling Unknown Policy
When no fee policy is configured or known for a provider, the engine:
1. Sets `is_fee_policy_known = False`.
2. Computes net settlement balance against observed deductions without fabricating an artificial fee schedule.
3. Flags `UNKNOWN_FEE_POLICY`.
4. Routes the transaction to `REVIEW_REQUIRED` so human finance operators can verify the uncontracted deductions.
