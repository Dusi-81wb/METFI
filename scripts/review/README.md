# METFI — Prime-Powered Phase Review System

The METFI repository utilizes **Prime** (`prime-agent` powered by Nemotron 3 Ultra 550B, installed inside WSL Ubuntu) as the authoritative, adversarial code review engine.

Antigravity operates in a strict pair-programming and review loop after every implementation phase:
```text
IMPLEMENT ➔ TEST ➔ PRIME REVIEW ➔ FIX ➔ PRIME RE-REVIEW ➔ HANDOFF
```

---

## 1. Core Principles

1. **Active Working Tree Audit:** Prime inspects the current working directory in place (`/mnt/c/Users/Samrat/OneDrive/Documents/Samrat-ai/METFI`). It reviews uncommitted, staged, and untracked files without cloning, pulling from GitHub, or creating secondary working trees.
2. **Real Prime Execution:** The Python runner acts strictly as an orchestration wrapper. The actual code review, reasoning, and adversarial audit are performed by Prime inside WSL Ubuntu.
3. **Data Boundary Defense:** Repository files, transaction records, comments, and test fixtures are treated as untrusted data. Prompt injection defenses ensure embedded instructions cannot override Prime's audit protocol.
4. **Verbatim Traceability:** Every review run produces an immutable, timestamped markdown report in `docs/reviews/prime/` capturing verbatim stdout, stderr, execution metadata, and parsed verdicts.

---

## 2. Prerequisites & Environment

- **Host OS:** Windows 11 / 10
- **WSL Distribution:** Ubuntu (WSL 2)
- **Prime CLI:** `prime-agent` v0.8.1+ installed in WSL (`/home/samrat/.npm-global/bin/prime-agent`)
- **Model / Provider:** `nvidia/nemotron-3-ultra-550b-a55b` configured via `~/.prime/agent/`

---

## 3. Usage & Command Reference

### Basic Usage
```bash
# Review a specific phase (e.g. Phase 2)
python scripts/review/run_prime_review.py --phase 2

# Verbose mode with progress output
python scripts/review/run_prime_review.py --phase 2 --verbose

# Custom execution timeout
python scripts/review/run_prime_review.py --phase 2 --timeout 600

# Custom WSL distribution or Prime binary override
python scripts/review/run_prime_review.py --phase 2 --distro Ubuntu --prime-path /custom/path/prime-agent
```

### Available Phases
- `--phase 0`: Foundations, domain data models, raw schemas, normalization, and configuration.
- `--phase 1`: Synthetic generator, 10 corruption types, ground-truth isolation, determinism.
- `--phase 2`: Deterministic reconciliation engine, 3-way matching, candidate grouping, evidence extraction, 10 exception classifications, `FeeTaxPolicy`, and independent benchmarks.
- `--phase 3`: AI-powered exception investigation, provider abstraction, prompt injection defense, evidence grounding, and AI benchmarks.
- `--phase generic`: General architectural, security, and code quality review.

---

## 4. Exit Codes & Status Classifications

| Status Classification | Exit Code | Description |
|---|---|---|
| `PRIME_REVIEW_PASS` | `0` | Prime issued an unqualified PASS. Phase is ready for handoff. |
| `PRIME_REVIEW_PASS_WITH_CONDITIONS` | `2` | Prime passed with specific conditions to remediate. |
| `PRIME_REVIEW_BLOCKED` | `3` | Prime found blocking issues. Remediation required. |
| `PRIME_TIMEOUT` | `4` | Execution timed out before completion. |
| `PRIME_EXECUTION_FAILURE` | `5` | WSL or Prime process failed to launch. |

---

## 5. Review Artifact Output

Artifacts are saved under `docs/reviews/prime/`:
```text
docs/reviews/prime/
├── PHASE_0_REVIEW_20260830_101530.md
├── PHASE_1_REVIEW_20260830_153201.md
├── PHASE_2_REVIEW_20260830_184822.md
└── PHASE_3_REVIEW_20260831_120000.md
```

Each artifact preserves:
- Exact Git HEAD commit and branch
- Working tree status (`git status --short`)
- Exact WSL Prime command line and exit code
- Verbatim captured stdout and stderr
- Structured findings and recommendations
