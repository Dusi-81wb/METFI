# METFI Master Specification v1.0

**Project:** METFI
**Track:** AI Finance Controller
**Repository:** https://github.com/Dusi-81wb/METFI
**Framework:** METFI Autonomous Finance Controller
**Architecture Review:** Automated Adversarial Hardening Suite
**Status:** FROZEN FOUNDATION
**Version:** 1.0

---

## 0. Executive Summary

METFI is an autonomous finance controller focused on one closed-loop finance-operations problem: **multi-source financial reconciliation**.

METFI ingests synthetic payment, settlement, and ledger records; normalizes and deterministically reconciles them; identifies exceptions; uses AI to investigate and explain ambiguous cases; applies explicit policy gates to determine whether a case can be automatically reconciled or must be reviewed; records an immutable audit trail; and evaluates itself against hidden ground truth.

The central product principle is:

> **Financial truth is deterministic. AI provides investigation, explanation, and bounded recommendations.**

The system must be measurable, reproducible, auditable, and demoable. The design directly targets the Track 04 requirements of processing a batch of synthetic records and demonstrating throughput, measured accuracy, and an honest exception list.

---

## 1. Goals

### 1.1 Primary Goal

Close one complete finance-ops loop from raw records to reconciled outcomes, exception handling, audit evidence, and measurable evaluation.

### 1.2 Competition Goals

METFI must demonstrate:

- Reliable batch processing.
- High measured reconciliation accuracy.
- Transparent exception detection.
- Explainable AI-assisted investigation.
- Strict control over AI actions.
- Reproducible benchmark results.
- Clear auditability.
- A polished 5-minute demonstration.

### 1.3 Non-Goals

METFI v1.0 will not attempt to be:

- A production banking platform.
- A general-purpose ERP.
- A broad fraud-detection platform.
- A payment gateway replacement.
- An unrestricted autonomous financial agent.
- A multi-agent swarm with unnecessary complexity.

---

## 2. Product Definition

### 2.1 Core Workflow

```text
Synthetic Financial Sources
        |
        v
     Ingestion
        |
        v
   Normalization
        |
        v
 Deterministic Reconciliation
        |
        +----------------------+
        |                      |
      Match                Exception
        |                      |
        |                      v
        |               AI Investigation
        |                      |
        |               AI Recommendation
        |                      |
        |                      v
        |                 Policy Engine
        |                      |
        +----------+-----------+
                   |
          +--------+--------+
          |        |        |
        AUTO     REVIEW  UNRESOLVED
          |        |        |
          +--------+--------+
                   |
                   v
              Audit Trail
                   |
                   v
               Evaluation
                   |
                   v
                Dashboard
```

### 2.2 Primary Finance-Operations Loop

**Multi-source payment reconciliation** across:

1. Payment records.
2. Settlement records.
3. Merchant ledger records.

---

## 3. Frozen Architecture

### 3.1 Architecture Principles

1. Deterministic financial rules are authoritative.
2. LLM output cannot directly alter canonical financial truth.
3. Every material decision must be explainable from stored evidence.
4. Every AI recommendation must be policy-gated.
5. Ground truth must never be exposed to inference logic.
6. Evaluation must be reproducible.
7. Every decision must be auditable.
8. Architecture changes require explicit approval and a new decision record.

### 3.2 System Layers

#### Layer A - Data Plane

- Synthetic data generator.
- Data schemas.
- Dataset versioning.
- Ground-truth generation.

#### Layer B - Ingestion

- CSV/JSON ingestion initially.
- Clear interfaces for future API connectors.
- Input validation.

#### Layer C - Normalization

Canonical representations for:

- IDs.
- Amounts.
- Currency.
- Timestamps.
- Statuses.
- References.

#### Layer D - Reconciliation Engine

Deterministic candidate matching and rule evaluation.

#### Layer E - Intelligence Layer

AI responsibilities:

- Investigate exceptions.
- Explain conflicting evidence.
- Classify exception type.
- Recommend a bounded action.

#### Layer F - Policy Engine

Allowed outcomes:

- `AUTO_RECONCILE`
- `REVIEW_REQUIRED`
- `UNRESOLVED`

#### Layer G - Audit

Append-only decision events with traceable evidence.

#### Layer H - Evaluation

Ground-truth comparison, metrics, benchmark execution, and reports.

#### Layer I - Presentation

Next.js dashboard for operations and judges.

---

## 4. Technology Stack

### Backend

- Python 3.12+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- Alembic
- PostgreSQL

### Data Processing

- Polars
- Python standard library where appropriate

### AI

- Provider/model abstraction.
- Structured outputs validated by Pydantic.
- Explicit agent/state orchestration.
- LangGraph is not required by default; it may be introduced only if a measured need exists.

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui

### Testing / Quality

- Pytest
- Integration tests
- Contract tests
- Property-based testing where useful
- Deterministic benchmark runner

### Infrastructure

- Docker
- Docker Compose for local orchestration

### Repository

- GitHub
- Conventional commits preferred.
- Pull requests for major changes where practical.

---

## 5. Repository Structure

```text
METFI/
|
+- AGENTS.md
+- ARCHITECTURE.md
+- PRODUCT_SPEC.md
+- EVALUATION_SPEC.md
+- TESTING.md
+- SECURITY.md
+- DECISIONS.md
+- CONTRIBUTING.md
+- README.md
|
+- backend/
|  +- app/
|  |  +- api/
|  |  +- core/
|  |  +- domain/
|  |  +- reconciliation/
|  |  +- intelligence/
|  |  +- policy/
|  |  +- audit/
|  |  +- evaluation/
|  |  +- services/
|  +- tests/
|  +- pyproject.toml
|  +- Dockerfile
|
+- frontend/
|  +- app/
|  +- components/
|  +- lib/
|  +- types/
|  +- package.json
|
+- data/
|  +- schemas/
|  +- generators/
|  +- fixtures/
|  +- ground_truth/
|
+- evaluation/
|  +- benchmarks/
|  +- metrics/
|  +- reports/
|
+- docs/
|  +- architecture/
|  +- demo/
|
+- scripts/
+- docker-compose.yml
```

---

## 6. Canonical Data Model

### 6.1 Payment Record

```text
payment_id
order_id
customer_id
amount
currency
status
payment_timestamp
metadata
```

### 6.2 Settlement Record

```text
settlement_id
payment_id
settled_amount
currency
settlement_timestamp
fee
fee_tax
status
metadata
```

### 6.3 Ledger Record

```text
ledger_id
order_id
debit
credit
currency
entry_timestamp
account
status
metadata
```

### 6.4 Canonical Reconciliation Case

```text
case_id
payment_id
order_id
payment_record
settlement_record
ledger_record
candidate_matches
rule_results
exception_type
canonical_status
ai_investigation
ai_recommendation
policy_decision
audited_at
```

---

## 7. Exception Taxonomy

METFI v1.0 must support at least:

1. `EXACT_MATCH`
2. `AMOUNT_MISMATCH`
3. `MISSING_SETTLEMENT`
4. `DUPLICATE_RECORD`
5. `DATE_MISMATCH`
6. `REFERENCE_MISMATCH`
7. `PARTIAL_SETTLEMENT`
8. `FEE_DISCREPANCY`
9. `CURRENCY_MISMATCH`
10. `AMBIGUOUS`

The taxonomy may be expanded, but existing labels may not be repurposed without updating the evaluation specification.

---

## 8. Deterministic Reconciliation Rules

The deterministic engine is the source of truth for canonical reconciliation state.

### Hard constraints

- Currency conflicts must never be treated as an exact match.
- Invalid identifiers cannot be accepted merely because amounts match.
- Duplicate records must be explicitly detected.
- A missing source record cannot become a match through an LLM explanation.
- Amount differences must be computed exactly, using decimal-safe arithmetic.

### Strong evidence

- Exact payment reference.
- Exact order ID.
- Exact currency.
- Expected settlement window.
- Exact amount.

### Candidate matching

The engine should first generate candidate relationships deterministically, then score/evaluate the evidence. AI may investigate ambiguous candidates but cannot invent records or links.

---

## 9. AI Responsibilities

### 9.1 Investigator

Input:

- Canonical case.
- Relevant source records.
- Deterministic rule results.
- Historical context if available and explicitly included.

Output:

- Exception classification.
- Explanation.
- Evidence references.
- Missing information.
- Confidence.

### 9.2 Resolver

Output only bounded recommendations:

- `AUTO_RECONCILE`
- `REVIEW_REQUIRED`
- `UNRESOLVED`

It must never directly mutate source records.

### 9.3 Verifier

The verifier challenges the AI conclusion against deterministic evidence and policy.

If there is a contradiction, the case must not be automatically resolved.

---

## 10. AI Output Contract

AI responses must be structured and validated.

Example:

```json
{
  "classification": "AMOUNT_MISMATCH",
  "explanation": "Settlement amount differs from payment amount by 150.00.",
  "evidence": [
    "payment reference matches",
    "currency matches",
    "settlement is inside the allowed window"
  ],
  "recommended_action": "REVIEW_REQUIRED",
  "confidence": 0.984
}
```

Rules:

- No unsupported claims.
- No hidden assumptions.
- No direct financial mutation.
- Evidence must map to actual record fields.
- Invalid structured output is treated as a failure, not silently repaired into truth.

---

## 11. Policy Engine

The policy engine is deterministic.

### AUTO_RECONCILE

Allowed only when all required hard constraints pass and no blocking exception exists.

### REVIEW_REQUIRED

Used for explainable discrepancies or cases that require human confirmation.

### UNRESOLVED

Used where evidence is insufficient, contradictory, or outside supported policy.

The AI can recommend, but the policy engine decides whether the recommendation is permitted.

---

## 12. Audit Model

Every reconciliation decision must produce an audit event containing at least:

```text
audit_id
case_id
timestamp
engine_version
policy_version
ai_model_identifier
input_record_references
deterministic_findings
ai_findings
final_decision
confidence
reason_code
```

Audit records must be append-only from the application perspective.

---

## 13. Synthetic Data Strategy

### Development Dataset

Target: 500 records.

### Stress Dataset

Target: 5,000 records initially; larger if practical after benchmarking.

### Controlled corruption classes

Approximate starting distribution:

- 65% exact matches.
- 10% amount mismatches.
- 6% missing settlements.
- 5% duplicates.
- 5% date mismatches.
- 4% reference mismatches.
- 3% partial settlements.
- 2% fee discrepancies.

The final distribution may be tuned after benchmark analysis, but the generator must be reproducible with a fixed random seed.

### Ground truth

Every synthetic case must retain hidden expected labels and, when applicable, the expected source relationship.

Ground truth must not flow into inference prompts or runtime decision-making.

---

## 14. Evaluation Specification

### Required headline metrics

- Reconciliation accuracy.
- Exception detection accuracy.
- Throughput.
- Unresolved exception count/rate.

### Additional metrics

- Precision.
- Recall.
- F1.
- False-match rate.
- False-unresolved rate.
- Auto-resolution rate.
- AI recommendation agreement with policy.
- Median and p95 processing latency.

### Evaluation integrity

- Separate benchmark input from ground truth.
- Use fixed seeds for reproducible datasets.
- Store benchmark version.
- Store software/version metadata.
- Do not hand-pick only successful examples.
- Do not report only the best run.
- Show failure classes explicitly.

---

## 15. Acceptance Targets

These are engineering targets, not claims. They must be measured on the actual implementation before publication.

### Functional

- 100% schema-valid ingestion for valid fixtures.
- Deterministic reconciliation passes all golden fixtures.
- No AI output can bypass policy gates.
- Audit record produced for every final decision.
- Evaluation run is reproducible.

### Quality

Target final benchmark:

- >= 95% reconciliation classification accuracy.
- >= 95% exception detection recall.
- 0 known hard-rule false matches on golden regression tests.
- 100% of unresolved cases explicitly surfaced.

If the achieved metrics are lower, the reported results must remain honest; targets must not be presented as measured results.

### Performance

Benchmark throughput on the final demo environment and publish the exact hardware/configuration. Avoid fabricated or environment-independent throughput claims.

---

## 16. Security and Safety Boundaries

METFI is a competition prototype, but financial safety boundaries still apply.

- No unrestricted model-controlled database writes.
- No secret exposure through prompts or logs.
- No raw credentials in source code.
- No production financial accounts required for the core demo.
- No destructive action without deterministic policy authorization.
- Secrets provided through environment configuration only.
- Audit logs must avoid unnecessary sensitive data.

---

## 17. API Boundary

Initial API surface should remain small.

Suggested endpoints:

```text
POST /api/v1/datasets/generate
POST /api/v1/reconciliation/run
GET  /api/v1/runs/{run_id}
GET  /api/v1/cases/{case_id}
GET  /api/v1/cases/{case_id}/audit
GET  /api/v1/metrics/{run_id}
GET  /api/v1/health
```

The UI should consume the API rather than embedding business logic.

---

## 18. Frontend Requirements

The dashboard must make the following immediately visible:

- Records processed.
- Reconciled count.
- Exception count.
- Accuracy.
- Throughput.
- Unresolved cases.
- Exception categories.
- Recent cases.

Case details must show:

- Source records side by side.
- Deterministic rule results.
- AI investigation.
- Evidence.
- Policy decision.
- Audit trail.

The UI is a demonstration surface for the actual engine, not a mock dashboard.

---

## 19. Development Phases

### Phase 0 - Governance

Create and validate:

- AGENTS.md
- ARCHITECTURE.md
- PRODUCT_SPEC.md
- EVALUATION_SPEC.md
- TESTING.md
- SECURITY.md
- DECISIONS.md

No feature work before Phase 0 is accepted.

### Phase 1 - Domain + Data

Build:

- schemas.
- synthetic generator.
- ground truth.
- database models.
- ingestion.
- normalization.

Exit criterion: deterministic fixtures pass.

### Phase 2 - Reconciliation Engine

Build and test deterministic matching and exception taxonomy.

Exit criterion: golden dataset has no known hard-rule false matches.

### Phase 3 - AI Investigation

Introduce structured AI investigation and verification.

Exit criterion: AI is unable to override deterministic truth.

### Phase 4 - Policy + Audit

Build bounded decisioning and audit trail.

Exit criterion: every final decision is explainable and auditable.

### Phase 5 - Evaluation

Build benchmark harness, metrics, stress tests, and reports.

Exit criterion: reproducible benchmark run.

### Phase 6 - Dashboard

Build operations dashboard and case investigation view.

Exit criterion: complete end-to-end demo from dataset run to case audit.

### Phase 7 - Hardening

Automated adversarial review is executed across all edge cases; fixes validated findings.

Exit criterion: no unresolved critical blockers and regression suite passes.

### Phase 8 - Demo / Submission

Prepare:

- final README.
- architecture diagram.
- benchmark results.
- failure/exception report.
- 5-minute demo flow.
- final screenshots.
- submission checklist.

---

## 20. System Operating Protocol

### Implementation Core

Role: Principal Execution Pipeline.

Must:

- Abide by all governance and financial invariants.
- Implement only within the frozen architecture.
- Run relevant tests after each meaningful change.
- Record significant decisions.
- Never silently change architectural boundaries.
- Never treat an LLM response as financial truth.

### Automated Adversarial Verifier

Role: Continuous Adversarial Inspection.

Must:

- Inspect code, schema invariants, and regression tests.
- Search for edge cases and failure modes.
- Challenge metrics and evaluation integrity.
- Validate cryptographic hash continuity and tamper safety.

---

## 21. Non-Negotiable Engineering Rules

1. Deterministic reconciliation must run without network access.
2. Ground truth must not be visible to the reconciliation engine.
3. Every exception must have an explicit reason code and classification.
4. AI components must never directly mutate financial records.
5. All money values must be exact Decimal or integer minor units.
6. The audit log must be tamper-evident.
7. Benchmarks must measure against synthetic ground truth.
8. Every decision must be reversible or quarantined.
9. No human approval may be bypassed without explicit policy rule.
10. The system must degrade gracefully under failure.

---

## 22. Definition of Done

METFI v1.0 is complete only when:

- End-to-end reconciliation works.
- Synthetic datasets are reproducible.
- Hidden ground truth is protected.
- Deterministic rules are tested.
- AI output is structured and validated.
- Policy gates are enforced.
- Every final case has an audit trail.
- Benchmark metrics are reproducible.
- Stress tests run successfully.
- UI demonstrates actual system state.
- Automated adversarial suite has no unresolved CRITICAL blockers.
- README and architecture documentation match the implementation.
- Demo can be executed from a clean environment using documented commands.

---

## 23. Demo Story

The final 5-minute demo should follow this order:

1. Problem: financial teams reconcile multiple sources manually.
2. Dataset: show a realistic batch with hundreds of records.
3. One-click run: execute the METFI controller.
4. Results: show throughput, accuracy, matched records, and exceptions.
5. Investigation: open a difficult exception.
6. Explainability: show source evidence + deterministic findings + AI reasoning.
7. Policy: show why the case was auto-resolved or escalated.
8. Audit: show the complete decision trail.
9. Evaluation: show measured benchmark results and honest unresolved cases.
10. Closing message: METFI provides an AI reasoning layer without surrendering financial control to an LLM.

---

## 24. Architectural Invariants

These must remain true throughout development:

1. Canonical financial truth is deterministic.
2. AI never directly mutates financial truth.
3. Ground truth is hidden during inference.
4. Policy gates all automated decisions.
5. Every final decision is auditable.
6. Evaluation is reproducible.
7. Exceptions are never silently discarded.
8. Model/provider changes do not require a rewrite of domain logic.
9. UI does not own business logic.
10. Architecture changes require an explicit decision record.

---

## 25. Initial ADRs

### ADR-001 - Deterministic Truth

Decision: deterministic reconciliation is authoritative; AI assists but cannot override it.

### ADR-002 - Bounded AI

Decision: AI outputs structured investigation/recommendation only and cannot perform unrestricted financial mutations.

### ADR-003 - Hidden Ground Truth

Decision: evaluation ground truth is generated and stored separately from inference data.

### ADR-004 - Reproducible Benchmarks

Decision: synthetic data generation uses explicit seeds and benchmark versions.

### ADR-005 - Provider Abstraction

Decision: AI integration is abstracted so evaluation and domain logic remain provider-independent.

### ADR-006 - Small Agent Surface

Decision: METFI uses a small number of logical AI roles instead of an unnecessary agent swarm.

### ADR-007 - Explicit Architecture Governance

Decision: architecture cannot drift silently; changes require an ADR and explicit approval.

---

## 26. Final Principle

METFI is not an LLM wrapped around spreadsheets.

It is a **measurable finance-control system with an AI reasoning layer**.

The engineering hierarchy is:

```text
Financial correctness
        >
Evaluation integrity
        >
Auditability
        >
Reliability
        >
Agentic sophistication
        >
Visual polish
```

Visual polish matters. Agentic sophistication matters. But neither is allowed to compromise the first four.

**END OF METFI MASTER SPECIFICATION v1.0**
