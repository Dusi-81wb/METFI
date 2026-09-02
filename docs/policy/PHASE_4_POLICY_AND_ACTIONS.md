# Phase 4 Architecture: Policy-Gated Resolution & Controlled Actions

## 1. System Overview & Authority Model

Phase 4 implements the **Policy-Gated Resolution & Controlled Operational Actions** subsystem for METFI. It takes the authoritative outputs from Phase 2 (**Deterministic Reconciliation Result**) and Phase 3 (**Verified AI Investigation Envelope**) alongside corporate **Domain Policies** to safely resolve exceptions and execute bounded operational actions.

### Core Non-Negotiable Invariants
1. **Primacy of Deterministic Financial Truth:** Canonical reconciliation classifications (`ReconciliationResult`) own financial truth. AI cannot mutate ledger balances, override deterministic match boundaries, or relax constraints.
2. **Primacy of Deterministic Policy Authorization:** AI recommendations are inputs to policy evaluation, never autonomous authorization authorities.
3. **Fail-Closed Safety:** Missing policy configurations, uncertified evidence references, or AI verification rejections immediately fail closed (`REVIEW_REQUIRED` or `UNRESOLVED`).
4. **Idempotency & Concurrency Safety:** Every controlled action carries a cryptographic SHA-256 idempotency key preventing duplicate executions and side-effects.
5. **Zero Real-World Money Movement:** All operational actions execute within a strictly sandboxed, simulated test harness (`SimulationActionExecutor`).

```
+-----------------------------------------------------------------------------------+
|                        INFERENCE & RESOLUTION PIPELINE ARCHITECTURE               |
|                                                                                   |
|  [Raw Sources] ➔ [Deterministic Reconciliation Engine] ➔ [ReconciliationResult]   |
|                                                                   |               |
|                                                                   v               |
|                                                      [AI Context Builder]         |
|                                                                   |               |
|                                                                   v               |
|                                                         [AI Investigator]         |
|                                                                   |               |
|                                                                   v               |
|                                                           [AI Verifier]           |
|                                                                   |               |
|                                                                   v               |
|                                                  [VerifiedInvestigationEnvelope]  |
|                                                                   |               |
|                                                                   v               |
|                                                  [Deterministic Policy Engine]    |
|                                                                   |               |
|                                                                   v               |
|                                                  [Policy Authorization Gate]      |
|                                                                   |               |
|                                         ┌─────────────────────────┴─────────────┐ |
|                                         ▼                                       ▼ |
|                             [Simulated Action Executor]             [Human Review Queue]  |
|                                         │                                       │ |
|                                         └─────────────────────────┬─────────────┘ |
|                                                                   v               |
|                                                      [Immutable Audit Events]     |
+-----------------------------------------------------------------------------------+
```

---

## 2. Action Domain Models & State Machine

Controlled actions follow a strict, validated finite state machine.

```
                  +-------------+
                  |  REQUESTED  |
                  +------+------+
                         |
                         v
                  +-------------+
         +--------+  VALIDATING +--------+
         |        +------+------+        |
         |               |               |
         v               v               v
   +----------+    +------------+   +----------+
   | REJECTED |    | AUTHORIZED |   | REJECTED |
   +----------+    +-----+------+   +----------+
                         |
                         v
                  +-------------+
                  |  EXECUTING  |
                  +------+------+
                         |
                  +------+------+
                  |             |
                  v             v
            +----------+   +----------+
            | EXECUTED |   |  FAILED  |
            +----------+   +----------+
```

### Supported Action Types
- `AUTO_RECONCILE`: Automatically mark transaction group and ledger postings as reconciled.
- `MARK_FOR_REVIEW`: Enqueue case into the human controller review queue with priority.
- `ESCALATE`: Escalate case to senior risk/compliance management.
- `REQUEST_RETRY`: Enqueue retry request to payment gateway / bank settlement batch.
- `REQUEST_MANUAL_VERIFICATION`: Require human operator to upload manual bank slips or receipts.

---

## 3. Deterministic Policy Engine & Hard Gates

The `DeterministicPolicyEngine` evaluates the case against 8 explicit safety gates:

| Gate | Name | Evaluation Rule | Failure Outcome |
|---|---|---|---|
| **1** | **Deterministic Conflict Gate** | Rejects `AUTO_RECONCILE` if classification is `CURRENCY_MISMATCH`, `DUPLICATE_RECORD`, `MISSING_SETTLEMENT`, or `AMBIGUOUS`. | `DENY` |
| **2** | **Verifier Gate** | Blocks autonomous actions if AI Verifier status is `REJECTED` or `INSUFFICIENT_EVIDENCE`. | `DENY` |
| **3** | **Unknown Policy Gate** | Rejects `AUTO_RECONCILE` if fee/tax policy is unconfigured and match is not exact. | `DENY` (Fails closed) |
| **4** | **Variance Tolerance Gate** | Checks fee and tax variances against configured `VarianceTolerancePolicy`. | `DENY` |
| **5** | **Retry Limit Gate** | Validates retry eligibility and enforces `max_retry_attempts`. | `DENY` |
| **6** | **Autonomous Cap Gate** | Blocks autonomous resolution of non-exact matches above monetary threshold. | `DENY` |
| **7** | **Evidence Integrity Gate** | Ensures all cited evidence references are valid and certified. | `DENY` |
| **8** | **Master Switch Gate** | Validates `auto_reconciliation_enabled` master configuration. | `DENY` |

---

## 4. Simulation Action Executor

The `SimulationActionExecutor` implements the `ActionExecutor` protocol:
- **Boundary Authorization Verification:** Direct execution calls on unapproved, non-authorized actions immediately raise `UnauthorizedExecutionError`.
- **Idempotency Cache & Locks:** Enforces unique `idempotency_key` via concurrency locks, ensuring identical repeat requests return cached results without side-effects.
- **Simulated Domain Side-Effects:** Safely simulates ledger mark, settlement status changes, gateway retries, and queue routing.
- **Audit Trail:** Emits structured, immutable `AuditEvent` payloads at execution boundaries.

---

## 5. Human Review & Escalation Queue

The `ReviewQueueService` manages the human controller review queue:
- **Priority-Driven Ordering:** Critical > High > Medium > Low with chronological tie-breaking.
- **Controller Claiming:** Lock assignment of items to specific controllers.
- **Resolution & Escalation:** Structured workflows attaching human rationale notes and resolving actions.

---

## 6. Evaluation & Benchmark Suite

An independent evaluation harness (`backend/app/evaluation/policy_evaluator.py`) measures 8 objective metrics:

```bash
uv run python evaluation/benchmarks/policy_runner.py
```

### Benchmark Metric Targets vs. Actual Results
- **Policy Decision Correctness:** 100.0% (Target: >= 95.0%)
- **Unauthorized Action Rejection Rate:** 100.0% (Mandatory: 100.0%)
- **Duplicate Action Prevention Rate:** 100.0% (Mandatory: 100.0%)
- **Safe Fallback under Unknown Policy:** 100.0% (Mandatory: 100.0%)
- **Verifier-Gated Action Enforcement:** 100.0% (Mandatory: 100.0%)
- **Deterministic Truth Preservation Rate:** 100.0% (Mandatory: 100.0%)
- **Simulated Execution Success Rate:** 100.0% (Target: 100.0%)
- **Average Policy Latency:** 0.20ms (Target: < 10ms)
- **Average Execution Latency:** 0.09ms (Target: < 25ms)
