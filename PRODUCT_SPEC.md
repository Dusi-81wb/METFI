# METFI Product Specification

**Project:** METFI (Autonomous Finance Controller)  
**Hackathon Track:** Razorpay AI Buildathon, Track 04 — AI Finance Controller  
**Version:** 1.0 (Phase 0 Baseline)  

---

## 1. Problem Statement & Context

In high-growth modern commerce and fintech operations (such as Razorpay merchants and payment platforms), financial controllers face the continuous challenge of reconciling transactions across three distinct, asynchronous systems of record:

1. **Payment Gateway Records:** Front-office transaction authorizations, customer references, and gross payment amounts.
2. **Bank / Acquirer Settlement Files:** Net funds transferred by acquiring banks after fee deductions, tax withholding, and settlement delays.
3. **Merchant General Ledger (ERP):** Double-entry accounting records (debits/credits) reflecting expected receivables and revenue recognition.

Manual reconciliation at scale creates massive operational overhead, delayed financial close, uncollected fees, un-reconciled chargebacks, and high human error rates.

Traditional automation fails on non-standard discrepancies (e.g., fee tier anomalies, partial refunds, date skews, reference truncation), while naive LLM wrappers produce hallucinated accounting numbers and introduce security risks.

**METFI provides an autonomous, auditable, and mathematically grounded financial controller that performs deterministic matching, bounded AI exception investigation, and policy-governed resolution.**

---

## 2. Source Data Specifications

METFI ingests and reconciles three distinct record feeds:

### 2.1 Payment Record Schema
- `payment_id`: Unique string identifier for the payment event (e.g., `pay_9823472198`).
- `order_id`: Associated merchant order reference (e.g., `ord_8723461`).
- `customer_id`: Unique identifier of the paying customer.
- `amount`: Gross payment amount represented as exact decimal (e.g., `1250.00`).
- `currency`: 3-letter ISO 4217 code (e.g., `INR`).
- `status`: Payment status (`SUCCESS`, `FAILED`, `PENDING`, `REFUNDED`).
- `payment_timestamp`: UTC timestamp of payment authorization.
- `metadata`: Key-value dictionary containing client parameters, payment method details, and session tags.

### 2.2 Settlement Record Schema
- `settlement_id`: Unique string identifier for the settlement payout (e.g., `set_38472910`).
- `payment_id`: Associated payment identifier.
- `settled_amount`: Net funds settled to merchant account (e.g., `1225.00`).
- `currency`: 3-letter ISO 4217 code.
- `settlement_timestamp`: UTC timestamp of settlement payout.
- `fee`: Platform/gateway processing fee (e.g., `21.19`).
- `fee_tax`: Tax levied on fee (e.g., `3.81` GST).
- `status`: Settlement status (`SETTLED`, `HOLD`, `FAILED`).
- `metadata`: Acquirer reference, UTR, batch settlement id.

### 2.3 Ledger Record Schema
- `ledger_id`: Unique string identifier for the journal entry (e.g., `led_9283741`).
- `order_id`: Associated merchant order reference.
- `debit`: Debit amount in exact decimal (e.g., `1250.00`).
- `credit`: Credit amount in exact decimal (e.g., `0.00`).
- `currency`: 3-letter ISO 4217 code.
- `entry_timestamp`: UTC timestamp of ledger posting.
- `account`: Target ledger account (`ACCOUNTS_RECEIVABLE`, `PAYMENT_GATEWAY_CLEARING`, `BANK_ACCOUNT`, `PROCESSING_FEE_EXPENSE`).
- `status`: Posting status (`POSTED`, `DRAFT`, `REVERSED`).
- `metadata`: Journal voucher id, cost center, accounting tags.

---

## 3. Exception Taxonomy

Every candidate tri-source reconciliation case is classified into one of the canonical 10 categories:

1. **`EXACT_MATCH`**: All payment, settlement, and ledger fields match perfectly. Net settlement equals gross amount minus standard fees and taxes. Date skews are within SLA.
2. **`AMOUNT_MISMATCH`**: Discrepancy between gross payment, ledger entry, or settled amount beyond allowed fee schedules.
3. **`MISSING_SETTLEMENT`**: Payment is marked success in gateway and posted in ledger, but no corresponding settlement payout exists beyond the SLA settlement window.
4. **`DUPLICATE_RECORD`**: Multiple settlement payouts or duplicate ledger entries tied to a single payment authorization.
5. **`DATE_MISMATCH`**: Settlement occurs outside acceptable time windows or precedes payment authorization timestamp.
6. **`REFERENCE_MISMATCH`**: Mismatch between order identifiers, customer IDs, or UTR references across records.
7. **`PARTIAL_SETTLEMENT`**: Settlement payout covers only a fraction of the payment authorization without an accompanying refund or split record.
8. **`FEE_DISCREPANCY`**: Processing fee or GST tax rate calculation does not match contracted fee schedule rules.
9. **`CURRENCY_MISMATCH`**: Multi-currency conversion error or mismatch between payment currency and settlement currency.
10. **`AMBIGUOUS`**: Multi-factor conflict or contradictory evidence that cannot be deterministically categorized without deep investigation.

---

## 4. Reconciliation Outcomes & Policy Gates

Reconciliation outcomes are strictly policy-governed:

```text
[ Reconciliation Case ]
           |
           v
  +-----------------+
  |  Policy Engine  |
  +-----------------+
     /     |     \
    /      |      \
   v       v       v
[AUTO]  [REVIEW]  [UNRESOLVED]
```

1. **`AUTO_RECONCILE`**:
   - Authorized when all deterministic validation rules pass or when the discrepancy is within pre-configured, verified policy bounds (e.g., exact match, or verified standard fee deduction).
   - Zero human intervention required.
2. **`REVIEW_REQUIRED`**:
   - Triggered when an explainable anomaly exists that requires human controller sign-off (e.g., high-value fee variance, suspected duplicate settlement).
   - Accompanied by full AI investigation breakdown, evidence citations, and recommended action.
3. **`UNRESOLVED`**:
   - Triggered when records are irreconcilable, data corruption is detected, or evidence is missing.
   - Surfaced prominently on the controller dashboard for escalated manual investigation.

---

## 5. Audit Trail Requirements

Every processed reconciliation case generates an immutable, structured audit log:
- `audit_id`: UUIDv4
- `case_id`: UUIDv4
- `timestamp`: UTC ISO 8601
- `engine_version`: Semantic version string
- `policy_version`: Semantic policy version
- `ai_model_identifier`: Name/version of LLM used for investigation
- `input_record_references`: Dict containing `{payment_id, settlement_id, ledger_id}`
- `deterministic_findings`: Rule execution results and computed mathematical deltas
- `ai_findings`: Structured investigation report, cited evidence, and root-cause analysis
- `final_decision`: Policy outcome (`AUTO_RECONCILE` | `REVIEW_REQUIRED` | `UNRESOLVED`)
- `confidence`: Calibrated confidence score (0.0 to 1.0)
- `reason_code`: Machine-readable classification code
