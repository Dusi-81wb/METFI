# METFI Phase 6: Operations Console & Showcase Demo

## 1. Architectural Philosophy

The **METFI Operations Console** provides a production-grade interface designed for financial controllers, compliance officers, technical evaluators, and judges.

### Core Invariant: Deterministic Primacy
- **AI Recommends, Policy Decides.** The user interface maintains an explicit visual boundary between **DETERMINISTIC FACT** (immutable ledger records, discrepancy calculations, tolerance rules) and **AI INTERPRETATION** (causal hypotheses, natural language summaries).
- **No TypeScript Business Logic Duplication.** The frontend never attempts to perform financial calculations or policy gating locally; all numbers and states are fetched from verified backend APIs.
- **Zero Fabricated Zeroes.** When a backend connection fails or data is loading, the UI explicitly renders error, loading, or partial states.

---

## 2. Interface Navigation & Page Taxonomy

| Route | View Name | Purpose |
|---|---|---|
| `/` | **Operations Dashboard** | Executive summary of processed records, latency profiles, and review queue counts. |
| `/showcase` | **1-Click Showcase Demo** | Interactive 10-stage execution walking through an end-to-end exception resolution lifecycle. |
| `/reconciliation` | **Reconciliation Workspace** | Batch-level view with match statistics, rules evaluated, and discrepancy breakdown. |
| `/exceptions` | **Exceptions Manager** | Discrepancy triage table filtered by severity, category, and source feeds. |
| `/cases/[caseId]` | **Case Detail (Primary Demo)** | Deep story of a single exception with side-by-side deterministic evidence and AI investigation. |
| `/review-queue` | **Controller Review Queue** | Human-in-the-loop triage interface with Claim, Resolve, and Escalate capabilities. |
| `/actions` | **Controlled Actions Tracker** | State machine visualization of policy-authorized sandbox executions with idempotency keys. |
| `/audit` | **Audit Trail & Hash Verifier** | Chronological timeline and live mathematical SHA-256 hash chain verification. |
| `/benchmarks` | **Evaluation Benchmarks** | Objective 8-dimension metrics across all previous phases. |

---

## 3. Case Detail Screen: The 10-Stage Story

The primary demonstration screen (`/cases/[caseId]`) exposes the complete financial exception lifecycle in strict chronological order:

```
1. Financial Evidence (Payment, Settlement, Ledger records)
   ↓
2. Deterministic Reconciliation Result (FEE_VARIANCE, -₹50.00)
   ↓
3. Visual Boundary (DETERMINISTIC FACT vs. AI INTERPRETATION)
   ↓
4. AI Investigation (Root Cause Analysis, Autonomous Agent Engine)
   ↓
5. AI Verifier Safety Gate (100% Grounded, No Contradictions)
   ↓
6. Deterministic Policy Gate (ALLOW_VARIANCE_TOLERANCE, Safe Limits)
   ↓
7. Controlled Action State Machine (AUTO_RECONCILE, Simulation Sandbox)
   ↓
8. SHA-256 Audit Trail & Live Hash Chain Verification (Genesis to Leaf Verified)
```
