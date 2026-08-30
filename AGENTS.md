# METFI System Agents & Operating Governance

This document establishes the operational rules, roles, safety boundaries, and collaboration protocols for **METFI (Autonomous Finance Controller for Razorpay AI Buildathon, Track 04)**.

---

## 1. METFI Core Intelligence Subsystem Roles

METFI operates a multi-stage, evidence-grounded reconciliation architecture where deterministic rules define financial truth and AI provides structured root-cause investigation.

```
+-----------------------------------------------------------------------------------+
|                        INFERENCE EXECUTION PIPELINE ARCHITECTURE                  |
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
|                                                        [Deterministic Policy]     |
|                                                                   |               |
|                                                                   v               |
|                                                            [Audit Trail]          |
+-----------------------------------------------------------------------------------+
```

### 1.1 Deterministic Reconciliation Engine
- **Role:** Canonical Financial Truth Authority
- **Responsibilities:**
  - Evaluates normalized payment and settlement pairs across monetary, currency, timing, and reference dimensions.
  - Classifies records into canonical exception classes (`EXACT_MATCH`, `AMOUNT_MISMATCH`, `CURRENCY_MISMATCH`, `DUPLICATE_RECORD`, etc.).
  - Calculates exact fee, tax, and settlement variances using deterministic formulas.
  - **Primacy Invariant:** Deterministic classification is immutable and cannot be overridden by AI opinions.

### 1.2 AI Context Builder (Security Boundary)
- **Role:** Safe Context Assembly & Ground-Truth Isolation
- **Responsibilities:**
  - Extracts minimized, relevant financial facts into structured prompt context.
  - Sanitizes untrusted text and descriptions against prompt injection attacks.
  - Generates verifiable citation whitelists (`[VALID CITATION FIELD PATHS]`).
  - Strict zero-access isolation: Never exposes ground truth labels, corruption classes, or benchmark metadata.

### 1.3 AI Investigator Agent
- **Role:** Evidence-Grounded Exception Root Cause Analysis
- **Responsibilities:**
  - Analyzes reconciliation discrepancies using a standard 12-class taxonomy.
  - Generates clear, non-technical primary and alternative explanations.
  - Cites specific field-level evidence references against the context whitelist.
  - Emits bounded operational recommendations (`AUTO_RECONCILE`, `REVIEW_REQUIRED`, `UNRESOLVED`).

### 1.4 AI Verifier Agent
- **Role:** Independent Controller & Audit Gate
- **Responsibilities:**
  - Audits AI investigation results against deterministic facts and context.
  - Enforces hard deterministic gates rejecting hallucinated citations, truth contradictions, and unsafe recommendations.
  - Emits structured `VerificationResult` (`VERIFIED`, `REJECTED`, `INSUFFICIENT_EVIDENCE`).

### 1.5 Deterministic Policy Engine
- **Role:** Automated Decision & Action Gatekeeper
- **Responsibilities:**
  - Evaluates verified investigation results against contract risk rules and variance tolerances.
  - Authorizes bounded actions (`AUTO_RECONCILE`, `FLAG_MANUAL_REVIEW`, `ROUTE_TO_OPS`).
  - Emits append-only immutable audit events for complete compliance.

---

## 2. Core Operating Invariants (Non-Negotiables)

Every component operating in this repository must enforce these 10 non-negotiable invariants:

1. **Deterministic Truth Primacy:** Deterministic financial rules own the canonical reconciliation truth. LLM inferences cannot override mathematical or transactional facts.
2. **Bounded AI Capability:** AI agents can only investigate, explain, categorize, and recommend bounded actions (`AUTO_RECONCILE`, `REVIEW_REQUIRED`, `UNRESOLVED`). They cannot directly mutate source databases or ledger states.
3. **Hidden Ground Truth:** Ground truth datasets must never be accessible to inference prompts or runtime decision agents.
4. **Policy Enforcement Gate:** Every AI recommendation must be evaluated and authorized by the deterministic Policy Engine.
5. **Immutable Audit Trail:** Every final decision and reconciliation attempt must emit an append-only audit event containing complete evidence references.
6. **Reproducible Evaluation:** All benchmarks and synthetic data generators must accept deterministic random seeds and produce reproducible metric outputs.
7. **No Silent Error Swallowing:** All exceptions, mismatches, and data corruptions must be surfaced explicitly.
8. **Decoupled Model Layer:** AI provider integrations must be abstracted behind structured interfaces so that LLM providers can be swapped without touching core financial logic.
9. **Zero Business Logic in UI:** The frontend is strictly an operational and presentation layer querying FastAPI endpoints.
10. **Architecture Freeze:** No new frameworks, multi-agent swarms, or alternative databases may be introduced without an approved Architecture Decision Record (`DECISIONS.md`).

---

## 3. Severity Levels & Quality Gates

When changes are submitted, issues are triaged into four severity tiers:

| Severity | Definition | Resolution Gate |
|---|---|---|
| **CRITICAL** | Violates deterministic financial correctness, leaks ground truth, allows un-gated financial mutations, or invalidates benchmark reproducibility. | **BLOCKING**: Must be resolved before merging code. |
| **HIGH** | Significant business logic flaw, unhandled edge cases in reconciliation taxonomy, security exposure, or major test suite deficiency. | **BLOCKING**: Must be addressed before sign-off. |
| **MEDIUM** | Performance bottleneck, code smell, incomplete error message, or missing non-critical validation. | Non-blocking if documented as technical debt. |
| **LOW** | Minor style discrepancies, documentation formatting, or polish suggestions. | Non-blocking. |

---

## 4. Development Phases Roadmap

- **Phase 0:** Governance, Repository Initialization, Base Environment, Health Smoke Test
- **Phase 1:** Domain Model, Normalization, Synthetic Data Generator & Ground Truth
- **Phase 2:** Deterministic Reconciliation Engine & Golden Fixture Validation
- **Phase 3:** AI Investigation Layer, Structured Reasoning & Verifier
- **Phase 4:** Policy Engine, Bounded Decisioning & Audit Trail
- **Phase 5:** Evaluation Engine, Metrics Harness & Stress Testing
- **Phase 6:** Next.js Operations Dashboard & Interactive Case Inspector
- **Phase 7:** Adversarial Hardening & Security/Correctness Audit
- **Phase 8:** Demo Package, Benchmark Publication & Submission Assets
