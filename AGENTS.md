# METFI Agent Operating Protocol & Governance

This document establishes the official operational rules, roles, safety boundaries, and collaboration protocols for AI and human contributors working on **METFI (Autonomous Finance Controller for Razorpay AI Buildathon, Track 04)**.

---

## 1. Primary Agent Roles & Responsibilities

### 1.1 Principal Implementation Agent
- **Identifier:** Antigravity IDE / Gemini 3.7 High (or designated builder harness)
- **Role:** Primary Architecture & Code Implementation
- **Mandate:**
  - Implement system layers strictly according to `METFI_MASTER_SPEC_v1.0.md` and approved architectural decisions (`DECISIONS.md`).
  - Maintain absolute separation between deterministic financial verification and AI reasoning.
  - Run all relevant automated tests (unit, integration, formatting, typing) before submitting any phase for review.
  - Record any new design decisions or required adjustments in `DECISIONS.md` using the ADR format.
  - Never silently modify frozen architectural boundaries or bypass deterministic policy gates.

### 1.2 Principal Adversarial Reviewer (Primary Authority)
- **Identifier:** Prime Agent / Nemotron 3 Ultra 550B (WSL/Ubuntu runtime)
- **Role:** Independent Quality, Correctness, and Security Auditor (Primary Certification Authority)
- **Mandate:**
  - Inspect codebase, test coverage, and benchmark outputs adversarially.
  - Attempt to falsify correctness, discover unhandled financial edge cases, and challenge evaluation integrity.
  - Verify that ground truth remains strictly isolated and is never leaked to inference prompts.
  - Issue structured review reports classified by severity.
  - Does not unilaterally rewrite architecture; proposes actionable findings backed by test cases and evidence.

### 1.3 Secondary & Specialist Reviewer (Specialist & Fallback Authority)
- **Identifier:** Kilo Code CLI (`@kilocode/cli` with specialized agents)
- **Role:** Secondary Adversarial Reviewer, Root-Cause Debugger, Test Validator, and Fallback Reviewer
- **Specialized Roles:**
  - **Reviewer (`ask`):** Evaluates contracts, magic constant removal, domain rules, and security.
  - **Debugger (`debug`):** Investigates failure modes, traces edge-case regressions, and isolates bugs.
  - **Tester (`tester`):** Assesses test coverage, boundary conditions, and matrix combinations.
  - **Planner (`plan`):** Generates non-destructive remediation proposals.
  - **Orchestrator (`orchestrator`):** Coordinates multi-agent findings aggregation.
- **Authority Constraints:**
  - Kilo can **NEVER** override a Prime `BLOCKED` status.
  - If Prime infrastructure fails (`TIMEOUT`, `UNAVAILABLE`, `EXECUTION_FAILURE`), Kilo executes as a secondary fallback with status `FALLBACK_REVIEW`.
  - Conflicts between Prime and Kilo are surfaced for developer adjudication.

---

## 2. Review Severity Levels & Action Gates

When PRs or Phase handoffs are submitted, findings are triaged into four severity tiers:

| Severity | Definition | Resolution Gate |
|---|---|---|
| **CRITICAL** | Violates deterministic financial correctness, leaks ground truth, allows un-gated financial mutations, or invalidates benchmark reproducibility. | **BLOCKING**: Must be resolved and verified before advancing to the next phase or merging code. |
| **HIGH** | Significant business logic flaw, unhandled edge cases in reconciliation taxonomy, security exposure, or major test suite deficiency. | **BLOCKING**: Must be addressed before phase sign-off. |
| **MEDIUM** | Performance bottleneck, code smell, incomplete error message, or missing non-critical validation. | Non-blocking for current phase if documented as technical debt in handoff. |
| **LOW** | Minor style discrepancies, documentation formatting, or polish suggestions. | Non-blocking. |

---

## 3. Core Operating Invariants (Non-Negotiables)

Every agent operating in this repository must enforce these 10 non-negotiable invariants:

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

## 4. Phase Transition & Multi-Agent Review Protocol

Every implementation phase must strictly follow the automated review cycle:

```text
       IMPLEMENT
           │
           ▼
       RUN TESTS (pytest, ruff, mypy, build)
           │
           ▼
    RUN REVIEW (`python scripts/review/run_prime_review.py --phase <N>`)
           │
           ├──────────────────────────────┬─────────────────────────────┐
           ▼                              ▼                             ▼
       [BLOCKED]                [PASS WITH CONDITIONS]                [PASS]
           │                              │                             │
           ▼                              ▼                             ▼
       Remediate                    Evaluate Conditions           Compile Handoff
           │                              │                             │
       Re-run Tests                       ▼                             ▼
           │                        Fix Conditions                    STOP
           │                              │                             │
           └──────────────────────────────┴─────────────────────────────┘
                                          │
                                          ▼
                                  Re-run Review
```

### Review Rules & Invariants:
1. **Active Working Tree:** Reviewers inspect the current working tree directly (`C:\Users\Samrat\OneDrive\Documents\Samrat-ai\METFI` and WSL mount). Do not clone a second repository or pull a fresh branch.
2. **Execution Commands:**
   ```bash
   # Prime primary + Kilo fallback
   python scripts/review/run_prime_review.py --phase <N> --verbose

   # Kilo specialist pipeline
   python scripts/review/run_prime_review.py --phase <N> --engine kilo --kilo-pipeline --verbose
   ```
3. **Artifact Persistence:** Every review generates an immutable, timestamped markdown report in `docs/reviews/prime/`.
4. **Builder Report:** When findings exist, Antigravity classifies them into `FIX`, `ACCEPT AS RISK`, or `REQUEST CLARIFICATION`. No phase can be closed with unresolved `CRITICAL` or `HIGH` findings.
5. **Phase Guard:** Antigravity must STOP after completing a phase and waiting for sign-off. Never automatically begin the next phase.

---

## 5. Development Phases Roadmap

- **Phase 0:** Governance, Repository Initialization, Base Environment, Health Smoke Test
- **Phase 1:** Domain Model, Normalization, Synthetic Data Generator & Ground Truth
- **Phase 2:** Deterministic Reconciliation Engine & Golden Fixture Validation
- **Phase 3:** AI Investigation Layer, Structured Reasoning & Verifier
- **Phase 4:** Policy Engine, Bounded Decisioning & Audit Trail
- **Phase 5:** Evaluation Engine, Metrics Harness & Stress Testing
- **Phase 6:** Next.js Operations Dashboard & Interactive Case Inspector
- **Phase 7:** Adversarial Hardening & Final Prime Security/Correctness Audit
- **Phase 8:** Demo Package, Benchmark Publication & Submission Assets
