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

### 1.2 Principal Adversarial Reviewer
- **Identifier:** Prime Agent / Nemotron 3 Ultra 550B (WSL/Ubuntu runtime)
- **Role:** Independent Quality, Correctness, and Security Auditor
- **Mandate:**
  - Inspect codebase, test coverage, and benchmark outputs adversarially.
  - Attempt to falsify correctness, discover unhandled financial edge cases, and challenge evaluation integrity.
  - Verify that ground truth remains strictly isolated and is never leaked to inference prompts.
  - Issue structured review reports classified by severity.
  - Does not unilaterally rewrite architecture; proposes actionable findings backed by test cases and evidence.

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

## 4. Phase Transition & Prime-Powered Review Protocol

Every implementation phase must strictly follow the automated Prime review cycle:

```text
       IMPLEMENT
           │
           ▼
       RUN TESTS (pytest, ruff, mypy, build)
           │
           ▼
    RUN PRIME REVIEW (`python scripts/review/run_prime_review.py --phase <N>`)
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
                                  Re-run Prime Review
```

### Review Rules & Invariants:
1. **Active Working Tree:** Prime reviews the current working tree directly (`/mnt/c/Users/Samrat/OneDrive/Documents/Samrat-ai/METFI`). Do not clone a second repository or pull a fresh branch.
2. **Review Command:**
   ```bash
   python scripts/review/run_prime_review.py --phase <PHASE_NUMBER> --verbose
   ```
3. **Artifact Persistence:** Every review generates an immutable, timestamped markdown report in `docs/reviews/prime/PHASE_<N>_REVIEW_<TIMESTAMP>.md`. Previous reviews are never overwritten.
4. **Builder Report:** When findings exist, Antigravity classifies them into `FIX`, `ACCEPT AS RISK`, or `REQUEST CLARIFICATION`. No phase can be closed with unresolved `CRITICAL` or `HIGH` findings.
5. **Phase Guard:** Antigravity must STOP after completing a phase and waiting for Prime's sign-off. Never automatically begin the next phase.

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
