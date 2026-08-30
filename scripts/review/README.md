# METFI — Multi-Agent Adversarial Review System (Prime + Kilo Code)

The METFI repository utilizes a multi-agent adversarial code review framework combining:
1. **Prime (`prime-agent`)**: Powered by Nemotron 3 Ultra 550B inside WSL Ubuntu (**Primary Independent Certification Authority**).
2. **Kilo Code CLI (`@kilocode/cli`)**: Specialized review agents (`reviewer`, `debugger`, `tester`, `planner`, `orchestrator`) operating on Windows (**Secondary / Specialist / Fallback Reviewer**).

Antigravity operates in a strict pair-programming and review loop after every implementation phase:
```text
IMPLEMENT ➔ TEST ➔ PRIME REVIEW ➔ (OPTIONAL: KILO SPECIALIST) ➔ FIX ➔ PRIME RE-REVIEW ➔ HANDOFF
```

---

## 1. Authority Model & Conflict Rules

- **Primary Certification Authority:** Prime / Nemotron 3 Ultra 550B.
- **Authority Hierarchy:**
  - `Prime: BLOCKED` + `Kilo: PASS` ➔ **Final Status: BLOCKED**. (Kilo can never override a Prime block).
  - `Prime: PASS` + `Kilo: CRITICAL / BLOCK` ➔ **Final Status: CONFLICT** (Flagged for developer adjudication).
  - `Prime: PASS` + `Kilo: PASS` ➔ **Final Status: PASS** (Dual-agent certified).
  - **Infrastructure Failure Fallback:** If Prime fails due to infrastructure (`PRIME_TIMEOUT`, `PRIME_UNAVAILABLE`, `PRIME_EXECUTION_FAILURE`), Kilo executes as a secondary fallback. The final status is classified as **`FALLBACK_REVIEW`** (never disguised as a Prime certification).

---

## 2. Kilo Specialized Agent Roles

Kilo Code provides specialized roles adapted to METFI review phases:
- **`reviewer`** (Kilo `ask` agent): Architectural compliance, magic constant removal, contract generalization, and security checks.
- **`debugger`** (Kilo `debug` agent): Failure reproduction, root-cause isolation, and regression tracing.
- **`tester`** (Kilo `ask`/`debug` test evaluation): Test coverage validation, matrix combinations, and assertion depth.
- **`planner`** (Kilo `plan` agent): Read-only remediation planning and architecture suggestions.
- **`orchestrator`** (Kilo `orchestrator` agent): Coordinates multi-agent findings aggregation.

---

## 3. Usage & Command Reference

### Basic Usage
```powershell
# Auto Mode: Prime primary + Kilo fallback on infrastructure issues
python scripts/review/run_prime_review.py --phase 2 --verbose

# Run WSL Prime CLI exclusively
python scripts/review/run_prime_review.py --phase 2 --engine prime --verbose

# Run Kilo Reviewer Agent
python scripts/review/run_prime_review.py --phase 2 --engine kilo --kilo-agent reviewer --verbose

# Run Kilo Specialist Pipeline (Reviewer + Debugger + Tester)
python scripts/review/run_prime_review.py --phase 2 --engine kilo --kilo-pipeline --verbose

# Run Kilo capability discovery
python scripts/review/kilo_capabilities.py
```

### Supported CLI Flags
- `--phase`: Target implementation phase (`0`, `1`, `2`, `3`, `generic`).
- `--engine`: `auto` (default), `prime`, `kilo`, `direct`.
- `--kilo-agent`: `reviewer` (default), `debugger`, `tester`, `planner`, `orchestrator`.
- `--kilo-pipeline`: Run full multi-agent specialist pipeline for phase.
- `--kilo-model`: Custom AI model for Kilo CLI.
- `--timeout`: Execution timeout in seconds (default: `600`).
- `--distro`: WSL distribution hosting Prime (default: `Ubuntu`).
- `--thinking`: Prime reasoning level (`off`, `minimal`, `low`, `medium`, `high`, `max`).
- `--output-dir`: Custom directory for generated reports.

---

## 4. Exit Codes & Status Classifications

| Status Classification | Exit Code | Description |
|---|---|---|
| `PRIME_REVIEW_PASS` | `0` | Prime issued an unqualified PASS. |
| `FALLBACK_REVIEW` | `0` | Kilo secondary fallback passed when Prime was unavailable. |
| `PRIME_REVIEW_PASS_WITH_CONDITIONS` | `2` | Review passed with minor conditions to remediate. |
| `PRIME_REVIEW_BLOCKED` | `3` | Blocking findings or violations detected. |
| `PRIME_TIMEOUT` | `4` | Prime CLI timed out. |
| `PRIME_EXECUTION_FAILURE` | `5` | Infrastructure execution failure. |
| `REVIEW_CONFLICT` | `7` | Multi-agent disagreement flagged for adjudication. |

---

## 5. Review Artifact Output Format

All reports are saved under `docs/reviews/prime/`:
- `PHASE_<N>_PRIME_REVIEW_<timestamp>.md`
- `PHASE_<N>_KILO_REVIEW_<role>_<timestamp>.md`
- `PHASE_<N>_COMBINED_REVIEW_<timestamp>.md`
- `PHASE_<N>_FALLBACK_REVIEW_<role>_<timestamp>.md`

Every artifact preserves:
- Exact Git HEAD commit, branch, and working tree status
- Exact command line executed and exit code
- Verbatim captured stdout and stderr
- Structured findings and recommendations
