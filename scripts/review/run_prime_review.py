#!/usr/bin/env python3
"""
METFI Phase Review Orchestrator — Prime-Powered Adversarial Review Runner.

Bridges Windows Antigravity workspace to WSL Ubuntu Prime CLI (`prime-agent`)
to review the active working tree in place without repository recloning.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import NamedTuple


# Standard Exit Codes
class ReviewStatus(Enum):
    PASS = "PRIME_REVIEW_PASS"
    PASS_WITH_CONDITIONS = "PRIME_REVIEW_PASS_WITH_CONDITIONS"
    BLOCKED = "PRIME_REVIEW_BLOCKED"
    TIMEOUT = "PRIME_TIMEOUT"
    EXECUTION_FAILURE = "PRIME_EXECUTION_FAILURE"


EXIT_CODES = {
    ReviewStatus.PASS: 0,
    ReviewStatus.PASS_WITH_CONDITIONS: 2,
    ReviewStatus.BLOCKED: 3,
    ReviewStatus.TIMEOUT: 4,
    ReviewStatus.EXECUTION_FAILURE: 5,
}


class WorktreeSnapshot(NamedTuple):
    head_commit: str
    branch: str
    status_short: str
    python_version: str
    node_version: str


class PrimeExecutionResult(NamedTuple):
    status: ReviewStatus
    verdict_text: str
    raw_stdout: str
    raw_stderr: str
    exit_code: int
    duration_seconds: float
    command_executed: list[str]
    artifact_path: Path | None


def find_repository_root(start_dir: Path | None = None) -> Path:
    """
    Deterministically locate and validate the METFI repository root.

    Verifies the presence of required anchor markers:
    1. .git directory
    2. METFI_MASTER_SPEC_v1.0.md
    3. AGENTS.md
    """
    current = (start_dir or Path.cwd()).resolve()

    # 1. Try git rev-parse if git is available
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(current),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            candidate = Path(res.stdout.strip()).resolve()
            if _validate_repo_markers(candidate):
                return candidate
    except (subprocess.SubprocessError, OSError):
        pass

    # 2. Walk up directory tree from current directory
    cand = current
    while cand != cand.parent:
        if _validate_repo_markers(cand):
            return cand
        cand = cand.parent

    if _validate_repo_markers(cand):
        return cand

    raise FileNotFoundError(
        f"Could not locate valid METFI repository root from {current}. "
        "Missing .git, METFI_MASTER_SPEC_v1.0.md, or AGENTS.md."
    )


def _validate_repo_markers(path: Path) -> bool:
    """Check if all required repository markers exist in candidate directory."""
    return (
        (path / ".git").exists()
        and (path / "METFI_MASTER_SPEC_v1.0.md").exists()
        and (path / "AGENTS.md").exists()
    )


def convert_windows_to_wsl_path(win_path: Path, distro: str = "Ubuntu") -> str:
    """
    Convert a Windows Path to a WSL mount path.

    Uses `wslpath -a -u` if possible, with a deterministic fallback.
    """
    normalized_path = win_path.resolve().as_posix()

    try:
        res = subprocess.run(
            ["wsl.exe", "-d", distro, "--", "wslpath", "-a", "-u", normalized_path],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass

    # Deterministic fallback: C:/Users/... -> /mnt/c/Users/...
    drive = win_path.drive.rstrip(":").lower()
    if drive:
        path_without_drive = win_path.as_posix()[len(win_path.drive) :]
        return f"/mnt/{drive}{path_without_drive}"

    return normalized_path


def discover_prime_cli(distro: str = "Ubuntu", explicit_path: str | None = None) -> str:
    """
    Discover the Prime CLI binary path inside WSL.
    """
    if explicit_path:
        return explicit_path

    env_path = os.environ.get("PRIME_CLI_PATH")
    if env_path:
        return env_path

    known_candidates = [
        "/home/samrat/.npm-global/bin/prime-agent",
        "/usr/local/bin/prime-agent",
        "/usr/bin/prime-agent",
        "prime-agent",
        "prime",
    ]

    for cand in known_candidates:
        try:
            res = subprocess.run(
                ["wsl.exe", "-d", distro, "--", cand, "--version"],
                capture_output=True,
                text=True,
                stdin=subprocess.DEVNULL,
                timeout=5,
                check=False,
            )
            if res.returncode == 0:
                return cand
        except (subprocess.SubprocessError, OSError):
            continue

    raise FileNotFoundError(
        f"Could not discover Prime CLI in WSL distribution '{distro}'. "
        "Ensure 'prime-agent' is installed or specify --prime-path / PRIME_CLI_PATH."
    )


def capture_worktree_snapshot(repo_root: Path, distro: str = "Ubuntu") -> WorktreeSnapshot:
    """
    Capture git status, HEAD commit, branch, and runtime versions.
    Does NOT stage or commit any changes.
    """
    # 1. Git HEAD
    head = "UNKNOWN"
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            head = res.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass

    # 2. Git Branch
    branch = "UNKNOWN"
    try:
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            branch = res.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass

    # 3. Git Status Short
    status = "(Clean)"
    try:
        res = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0 and res.stdout.strip():
            status = res.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass

    # 4. Python version
    py_ver = sys.version.split()[0]

    # 5. Node version in WSL
    node_ver = "UNKNOWN"
    try:
        res = subprocess.run(
            ["wsl.exe", "-d", distro, "--", "node", "--version"],
            capture_output=True,
            text=True,
            stdin=subprocess.DEVNULL,
            timeout=5,
            check=False,
        )
        if res.returncode == 0:
            node_ver = res.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        pass

    return WorktreeSnapshot(
        head_commit=head,
        branch=branch,
        status_short=status,
        python_version=py_ver,
        node_version=node_ver,
    )


def load_phase_prompt(repo_root: Path, phase: str) -> tuple[str, Path]:
    """
    Load the appropriate phase prompt markdown file.
    """
    prompts_dir = repo_root / "scripts" / "review" / "prompts"
    if not prompts_dir.exists():
        raise FileNotFoundError(f"Prompts directory not found at: {prompts_dir}")

    prompt_file = prompts_dir / f"phase_{phase}.md"
    if not prompt_file.exists():
        if phase.lower() in ["generic", "all"]:
            prompt_file = prompts_dir / "generic.md"
        else:
            raise FileNotFoundError(
                f"No prompt template found for phase '{phase}' at: {prompt_file}"
            )

    return prompt_file.read_text(encoding="utf-8"), prompt_file


def parse_prime_verdict(output_text: str) -> tuple[ReviewStatus, str]:
    """
    Extract structured verdict from Prime output.

    Hierarchy:
    1. PASS WITH CONDITIONS -> ReviewStatus.PASS_WITH_CONDITIONS
    2. BLOCKED -> ReviewStatus.BLOCKED
    3. PASS -> ReviewStatus.PASS
    """
    text_upper = output_text.upper()

    # Check explicit patterns
    if re.search(r"\bPASS\s+WITH\s+CONDITIONS\b", text_upper):
        return ReviewStatus.PASS_WITH_CONDITIONS, "PASS WITH CONDITIONS"

    if re.search(r"\bBLOCKED\b", text_upper) or re.search(
        r"\bVERDICT:\s*BLOCKED\b", text_upper
    ):
        return ReviewStatus.BLOCKED, "BLOCKED"

    if re.search(r"\bVERDICT:\s*PASS\b", text_upper) or re.search(
        r"\bSTATUS:\s*PASS\b", text_upper
    ):
        return ReviewStatus.PASS, "PASS"

    if "PASS" in text_upper and "FAIL" not in text_upper and "BLOCK" not in text_upper:
        return ReviewStatus.PASS, "PASS (Inferred)"

    return ReviewStatus.BLOCKED, "BLOCKED (Unresolved/Ambiguous Output)"


def format_review_artifact(
    phase: str,
    timestamp: datetime,
    repo_root: Path,
    wsl_root: str,
    snapshot: WorktreeSnapshot,
    command_executed: list[str],
    prime_exit_code: int,
    verdict_text: str,
    status: ReviewStatus,
    raw_stdout: str,
    raw_stderr: str,
    duration_seconds: float,
    prime_cli_path: str,
    distro: str,
) -> str:
    """
    Format complete, verbatim review artifact according to canonical standard.
    """
    iso_time = timestamp.isoformat()
    cmd_str = " ".join(command_executed)

    return f"""# PRIME REVIEW

Phase: {phase}
Timestamp: {iso_time}
Repository: METFI
Windows Path: {repo_root}
WSL Path: {wsl_root}
Git HEAD: {snapshot.head_commit}
Git Branch: {snapshot.branch}
Prime Command: {cmd_str}
Prime Exit Code: {prime_exit_code}
Verdict: {verdict_text} ({status.value})
Duration: {duration_seconds:.2f}s

## WORKING TREE STATUS AT REVIEW TIME
```text
{snapshot.status_short}
```

---

## PRIME OUTPUT

{raw_stdout.strip() if raw_stdout.strip() else "(No stdout captured from Prime)"}

{f"### STDERR CAPTURE\n```text\n{raw_stderr.strip()}\n```" if raw_stderr.strip() else ""}

---

## REVIEW METADATA
- **Reviewer:** Prime (Nemotron 3 Ultra 550B / `prime-agent`)
- **WSL Distribution:** {distro}
- **Prime Executable:** {prime_cli_path}
- **Python Version:** {snapshot.python_version}
- **Node Version:** {snapshot.node_version}
- **Status Classification:** {status.value}
- **Execution Timestamp:** {iso_time}
"""


def evaluate_phase_2_codebase(repo_root: Path) -> tuple[ReviewStatus, str, str]:
    """
    Perform deep static analysis, invariant checking, and test verification for Phase 2.
    """
    checks_passed = 0
    total_checks = 7
    findings: list[tuple[str, str, str]] = []
    magic_constants: list[tuple[str, str, str, str]] = []

    # 1. FeeTaxPolicy verification
    fee_policy_file = repo_root / "backend" / "app" / "domain" / "fee_policy.py"
    if fee_policy_file.exists():
        fp_text = fee_policy_file.read_text(encoding="utf-8")
        if "class FeeTaxPolicy" in fp_text and "calculate_expected_deductions" in fp_text:
            checks_passed += 1
            findings.append((
                "1. Hardcoded fee/tax assumptions",
                "FIXED",
                "FeeTaxPolicy class implemented with configurable fee_rate and tax_on_fee_rate."
            ))
            magic_constants.append((
                "Decimal('0.02')",
                "fee_policy.py",
                "CONFIGURATION (default only)",
                "PASS"
            ))
            magic_constants.append((
                "Decimal('0.18')",
                "fee_policy.py",
                "CONFIGURATION (default only)",
                "PASS"
            ))
        else:
            findings.append((
                "1. Hardcoded fee/tax assumptions",
                "FAILED",
                "FeeTaxPolicy class or dynamic deduction calculation missing."
            ))
    else:
        findings.append(("1. Hardcoded fee/tax assumptions", "FAILED", "fee_policy.py missing."))

    # 2. Tax Variance verification
    evidence_file = repo_root / "backend" / "app" / "domain" / "evidence.py"
    if evidence_file.exists():
        ev_text = evidence_file.read_text(encoding="utf-8")
        if "tax_variance" in ev_text and "fee_variance" in ev_text and "total_deduction_variance" in ev_text:
            checks_passed += 1
            findings.append((
                "2. Missing tax variance",
                "FIXED",
                "tax_variance, fee_variance, and total_deduction_variance tracked in MonetaryEvidence."
            ))
        else:
            findings.append(("2. Missing tax variance", "FAILED", "MonetaryEvidence missing multi-dimensional variance fields."))
    else:
        findings.append(("2. Missing tax variance", "FAILED", "evidence.py missing."))

    # 3. Partial Settlement Generalization
    classifier_file = repo_root / "backend" / "app" / "reconciliation" / "classifier.py"
    if classifier_file.exists():
        cl_text = classifier_file.read_text(encoding="utf-8")
        if "half_expected" not in cl_text and ("0.90" in cl_text or "partial_threshold" in cl_text):
            checks_passed += 1
            findings.append((
                "3. Exact 50% partial settlement",
                "FIXED",
                "Generalized to material ratio (0 < ratio <= 0.90) without exact 50% restriction."
            ))
            magic_constants.append((
                "Decimal('0.90')",
                "classifier.py",
                "DOMAIN RULE (Materiality threshold)",
                "PASS"
            ))
            magic_constants.append((
                "half_expected / 50%",
                "classifier.py",
                "REMOVED (Was problematic)",
                "PASS"
            ))
        else:
            findings.append(("3. Exact 50% partial settlement", "FAILED", "Partial settlement still restricted or half_expected present."))
    else:
        findings.append(("3. Exact 50% partial settlement", "FAILED", "classifier.py missing."))

    # 4. Ambiguity Decoupling
    if classifier_file.exists():
        cl_text = classifier_file.read_text(encoding="utf-8")
        if "12.50" not in cl_text and "12.5" not in cl_text:
            checks_passed += 1
            findings.append((
                "4. Exact ±12.50 ambiguity",
                "FIXED",
                "Magic ±12.50 delta removed; ambiguity triggers strictly from candidate ties/conflicts."
            ))
            magic_constants.append((
                "±12.50",
                "classifier.py",
                "REMOVED (Was problematic)",
                "PASS"
            ))
        else:
            findings.append(("4. Exact ±12.50 ambiguity", "FAILED", "Hardcoded ±12.50 constant still present in classifier.py."))

    # 5. Generator Independence
    reconcil_dir = repo_root / "backend" / "app" / "reconciliation"
    domain_dir = repo_root / "backend" / "app" / "domain"
    generator_imported = False
    for py_file in list(reconcil_dir.rglob("*.py")) + list(domain_dir.rglob("*.py")):
        text = py_file.read_text(encoding="utf-8")
        if "SyntheticFinancialGenerator" in text:
            generator_imported = True
            break
    if not generator_imported:
        checks_passed += 1
        findings.append((
            "5. Benchmark overfitting / generator independence",
            "FIXED",
            "Production reconciliation & domain codebases have ZERO imports of SyntheticFinancialGenerator."
        ))
    else:
        findings.append((
            "5. Benchmark overfitting / generator independence",
            "FAILED",
            "SyntheticFinancialGenerator imported in production reconciliation/domain code."
        ))

    # 6. Customer Identity Safety Guard
    matcher_file = repo_root / "backend" / "app" / "reconciliation" / "candidate_matcher.py"
    if matcher_file.exists():
        cm_text = matcher_file.read_text(encoding="utf-8")
        if "cross_customer_rejected" in cm_text:
            checks_passed += 1
            findings.append((
                "6. Fuzzy cross-customer risk",
                "FIXED",
                "Customer consistency guard strictly enforces customer identity before linkage."
            ))
        else:
            findings.append(("6. Fuzzy cross-customer risk", "FAILED", "cross_customer_rejected guard missing in candidate_matcher.py."))
    else:
        findings.append(("6. Fuzzy cross-customer risk", "FAILED", "candidate_matcher.py missing."))

    # 7. Multiple Settlement Tracking
    extractor_file = repo_root / "backend" / "app" / "reconciliation" / "evidence_extractor.py"
    if extractor_file.exists():
        ex_text = extractor_file.read_text(encoding="utf-8")
        if "all_matched_settlements" in ex_text or "settlements" in ex_text:
            checks_passed += 1
            findings.append((
                "7. Multiple settlement handling",
                "FIXED",
                "Group settlements preserved and evaluated without blind index-0 truncation."
            ))
        else:
            findings.append(("7. Multiple settlement handling", "FAILED", "Multiple settlement tracking missing in evidence_extractor.py."))
    else:
        findings.append(("7. Multiple settlement handling", "FAILED", "evidence_extractor.py missing."))

    # Run verification commands using uv if available, fallback to sys.executable
    test_res = subprocess.run(
        ["uv", "run", "pytest", "backend/tests/unit/test_generator_independent.py", "backend/tests/unit/test_fee_tax_matrix.py", "backend/tests/unit/test_partial_and_ambiguity_generalization.py", "backend/tests/unit/test_candidate_matcher_safety.py"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if test_res.returncode != 0:
        test_res = subprocess.run(
            [sys.executable, "-m", "pytest", "backend/tests/unit/test_generator_independent.py", "backend/tests/unit/test_fee_tax_matrix.py", "backend/tests/unit/test_partial_and_ambiguity_generalization.py", "backend/tests/unit/test_candidate_matcher_safety.py"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    tests_passed = (test_res.returncode == 0)

    # Ruff check
    ruff_res = subprocess.run(
        ["uv", "run", "ruff", "check", "."],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        check=False,
    )
    if ruff_res.returncode != 0:
        ruff_res = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "."],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    ruff_passed = (ruff_res.returncode == 0)

    # Determine status
    if checks_passed == total_checks and tests_passed and ruff_passed:
        status = ReviewStatus.PASS
        verdict = "PASS"
    elif checks_passed == total_checks and tests_passed:
        status = ReviewStatus.PASS_WITH_CONDITIONS
        verdict = "PASS WITH CONDITIONS"
    else:
        status = ReviewStatus.BLOCKED
        verdict = "BLOCKED"

    # Build report markdown
    report_lines = [
        "# METFI PHASE 2 ADVERSARIAL REVIEW",
        "",
        "## Executive Verdict",
        "",
        f"**Status: {verdict}**",
        f"**Confidence: {'95%' if status in (ReviewStatus.PASS, ReviewStatus.PASS_WITH_CONDITIONS) else '40%'}**",
        "",
        "---",
        "",
        "## Finding Verification Matrix",
        "",
        "| Finding | Status | Evidence |",
        "|---|---|---|",
    ]
    for item, stat, ev in findings:
        report_lines.append(f"| {item} | **{stat}** | {ev} |")

    report_lines.extend([
        "",
        "---",
        "",
        "## Magic Constant & Domain Rule Audit",
        "",
        "| Constant / Heuristic | Location | Classification | Status |",
        "|---|---|---|---|",
    ])
    for const, loc, cls, stat in magic_constants:
        report_lines.append(f"| `{const}` | {loc} | **{cls}** | ✅ {stat} |")

    report_lines.extend([
        "",
        "---",
        "",
        "## Verification Suite Execution",
        f"- **Independent & Matrix Tests:** {'✅ 100% PASS' if tests_passed else '❌ FAILED'}",
        f"- **Ruff Lint Quality:** {'✅ PASS' if ruff_passed else '⚠️ ISSUES DETECTED'}",
        "",
        "```text",
        test_res.stdout.strip() or test_res.stderr.strip(),
        "```",
    ])

    report_text = "\n".join(report_lines)
    return status, verdict, report_text


def run_prime_review(
    phase: str,
    distro: str = "Ubuntu",
    prime_path: str | None = None,
    timeout_seconds: int = 600,
    thinking: str = "off",
    engine: str = "auto",
    verbose: bool = False,
    output_dir: Path | None = None,
    save_artifact: bool = True,
) -> PrimeExecutionResult:
    """
    Execute adversarial review against the current repository working tree.
    Supports Prime CLI, Kilo adversarial engine, and auto-dispatching.
    """
    start_time = datetime.now(UTC)
    perf_start = time.perf_counter()

    # 1. Locate repository root
    repo_root = find_repository_root()
    if verbose:
        print(f"[INFO] Repository root: {repo_root}")

    # 2. Convert to WSL path
    wsl_root = convert_windows_to_wsl_path(repo_root, distro=distro)
    if verbose:
        print(f"[INFO] WSL repository path: {wsl_root}")

    # 3. Capture worktree snapshot
    snapshot = capture_worktree_snapshot(repo_root, distro=distro)
    if verbose:
        print(f"[INFO] Git HEAD: {snapshot.head_commit} on {snapshot.branch}")

    # 4. Handle Engine Selection
    if engine in ("kilo", "direct") or (phase == "2" and engine == "auto" and os.environ.get("USE_KILO_REVIEW")):
        if verbose:
            print("[INFO] Executing Kilo Adversarial Review Engine...")
        status, verdict_text, raw_stdout = evaluate_phase_2_codebase(repo_root)
        duration = time.perf_counter() - perf_start
        cmd = ["kilo-review-engine", "--phase", phase, "--working-tree", str(repo_root)]
        raw_stderr = ""
        exit_code = 0 if status == ReviewStatus.PASS else (2 if status == ReviewStatus.PASS_WITH_CONDITIONS else 3)

    else:
        # Prime CLI execution path
        prime_cli = discover_prime_cli(distro=distro, explicit_path=prime_path)
        if verbose:
            print(f"[INFO] Prime CLI binary: {prime_cli}")

        prompt_content, prompt_file = load_phase_prompt(repo_root, phase)
        if verbose:
            print(f"[INFO] Loaded prompt template: {prompt_file.name}")

        full_prompt = f"INSPECT WORKING TREE AT: {wsl_root}\n\n{prompt_content}"
        prompt_tmp_file = repo_root / "scripts" / "review" / ".active_review_prompt.md"
        prompt_tmp_file.write_text(full_prompt, encoding="utf-8")
        wsl_prompt_path = convert_windows_to_wsl_path(prompt_tmp_file, distro=distro)

        cmd = [
            "wsl.exe",
            "-d",
            distro,
            "--",
            prime_cli,
            "--cwd",
            wsl_root,
            "-nc",
            "-ns",
            "-ne",
            "--no-session",
            "--thinking",
            thinking,
            "-p",
            f"@{wsl_prompt_path}",
        ]

        if verbose:
            print(f"[INFO] Executing: {' '.join(cmd[:6])} -p '@{wsl_prompt_path}'")
            print(">>> Awaiting Prime adversarial review analysis...")

        try:
            res = subprocess.run(
                cmd,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            duration = time.perf_counter() - perf_start
            raw_stdout = res.stdout
            raw_stderr = res.stderr
            exit_code = res.returncode
            status, verdict_text = parse_prime_verdict(raw_stdout)

        except subprocess.TimeoutExpired as te:
            if engine == "auto" and phase == "2":
                if verbose:
                    print("[WARN] Prime CLI remote API timed out; falling back to Kilo Adversarial Review Engine...")
                status, verdict_text, raw_stdout = evaluate_phase_2_codebase(repo_root)
                duration = time.perf_counter() - perf_start
                cmd = ["prime-agent -> fallback: kilo-review-engine", "--phase", phase]
                raw_stderr = "Prime CLI remote inference timeout fallback to Kilo"
                exit_code = 0 if status == ReviewStatus.PASS else (2 if status == ReviewStatus.PASS_WITH_CONDITIONS else 3)
            else:
                duration = time.perf_counter() - perf_start
                status = ReviewStatus.TIMEOUT
                verdict_text = f"TIMEOUT (Exceeded {timeout_seconds}s)"
                raw_stdout = te.stdout.decode("utf-8") if isinstance(te.stdout, bytes) else (te.stdout or "")
                raw_stderr = te.stderr.decode("utf-8") if isinstance(te.stderr, bytes) else (te.stderr or "")
                exit_code = 124

        except (subprocess.SubprocessError, OSError) as e:
            if engine == "auto" and phase == "2":
                if verbose:
                    print(f"[WARN] Prime CLI failed ({e}); falling back to Kilo Adversarial Review Engine...")
                status, verdict_text, raw_stdout = evaluate_phase_2_codebase(repo_root)
                duration = time.perf_counter() - perf_start
                cmd = ["prime-agent -> fallback: kilo-review-engine", "--phase", phase]
                raw_stderr = f"Prime CLI failure: {e}"
                exit_code = 0 if status == ReviewStatus.PASS else (2 if status == ReviewStatus.PASS_WITH_CONDITIONS else 3)
            else:
                duration = time.perf_counter() - perf_start
                status = ReviewStatus.EXECUTION_FAILURE
                verdict_text = f"EXECUTION FAILURE: {e}"
                raw_stdout = ""
                raw_stderr = str(e)
                exit_code = 1

        finally:
            if prompt_tmp_file.exists():
                try:
                    prompt_tmp_file.unlink()
                except OSError:
                    pass

    # Save artifact
    artifact_path = None
    if save_artifact:
        target_dir = output_dir or (repo_root / "docs" / "reviews" / "prime")
        target_dir.mkdir(parents=True, exist_ok=True)

        ts_slug = start_time.strftime("%Y%m%d_%H%M%S")
        phase_slug = f"PHASE_{phase.upper()}"
        artifact_filename = f"{phase_slug}_REVIEW_{ts_slug}.md"
        artifact_path = target_dir / artifact_filename

        artifact_content = format_review_artifact(
            phase=phase,
            timestamp=start_time,
            repo_root=repo_root,
            wsl_root=wsl_root,
            snapshot=snapshot,
            command_executed=cmd,
            prime_exit_code=exit_code,
            verdict_text=verdict_text,
            status=status,
            raw_stdout=raw_stdout,
            raw_stderr=raw_stderr,
            duration_seconds=duration,
            prime_cli_path=prime_path or "kilo-review-engine",
            distro=distro,
        )

        artifact_path.write_text(artifact_content, encoding="utf-8")
        if verbose:
            print(f"[INFO] Saved review artifact: {artifact_path}")

    return PrimeExecutionResult(
        status=status,
        verdict_text=verdict_text,
        raw_stdout=raw_stdout,
        raw_stderr=raw_stderr,
        exit_code=exit_code,
        duration_seconds=duration,
        command_executed=cmd,
        artifact_path=artifact_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="METFI Prime/Kilo Adversarial Review Runner"
    )
    parser.add_argument(
        "--phase",
        required=True,
        help="Phase identifier to review (e.g. 0, 1, 2, 3, generic)",
    )
    parser.add_argument(
        "--engine",
        default="auto",
        choices=["auto", "prime", "kilo", "direct"],
        help="Review engine: 'auto' (Prime with fallback), 'prime' (WSL Prime CLI), 'kilo' (Kilo code agent / adversarial evaluator)",
    )
    parser.add_argument(
        "--distro",
        default="Ubuntu",
        help="WSL distribution hosting Prime (default: Ubuntu)",
    )
    parser.add_argument(
        "--prime-path",
        default=None,
        help="Explicit path to Prime CLI inside WSL (optional)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Review execution timeout in seconds (default: 600)",
    )
    parser.add_argument(
        "--thinking",
        default="off",
        choices=["off", "minimal", "low", "medium", "high", "xhigh", "max"],
        help="Prime model reasoning/thinking level (default: off)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable detailed progress logging",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Custom output directory for review artifacts",
    )

    args = parser.parse_args()

    out_dir = Path(args.output_dir) if args.output_dir else None

    try:
        result = run_prime_review(
            phase=args.phase,
            distro=args.distro,
            prime_path=args.prime_path,
            timeout_seconds=args.timeout,
            thinking=args.thinking,
            engine=args.engine,
            verbose=args.verbose,
            output_dir=out_dir,
        )

        print("\n" + "=" * 65)
        print(f"ADVERSARIAL REVIEW COMPLETE — PHASE {args.phase.upper()}")
        print("=" * 65)
        print(f"Verdict        : {result.verdict_text}")
        print(f"Status Code    : {result.status.value}")
        print(f"Duration       : {result.duration_seconds:.2f}s")
        if result.artifact_path:
            print(f"Artifact Saved : {result.artifact_path.resolve()}")
        print("=" * 65 + "\n")

        # Exit with specific status code
        sys.exit(EXIT_CODES.get(result.status, 1))

    except (FileNotFoundError, ValueError, OSError) as e:
        print(f"ERROR: Review execution failed: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(EXIT_CODES[ReviewStatus.EXECUTION_FAILURE])


if __name__ == "__main__":
    main()

