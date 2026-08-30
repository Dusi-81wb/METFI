# METFI ADVERSARIAL PHASE REVIEW SYSTEM — HANDOFF SPECIFICATION

## 1. Executive Summary

The **METFI Adversarial Phase Review System** provides an automated, multi-engine adversarial auditing framework designed to review the active working tree in place after each implementation phase. It connects Windows developer workflows and Antigravity pair programming to adversarial review engines—including the **WSL Prime CLI (`prime-agent`)** powered by Nemotron 3 Ultra 550B, and the **Kilo Code Agent / Deterministic Adversarial Evaluation Engine**.

### Core Architecture Principles
1. **In-Place Working Tree Inspection:** Operates directly on the current working directory. Does NOT clone the repository, pull fresh GitHub branches, or create isolated worktrees.
2. **Multi-Engine Dispatching:**
   - `--engine prime`: Invokes WSL Ubuntu `prime-agent` with Nemotron 3 Ultra 550B.
   - `--engine kilo`: Executes the Kilo Code Agent / Deterministic Adversarial Evaluation Engine.
   - `--engine auto` (Default): Automatically coordinates Prime CLI with intelligent fallback.
3. **Strict Data Boundary Security:** All files in the repository (source code, tests, fixtures, comments, markdown specs) are treated as UNTRUSTED DATA. Prompts enforce prompt-injection defense boundaries.
4. **Structured Verdict & Exit Code Contract:** Verdicts determine downstream CI and workflow behavior (`PASS` = 0, `PASS_WITH_CONDITIONS` = 2, `BLOCKED` = 3, `TIMEOUT` = 4, `EXECUTION_FAILURE` = 5).
5. **Canonical Artifact Generation:** Every execution writes an immutable, timestamped markdown report to `docs/reviews/prime/PHASE_<PHASE>_REVIEW_<TIMESTAMP>.md`.

---

## 2. Review Protocol Lifecycle

Every development phase follows this mandatory cycle:

```
┌─────────────────┐     ┌───────────────┐     ┌──────────────────────┐
│   IMPLEMENT     │ ──> │     TEST      │ ──> │ ADVERSARIAL REVIEW   │
│ (Feature Code)  │     │ (Pytest/Ruff) │     │ (Prime / Kilo Engine)│
└─────────────────┘     └───────────────┘     └──────────┬───────────┘
                                                         │
                        ┌───────────────┐                │
                        │      FIX      │ <── BLOCKED ───┤
                        │ (Remediate)   │                │
                        └───────┬───────┘                │
                                │                        │
                                v                        v
                        ┌───────────────┐     ┌──────────────────────┐
                        │   RE-REVIEW   │     │       HANDOFF        │
                        │ (Verification)│     │  (Commit & Proceed)  │
                        └───────────────┘     └──────────────────────┘
```

---

## 3. CLI Usage & Execution Flags

### Basic Invocation
```powershell
# Review Phase 2 using auto-dispatch
python scripts/review/run_prime_review.py --phase 2 --verbose

# Review using Kilo Code Agent / Deterministic Adversarial Engine
python scripts/review/run_prime_review.py --phase 2 --engine kilo --verbose

# Review using WSL Prime CLI directly
python scripts/review/run_prime_review.py --phase 2 --engine prime --timeout 600 --verbose
```

### Supported Arguments

| Flag | Type | Default | Description |
|---|---|---|---|
| `--phase` | `str` | *Required* | Phase identifier (`0`, `1`, `2`, `3`, `generic`). |
| `--engine` | `str` | `auto` | Engine selection: `auto`, `prime`, `kilo`, `direct`. |
| `--distro` | `str` | `Ubuntu` | WSL distribution hosting Prime binary. |
| `--prime-path`| `str` | `None` | Custom path to Prime CLI inside WSL (optional). |
| `--timeout` | `int` | `600` | Review timeout in seconds. |
| `--thinking`| `str` | `off` | Prime reasoning level (`off`, `minimal`, `low`, `medium`, `high`, `max`). |
| `--output-dir`| `str` | `docs/reviews/prime/` | Destination directory for markdown reports. |
| `--verbose` | `flag`| `False` | Enable detailed execution logging. |

---

## 4. Exit Code Contract

Review scripts follow this standard exit code specification:

| Verdict / Status | Enum Constant | Exit Code | Workflow Action |
|---|---|---|---|
| **PASS** | `ReviewStatus.PASS` | `0` | Phase verified. Proceed to handoff. |
| **PASS WITH CONDITIONS** | `ReviewStatus.PASS_WITH_CONDITIONS` | `2` | Review passed with minor non-blocking items. Fix and re-verify. |
| **BLOCKED** | `ReviewStatus.BLOCKED` | `3` | Critical finding or heuristic violation. Remediate before proceeding. |
| **TIMEOUT** | `ReviewStatus.TIMEOUT` | `4` | Execution exceeded timeout threshold. |
| **EXECUTION FAILURE** | `ReviewStatus.EXECUTION_FAILURE` | `5` | Infrastructure, WSL, or runner error. |

---

## 5. Artifact Output Format

All review artifacts are saved to `docs/reviews/prime/` with the filename schema:
`PHASE_<PHASE>_REVIEW_<YYYYMMDD_HHMMSS>.md`

### Canonical Artifact Structure
```markdown
# PRIME REVIEW

Phase: <phase>
Timestamp: <ISO-8601 UTC>
Repository: METFI
Windows Path: <Windows path>
WSL Path: <WSL path>
Git HEAD: <commit hash>
Git Branch: <branch name>
Prime Command: <command string>
Prime Exit Code: <exit code>
Verdict: <Verdict> (<Status Enum>)
Duration: <seconds>s

## WORKING TREE STATUS AT REVIEW TIME
<git status output>

---

## PRIME OUTPUT
# METFI PHASE <N> ADVERSARIAL REVIEW

## Executive Verdict
**Status: PASS**
**Confidence: 95%**

## Finding Verification Matrix
| Finding | Status | Evidence |
|---|---|---|
| ... | ... | ... |

## Magic Constant & Domain Rule Audit
| Constant / Heuristic | Location | Classification | Status |
|---|---|---|---|
| ... | ... | ... | ... |

## Verification Suite Execution
- Independent Tests: ✅ 100% PASS
- Lint Quality: ✅ PASS
```

---

## 6. Verification & Validation Evidence

### 1. Test Suite Verification
```text
============================= test session starts =============================
platform win32 -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Samrat\OneDrive\Documents\Samrat-ai\METFI\backend
collected 204 items

tests\integration\test_dataset_generation_pipeline.py .                  [  0%]
tests\integration\test_db_persistence.py ..                              [  1%]
tests\integration\test_reconciliation_pipeline.py ...                    [  2%]
tests\test_health.py ...                                                 [  4%]
tests\test_smoke_live.py .                                               [  4%]
tests\unit\test_candidate_matcher.py .....                               [  7%]
tests\unit\test_candidate_matcher_safety.py ..                           [  8%]
tests\unit\test_classification_precedence.py .....                       [ 10%]
tests\unit\test_config.py ...                                            [ 12%]
tests\unit\test_corruption.py ............                               [ 18%]
tests\unit\test_evaluation_metrics.py ..                                 [ 19%]
tests\unit\test_evidence_extractor.py ..                                 [ 20%]
tests\unit\test_fee_tax_matrix.py ...................................... [ 38%]
............                                                             [ 44%]
tests\unit\test_generator.py ...                                         [ 46%]
tests\unit\test_generator_independent.py ....                            [ 48%]
tests\unit\test_ground_truth_isolation.py .......                        [ 51%]
tests\unit\test_intelligence_provider.py ....                            [ 53%]
tests\unit\test_invariants.py .                                          [ 53%]
tests\unit\test_money.py .......                                         [ 57%]
tests\unit\test_normalizer.py ....                                       [ 59%]
tests\unit\test_partial_and_ambiguity_generalization.py ............     [ 65%]
tests\unit\test_policy_engine.py ....                                    [ 67%]
tests\unit\test_prime_review_runner.py .....................             [ 77%]
tests\unit\test_reconciliation_engine.py ..........                      [ 82%]
tests\unit\test_schemas.py ....                                          [ 84%]
tests\unit\test_security_sanitization.py ..........................      [ 97%]
tests\unit\test_time.py ......                                           [100%]

============================= 204 passed in 8.37s =============================
```

### 2. Static Typing Verification
```text
$ uv run mypy app
Success: no issues found in 40 source files
```

### 3. Linting Verification
```text
$ uv run ruff check .
All checks passed!
```

### 4. Live Review Artifact Generated
- Artifact Path: `docs/reviews/prime/PHASE_2_REVIEW_20260830_140458.md`
- Status: `PASS`
- Exit Code: `0`
- Duration: `4.09s`
