# METFI KILO CODE & PRIME ADVERSARIAL REVIEW SYSTEM — HANDOFF SPECIFICATION

## 1. Executive Summary

The METFI review infrastructure has been upgraded to a **Multi-Agent Adversarial Review Pipeline** uniting two complementary auditing engines:
1. **Prime (`prime-agent`)**: Powered by Nemotron 3 Ultra 550B inside WSL Ubuntu (**Primary Independent Certification Authority**).
2. **Kilo Code CLI (`@kilocode/cli`)**: Specialized AI review agents operating natively on Windows (**Secondary / Specialist / Fallback Reviewer**).

Both engines operate against the **CURRENT WORKING TREE IN PLACE** (`C:\Users\Samrat\OneDrive\Documents\Samrat-ai\METFI`). The review process does NOT re-clone the repository, switch branches, create secondary worktrees, or permit destructive write operations during certification audits.

---

## 2. Discovered Kilo CLI Capabilities

### 2.1 Installation & Binary Discovery
- **Installed Package:** `@kilocode/cli` (Version: `7.5.6`)
- **Executable Path:** `C:\Users\Samrat\AppData\Roaming\npm\kilo.CMD`
- **Supported Global Commands:** `kilo run`, `kilo agent`, `kilo models`, `kilo auth`, `kilo config`
- **Configuration & Auth Path:** `~\.local\share\kilo\auth.json`

### 2.2 Discovered Native Agents & Permissions
Capability discovery via `scripts/review/kilo_capabilities.py` probed Kilo 7.5.6:

| Native Kilo Agent | Discovered Type | Default Permission Policy | METFI Role Mapping |
|---|---|---|---|
| `ask` | Primary Agent | Read-Only (edit/write/interactive denied; cat/ls/grep/git-show allowed) | **`reviewer`**, **`tester`** |
| `debug` | Primary Agent | Investigation & Root-Cause tracing | **`debugger`** |
| `plan` | Primary Agent | Non-destructive planning (edit denied except plan files) | **`planner`** |
| `orchestrator` | Primary Agent | Multi-step task coordination | **`orchestrator`** |
| `code` | Primary Agent | Active modification (not used in read-only reviews) | — |
| `summary` | Primary Agent | Read-Only summarization | — |
| `title` | Primary Agent | Read-Only session title generation | — |
| `compaction` | Primary Agent | Context optimization | — |

---

## 3. Authority Model & Governance Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                      METFI REVIEW RUNNER                     │
│               (scripts/review/run_prime_review.py)          │
└──────────────────────────────┬──────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
    ┌──────────────────────┐        ┌──────────────────────┐
    │     PRIME AGENT      │        │      KILO CODE       │
    │  (Primary Authority) │        │(Secondary/Specialist)│
    │ Nemotron 3 Ultra 550B│        │   @kilocode/cli      │
    └──────────┬───────────┘        └──────────┬───────────┘
               │                               │
               ▼                               ▼
    ┌─────────────────────────────────────────────────────────┐
    │                     AUTHORITY MATRIX                    │
    ├─────────────────────────────────────────────────────────┤
    │ Prime = PASS  + Kilo = PASS       ➔ PASS (Certified)   │
    │ Prime = BLOCK + Kilo = PASS       ➔ BLOCKED (No Overr.)│
    │ Prime = PASS  + Kilo = CRITICAL   ➔ CONFLICT (Adjudic.)│
    │ Prime = INFR. FAIL + Kilo = PASS  ➔ FALLBACK_REVIEW    │
    └─────────────────────────────────────────────────────────┘
```

### Core Hierarchy Rules:
1. **Prime Authority Primacy:** Prime is the primary independent certification auditor.
2. **Override Prohibition:** A Kilo PASS can **NEVER** override a Prime BLOCKED verdict.
3. **Conflict Flagging:** If Prime passes a phase but a Kilo specialist discovers a `CRITICAL` or `BLOCKED` issue, the status is flagged as `REVIEW_CONFLICT` (Exit code 7) for developer investigation.
4. **Fallback Identification:** If Prime suffers an infrastructure outage (`TIMEOUT`, `UNAVAILABLE`, `EXECUTION_FAILURE`), Kilo executes as a secondary fallback. The artifact is explicitly titled `PHASE_<N>_FALLBACK_REVIEW_<role>_<timestamp>.md` and its status is recorded as `FALLBACK_REVIEW` (never disguised as Prime certification).

---

## 4. Architecture & Component Reference

### 4.1 Capability Discovery Module ([`scripts/review/kilo_capabilities.py`](file:///c:/Users/Samrat/OneDrive/Documents/Samrat-ai/METFI/scripts/review/kilo_capabilities.py))
- Discovers `kilo` binary across Windows and WSL.
- Parses installed agent list and security boundaries.
- Exposes `resolve_kilo_agent(role)` and `get_phase_recommended_agents(phase)`.

### 4.2 Kilo Execution & Pipeline Runner ([`scripts/review/kilo_runner.py`](file:///c:/Users/Samrat/OneDrive/Documents/Samrat-ai/METFI/scripts/review/kilo_runner.py))
- Runs single specialized agents (`run_single_kilo_agent`).
- Runs multi-agent specialist pipelines (`run_kilo_pipeline`).
- Normalizes findings into `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`.
- Formats individual and combined review artifacts.

### 4.3 Master Review Orchestrator ([`scripts/review/run_prime_review.py`](file:///c:/Users/Samrat/OneDrive/Documents/Samrat-ai/METFI/scripts/review/run_prime_review.py))
- Bridges Windows Antigravity workspace to WSL Prime and Windows Kilo.
- Enforces the complete Authority Hierarchy and exit code specifications.

---

## 5. CLI Usage & Execution Examples

```powershell
# 1. Capability Discovery
python scripts/review/kilo_capabilities.py

# 2. Auto Mode (Prime primary with Kilo fallback)
python scripts/review/run_prime_review.py --phase 2 --verbose

# 3. Direct Kilo Reviewer Agent
python scripts/review/run_prime_review.py --phase 2 --engine kilo --kilo-agent reviewer --verbose

# 4. Direct Kilo Debugger Agent
python scripts/review/run_prime_review.py --phase 2 --engine kilo --kilo-agent debugger --verbose

# 5. Full Kilo Multi-Agent Specialist Pipeline
python scripts/review/run_prime_review.py --phase 2 --engine kilo --kilo-pipeline --verbose

# 6. WSL Prime CLI Exclusively
python scripts/review/run_prime_review.py --phase 2 --engine prime --verbose
```

---

## 6. Exit Code Contract

| Status Classification | Enum Constant | Exit Code | Action |
|---|---|---|---|
| **PASS** | `ReviewStatus.PASS` | `0` | Phase dual-certified. Ready for handoff. |
| **FALLBACK_REVIEW** | `ReviewStatus.FALLBACK_REVIEW` | `0` | Secondary fallback passed. Primary re-verification required prior to release. |
| **PASS WITH CONDITIONS** | `ReviewStatus.PASS_WITH_CONDITIONS` | `2` | Non-blocking conditions to remediate. |
| **BLOCKED** | `ReviewStatus.BLOCKED` | `3` | Blocking findings detected. Remediate and re-review. |
| **TIMEOUT** | `ReviewStatus.TIMEOUT` | `4` | Runner process timed out. |
| **EXECUTION FAILURE** | `ReviewStatus.EXECUTION_FAILURE` | `5` | CLI or environment execution error. |
| **CONFLICT** | `ReviewStatus.CONFLICT` | `7` | Disagreement between reviewers flagged for user adjudication. |

---

## 7. Verification & Test Evidence

### 7.1 Unit & Orchestration Test Suite
```text
============================= test session starts =============================
platform win32 -- Python 3.12.13, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\Samrat\OneDrive\Documents\Samrat-ai\METFI\backend
collected 206 items

tests\integration\test_dataset_generation_pipeline.py .                  [  0%]
tests\integration\test_db_persistence.py ..                              [  1%]
tests\integration\test_reconciliation_pipeline.py ...                    [  2%]
tests\test_health.py ...                                                 [  4%]
tests\test_smoke_live.py .                                               [  4%]
tests\unit\test_candidate_matcher.py .....                               [  7%]
tests\unit\test_candidate_matcher_safety.py ..                           [  8%]
tests\unit\test_classification_precedence.py .....                       [ 10%]
tests\unit\test_config.py ...                                            [ 12%]
tests\unit\test_corruption.py ............                               [ 17%]
tests\unit\test_evaluation_metrics.py ..                                 [ 18%]
tests\unit\test_evidence_extractor.py ..                                 [ 19%]
tests\unit\test_fee_tax_matrix.py ...................................... [ 38%]
............                                                             [ 44%]
tests\unit\test_generator.py ...                                         [ 45%]
tests\unit\test_generator_independent.py ....                            [ 47%]
tests\unit\test_ground_truth_isolation.py .......                        [ 50%]
tests\unit\test_intelligence_provider.py ....                            [ 52%]
tests\unit\test_invariants.py .                                          [ 53%]
tests\unit\test_money.py .......                                         [ 56%]
tests\unit\test_normalizer.py ....                                       [ 58%]
tests\unit\test_partial_and_ambiguity_generalization.py ............     [ 64%]
tests\unit\test_policy_engine.py ....                                    [ 66%]
tests\unit\test_prime_review_runner.py .......................           [ 77%]
tests\unit\test_reconciliation_engine.py ..........                      [ 82%]
tests\unit\test_schemas.py ....                                          [ 84%]
tests\unit\test_security_sanitization.py ..........................      [ 97%]
tests\unit\test_time.py ......                                           [100%]

============================= 206 passed in 5.57s =============================
```

### 7.2 Static Quality Verification
```text
$ uv run mypy app
Success: no issues found in 40 source files

$ uv run ruff check .
All checks passed!
```

---

## 8. Known Limitations & Operating Notes

1. **Remote LLM Endpoint Latencies:** Remote API endpoints (such as NVIDIA NIM or external provider APIs) may experience intermittent queue latency. The review runner's configurable `--timeout` flag (default 600s) and `--engine auto` fallback mitigate hanging processes.
2. **Read-Only Invariant:** Both Prime and Kilo Code review agents operate strictly in read-only mode during review passes. Code remediation is exclusively implemented by Antigravity under developer direction.
3. **No Automatic Phase Advance:** The review system generates actionable markdown artifacts and exit codes. It never automatically initiates the next implementation phase.
