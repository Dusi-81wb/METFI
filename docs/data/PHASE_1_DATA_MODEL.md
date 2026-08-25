# METFI Phase 1 Data Foundation & Ground-Truth Isolation Model

**Version:** 1.0.0  
**Phase:** Phase 1 — Domain Schemas, Normalization, Synthetic Generation & Isolation  
**Authors:** Antigravity IDE (Principal Builder)  
**Status:** Canonical Reference Document  

---

## 1. Overview & Architectural Principles

The METFI data layer establishes a mathematically strict, deterministic, and isolated financial dataset foundation for multi-source reconciliation. It fulfills three critical guarantees:

1. **Exact Monetary Precision:** All monetary arithmetic uses `Decimal` with banker/half-up rounding (`ROUND_HALF_UP`) quantized to 2 decimal places (`0.01`). Binary floating-point representation (`float`) is strictly prohibited in financial calculations.
2. **Deterministic Reproducibility:** Every generated dataset is completely reproducible given a generator version and random seed.
3. **Strict Physical & Semantic Ground-Truth Isolation:** Inference inputs (`data/generated/<dataset_id>/input/`) are physically segregated from ground-truth evaluation artifacts (`data/ground_truth/<dataset_id>/`). Inference inputs and metadata contain zero hidden labels, policy outcomes, or fault descriptions.

---

## 2. Tri-Source Domain Schemas

### 2.1 Payments Source (Gateway / Processor)
Represents transaction authorizations captured at the payment gateway:
- `payment_id` (`str`): Unique gateway payment identifier (e.g. `pay_42_00001`).
- `order_id` (`str`): Merchant checkout order reference (e.g. `ord_42_00001`).
- `customer_id` (`str`): Customer entity reference (e.g. `cust_1042`).
- `amount` (`Decimal`): Gross authorized transaction amount.
- `currency` (`str`): ISO 4217 uppercase 3-letter currency code (e.g. `INR`).
- `status` (`PaymentStatus`): Enum (`SUCCESS`, `FAILED`, `PENDING`, `REFUNDED`).
- `payment_timestamp` (`datetime`): UTC timezone-aware authorization timestamp.
- `metadata` (`dict`): Gateway specific attributes (payment method, card network).

### 2.2 Settlements Source (Acquirer / Bank Payout)
Represents funds disbursed into merchant accounts post-processing:
- `settlement_id` (`str`): Unique settlement batch/payout identifier.
- `payment_id` (`str`): Associated payment reference.
- `settled_amount` (`Decimal`): Net funds received.
- `fee` (`Decimal`): Gateway processing fee deducted.
- `fee_tax` (`Decimal`): Tax levied on fee (e.g. 18% GST).
- `currency` (`str`): ISO 4217 uppercase currency code.
- `settlement_timestamp` (`datetime`): UTC timezone-aware payout timestamp.
- `status` (`SettlementStatus`): Enum (`SETTLED`, `HOLD`, `FAILED`).
- `metadata` (`dict`): Banking/acquirer metadata.

### 2.3 General Ledger Source (Merchant ERP / Accounting)
Represents double-entry accounting journal postings:
- `ledger_id` (`str`): Journal entry voucher identifier (e.g. `led_42_00001_dr`).
- `order_id` (`str`): Merchant order reference.
- `debit` (`Decimal`): Debit monetary value.
- `credit` (`Decimal`): Credit monetary value.
- `currency` (`str`): ISO 4217 uppercase currency code.
- `entry_timestamp` (`datetime`): UTC timezone-aware journal posting timestamp.
- `account` (`LedgerAccount`): Enum (`PAYMENT_GATEWAY_CLEARING`, `ACCOUNTS_RECEIVABLE`, `BANK_ACCOUNT`, `PROCESSING_FEE_EXPENSE`, `SALES_REVENUE`, `REFUND_EXPENSE`).
- `status` (`LedgerStatus`): Enum (`POSTED`, `DRAFT`, `REVERSED`).

---

## 3. Canonical Normalization Pipeline

Raw ingests from disparate feeds pass through deterministic normalization before reaching the reconciliation core:

```
[Raw Payment Ingest]    ──> [normalize_payment]    ──> [CanonicalPayment]
[Raw Settlement Ingest] ──> [normalize_settlement] ──> [CanonicalSettlement]
[Raw Ledger Ingest]     ──> [normalize_ledger]     ──> [CanonicalLedgerEntry]
```

### Normalization Rules:
- **Identifier Sanitization:** Leading/trailing whitespace trimmed; empty strings rejected with `NormalizationError`.
- **Monetary Quantization:** Coerced to exact 2-decimal `Decimal` using `ROUND_HALF_UP`. Negative amounts rejected for gross payments and settlements.
- **Currency Normalization:** Trimmed and converted to uppercase ISO 4217 (`" inr "` -> `"INR"`).
- **Timestamp Parsing:** Standardized to UTC timezone-aware ISO 8601 strings (`YYYY-MM-DDTHH:MM:SSZ`). Naive datetimes are explicitly converted to UTC.
- **Strict Error Handling:** Malformed records are never silently coerced; they raise explicit `NormalizationError` detailing the faulty field and record payload.

---

## 4. Canonical Exception Taxonomy (10 Classes)

The dataset generator models realistic financial edge cases with mathematical precision:

| Class Name | Target % | Semantic Description | Expected Policy Outcome |
|---|---|---|---|
| `EXACT_MATCH` | 60.0% | 3-way match across payment, settlement, and ledger | `AUTO_RECONCILE` |
| `AMOUNT_MISMATCH` | 10.0% | Variance between net settled and expected gross minus fees | `REVIEW_REQUIRED` |
| `MISSING_SETTLEMENT` | 6.0% | Payment authorized but payout omitted beyond SLA window | `UNRESOLVED` |
| `DUPLICATE_RECORD` | 5.0% | Multiple settlement disbursements for a single payment | `REVIEW_REQUIRED` |
| `DATE_MISMATCH` | 5.0% | Settlement timestamp precedes payment or exceeds 30-day SLA | `REVIEW_REQUIRED` |
| `REFERENCE_MISMATCH` | 4.0% | Typo, transposition, or truncation in order reference | `REVIEW_REQUIRED` |
| `PARTIAL_SETTLEMENT` | 3.0% | Payout covers only a fraction (e.g. 50%) of the transaction | `REVIEW_REQUIRED` |
| `FEE_DISCREPANCY` | 2.0% | Non-contractual processing fee deducted by gateway | `REVIEW_REQUIRED` |
| `CURRENCY_MISMATCH` | 2.5% | Settlement disbursed in alternate currency without FX adjustment | `UNRESOLVED` |
| `AMBIGUOUS` | 2.5% | Complex multi-factor anomaly requiring deep evidence reasoning | `UNRESOLVED` |

---

## 5. Ground-Truth Isolation & File Topology

To prevent data contamination and benchmark overfitting, files are segregated at rest:

```text
data/
├── generated/
│   ├── dev_500/
│   │   └── input/
│   │       ├── payments.json       # 500 records (NO labels)
│   │       ├── settlements.json    # 495 records (NO labels)
│   │       ├── ledger.json         # 1000 records (NO labels)
│   │       └── manifest.json       # Input record counts and seed ONLY
│   └── stress_5000/
│       └── input/
│           ├── payments.json       # 5000 records
│           ├── settlements.json    # 4950 records
│           ├── ledger.json         # 10000 records
│           └── manifest.json
└── ground_truth/
    ├── dev_500/
    │   ├── ground_truth.json       # GroundTruthRecord objects with expected classes
    │   └── manifest.json           # Audit manifest with SHA256 checksums & full distribution
    └── stress_5000/
        ├── ground_truth.json
        └── manifest.json
```

---

## 6. Deterministic Reproducibility & Benchmark Tiers

### 6.1 Benchmark Tiers
- **Development Tier (`dev_500`):** 500 transactions, random seed `42`.
- **Stress Tier (`stress_5000`):** 5,000 transactions, random seed `1337`.

### 6.2 Generator Execution
```bash
# Generate dev benchmark
python data/generators/cli.py --size 500 --seed 42 --dataset-id dev_500

# Generate stress benchmark
python data/generators/cli.py --size 5000 --seed 1337 --dataset-id stress_5000

# Inspect dataset
python data/generators/inspect_dataset.py --dataset-id dev_500
```
