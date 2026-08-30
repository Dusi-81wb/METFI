#!/usr/bin/env python3
"""
METFI Kilo Code Review Runner — Specialized Agent Adversarial Evaluation Engine.

Executes Kilo Code CLI (@kilocode/cli) specialized agents (reviewer, debugger,
tester, planner, orchestrator) against the active working tree with read-only guarantees.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import NamedTuple

from kilo_capabilities import (
    discover_kilo_capabilities,
    get_phase_recommended_agents,
    resolve_kilo_agent,
)


class FindingSeverity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class KiloFinding(NamedTuple):
    severity: FindingSeverity
    title: str
    description: str
    location: str | None = None
    agent: str = "kilo"


class KiloReviewStatus(Enum):
    PASS = "KILO_REVIEW_PASS"
    PASS_WITH_CONDITIONS = "KILO_REVIEW_PASS_WITH_CONDITIONS"
    BLOCKED = "KILO_REVIEW_BLOCKED"
    TIMEOUT = "KILO_TIMEOUT"
    EXECUTION_FAILURE = "KILO_EXECUTION_FAILURE"
    UNAVAILABLE = "KILO_UNAVAILABLE"


KILO_EXIT_CODES = {
    KiloReviewStatus.PASS: 0,
    KiloReviewStatus.PASS_WITH_CONDITIONS: 2,
    KiloReviewStatus.BLOCKED: 3,
    KiloReviewStatus.TIMEOUT: 4,
    KiloReviewStatus.EXECUTION_FAILURE: 5,
    KiloReviewStatus.UNAVAILABLE: 6,
}


class KiloExecutionResult(NamedTuple):
    status: KiloReviewStatus
    verdict_text: str
    raw_stdout: str
    raw_stderr: str
    exit_code: int
    duration_seconds: float
    command_executed: list[str]
    agent_role: str
    resolved_kilo_agent: str
    findings: list[KiloFinding]
    artifact_path: Path | None


def parse_kilo_findings(text: str, agent: str = "kilo") -> list[KiloFinding]:
    """Parse structured severity findings from Kilo output."""
    findings: list[KiloFinding] = []
    lines = text.splitlines()

    for line in lines:
        match = re.search(
            r"\b(CRITICAL|HIGH|MEDIUM|LOW|INFO)\b[:\s\-]+(.+)",
            line,
            re.IGNORECASE,
        )
        if match:
            sev_str = match.group(1).upper()
            title = match.group(2).strip()
            # Ignore markdown header echoes
            if title.startswith("#") or "FINDING" in title.upper() and len(title) < 15:
                continue
            severity = FindingSeverity[sev_str]
            findings.append(
                KiloFinding(
                    severity=severity,
                    title=title,
                    description=line.strip(),
                    agent=agent,
                )
            )

    return findings


def parse_kilo_verdict(
    text: str, findings: list[KiloFinding] | None = None
) -> tuple[KiloReviewStatus, str]:
    """
    Parse Kilo review verdict into canonical status: PASS, PASS_WITH_CONDITIONS, or BLOCKED.
    """
    text_upper = text.upper()

    # Explicit blocked signals
    if (
        re.search(r"\bVERDICT:\s*BLOCKED\b", text_upper)
        or re.search(r"\bSTATUS:\s*BLOCKED\b", text_upper)
        or re.search(r"\bFINAL VERDICT:\s*BLOCKED\b", text_upper)
    ):
        return KiloReviewStatus.BLOCKED, "BLOCKED"

    # If critical findings exist, block regardless
    if findings:
        critical_count = sum(
            1 for f in findings if f.severity == FindingSeverity.CRITICAL
        )
        if critical_count > 0:
            return (
                KiloReviewStatus.BLOCKED,
                f"BLOCKED ({critical_count} critical finding(s))",
            )

    # Explicit Pass with conditions
    if (
        re.search(r"\bVERDICT:\s*PASS\s+WITH\s+CONDITIONS\b", text_upper)
        or re.search(r"\bSTATUS:\s*PASS\s+WITH\s+CONDITIONS\b", text_upper)
        or "PASS WITH CONDITIONS" in text_upper
    ):
        return KiloReviewStatus.PASS_WITH_CONDITIONS, "PASS WITH CONDITIONS"

    # Explicit Pass
    if re.search(r"\bVERDICT:\s*PASS\b", text_upper) or re.search(
        r"\bSTATUS:\s*PASS\b", text_upper
    ):
        return KiloReviewStatus.PASS, "PASS"

    # Check for high severity findings
    if findings:
        high_count = sum(1 for f in findings if f.severity == FindingSeverity.HIGH)
        if high_count > 0:
            return (
                KiloReviewStatus.PASS_WITH_CONDITIONS,
                f"PASS WITH CONDITIONS ({high_count} high finding(s))",
            )

    if "PASS" in text_upper and "FAIL" not in text_upper and "BLOCK" not in text_upper:
        return KiloReviewStatus.PASS, "PASS (Inferred)"

    return KiloReviewStatus.BLOCKED, "BLOCKED (Unresolved/Ambiguous Output)"


def format_kilo_review_artifact(
    phase: str,
    timestamp: datetime,
    repo_root: Path,
    agent_role: str,
    resolved_agent: str,
    command_executed: list[str],
    exit_code: int,
    verdict_text: str,
    status: KiloReviewStatus,
    raw_stdout: str,
    raw_stderr: str,
    duration_seconds: float,
    kilo_version: str,
    git_head: str,
    git_branch: str,
    git_status: str,
    is_fallback: bool = False,
    primary_failure_reason: str | None = None,
) -> str:
    """Format single Kilo review artifact according to canonical standard."""
    iso_time = timestamp.isoformat()
    cmd_str = " ".join(command_executed)

    header = f"""# KILO CODE REVIEW

Phase: {phase}
Timestamp: {iso_time}
Repository: METFI
Working tree: {repo_root}
Git HEAD: {git_head}
Git Branch: {git_branch}
Engine: Kilo Code CLI (@kilocode/cli)
Agent Role: {agent_role}
Resolved Kilo Agent: {resolved_agent}
Kilo Version: {kilo_version}
Command: {cmd_str}
Exit Code: {exit_code}
Verdict: {verdict_text} ({status.value})
Duration: {duration_seconds:.2f}s
"""

    if is_fallback:
        header += f"""
> [!WARNING]
> **FALLBACK REVIEW ACTIVE**
> Primary Reviewer: Prime — unavailable ({primary_failure_reason or "infrastructure failure"})
> Fallback Reviewer: Kilo Code — {agent_role} ({resolved_agent})
> Note: This fallback review provides secondary verification and does NOT constitute Prime independent certification.
"""

    body = f"""
## WORKING TREE STATUS AT REVIEW TIME
```text
{git_status}
```

---

## VERBATIM ENGINE OUTPUT

{raw_stdout.strip() if raw_stdout.strip() else "(No stdout captured from Kilo)"}

{f"### STDERR CAPTURE\n```text\n{raw_stderr.strip()}\n```" if raw_stderr.strip() else ""}

---

## REVIEW METADATA
- **Reviewer:** Kilo Code ({resolved_agent} / {agent_role})
- **Engine Type:** Secondary / Specialist Reviewer
- **Kilo CLI Version:** {kilo_version}
- **Status Classification:** {status.value}
- **Execution Timestamp:** {iso_time}
"""

    return header + body


def run_single_kilo_agent(
    phase: str,
    agent_role: str = "reviewer",
    repo_root: Path | None = None,
    timeout_seconds: int = 600,
    model: str | None = None,
    thinking: bool = False,
    is_fallback: bool = False,
    primary_failure_reason: str | None = None,
    verbose: bool = False,
    output_dir: Path | None = None,
    save_artifact: bool = True,
) -> KiloExecutionResult:
    """
    Execute a single Kilo Code agent review against the current active working tree.
    """
    start_time = datetime.now(UTC)
    perf_start = time.perf_counter()

    root = repo_root or Path.cwd()
    caps = discover_kilo_capabilities()

    if not caps.available or not caps.executable:
        return KiloExecutionResult(
            status=KiloReviewStatus.UNAVAILABLE,
            verdict_text="KILO_UNAVAILABLE (Kilo CLI executable not found in PATH)",
            raw_stdout="",
            raw_stderr=caps.raw_error or "Kilo CLI unavailable",
            exit_code=KILO_EXIT_CODES[KiloReviewStatus.UNAVAILABLE],
            duration_seconds=0.0,
            command_executed=[],
            agent_role=agent_role,
            resolved_kilo_agent="none",
            findings=[],
            artifact_path=None,
        )

    resolved_agent = resolve_kilo_agent(agent_role)

    # Git snapshot
    try:
        head_res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        git_head = head_res.stdout.strip() if head_res.returncode == 0 else "UNKNOWN"
        branch_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        git_branch = (
            branch_res.stdout.strip() if branch_res.returncode == 0 else "UNKNOWN"
        )
        status_res = subprocess.run(
            ["git", "status", "--short"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=False,
        )
        git_status = status_res.stdout.strip() if status_res.returncode == 0 else ""
    except (subprocess.SubprocessError, OSError):
        git_head, git_branch, git_status = "UNKNOWN", "UNKNOWN", ""

    # Load prompt for phase
    prompt_file = root / "scripts" / "review" / "prompts" / f"phase_{phase}.md"
    if not prompt_file.exists():
        prompt_file = root / "scripts" / "review" / "prompts" / "generic.md"

    prompt_content = (
        prompt_file.read_text(encoding="utf-8")
        if prompt_file.exists()
        else f"Review Phase {phase}"
    )

    role_instruction = (
        f"You are operating as the KILO SPECIALIST ({agent_role.upper()}) conducting an adversarial review of Phase {phase}.\n"
        f"Role Mission:\n"
        f"- Reviewer: evaluate architecture, contract generalization, magic constants, and domain correctness.\n"
        f"- Debugger: isolate potential regression vulnerabilities, edge cases, and failure modes.\n"
        f"- Tester: verify test coverage, matrix combinations, and assertion completeness.\n"
        f"- Planner: prepare remediation recommendations without modifying code.\n"
        f"- Orchestrator: coordinate multi-step finding aggregation.\n\n"
        f"CRITICAL CONSTRAINT: YOU ARE A READ-ONLY REVIEWER. DO NOT WRITE, EDIT, OR COMMIT FILES.\n\n"
        f"{prompt_content}"
    )

    cmd = [
        caps.executable,
        "run",
        "--agent",
        resolved_agent,
        "--dir",
        str(root),
    ]

    if model:
        cmd.extend(["--model", model])
    if thinking:
        cmd.append("--thinking")

    cmd.append(role_instruction)

    if verbose:
        print(
            f"[INFO] Executing Kilo ({agent_role} -> {resolved_agent}) against {root}"
        )

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

        findings = parse_kilo_findings(raw_stdout, agent=agent_role)
        status, verdict_text = parse_kilo_verdict(raw_stdout, findings=findings)

    except subprocess.TimeoutExpired as te:
        duration = time.perf_counter() - perf_start
        status = KiloReviewStatus.TIMEOUT
        verdict_text = f"TIMEOUT (Exceeded {timeout_seconds}s)"
        raw_stdout = (
            te.stdout.decode("utf-8")
            if isinstance(te.stdout, bytes)
            else (te.stdout or "")
        )
        raw_stderr = (
            te.stderr.decode("utf-8")
            if isinstance(te.stderr, bytes)
            else (te.stderr or "")
        )
        exit_code = 124
        findings = []

    except (subprocess.SubprocessError, OSError) as e:
        duration = time.perf_counter() - perf_start
        status = KiloReviewStatus.EXECUTION_FAILURE
        verdict_text = f"EXECUTION FAILURE: {e}"
        raw_stdout = ""
        raw_stderr = str(e)
        exit_code = 1
        findings = []

    # Save artifact
    artifact_path = None
    if save_artifact:
        target_dir = output_dir or (root / "docs" / "reviews" / "prime")
        target_dir.mkdir(parents=True, exist_ok=True)

        ts_slug = start_time.strftime("%Y%m%d_%H%M%S")
        prefix = "FALLBACK" if is_fallback else "KILO"
        artifact_filename = (
            f"PHASE_{phase.upper()}_{prefix}_REVIEW_{agent_role.upper()}_{ts_slug}.md"
        )
        artifact_path = target_dir / artifact_filename

        content = format_kilo_review_artifact(
            phase=phase,
            timestamp=start_time,
            repo_root=root,
            agent_role=agent_role,
            resolved_agent=resolved_agent,
            command_executed=cmd[:6],
            exit_code=exit_code,
            verdict_text=verdict_text,
            status=status,
            raw_stdout=raw_stdout,
            raw_stderr=raw_stderr,
            duration_seconds=duration,
            kilo_version=caps.version or "unknown",
            git_head=git_head,
            git_branch=git_branch,
            git_status=git_status,
            is_fallback=is_fallback,
            primary_failure_reason=primary_failure_reason,
        )

        artifact_path.write_text(content, encoding="utf-8")
        if verbose:
            print(f"[INFO] Saved Kilo artifact: {artifact_path}")

    return KiloExecutionResult(
        status=status,
        verdict_text=verdict_text,
        raw_stdout=raw_stdout,
        raw_stderr=raw_stderr,
        exit_code=exit_code,
        duration_seconds=duration,
        command_executed=cmd[:6],
        agent_role=agent_role,
        resolved_kilo_agent=resolved_agent,
        findings=findings,
        artifact_path=artifact_path,
    )


def run_kilo_pipeline(
    phase: str,
    repo_root: Path | None = None,
    timeout_seconds: int = 600,
    model: str | None = None,
    thinking: bool = False,
    verbose: bool = False,
    output_dir: Path | None = None,
) -> tuple[KiloReviewStatus, str, Path | None]:
    """
    Execute full multi-agent Kilo specialist pipeline for the phase and generate combined report.
    """
    start_time = datetime.now(UTC)
    root = repo_root or Path.cwd()

    specialist_roles = get_phase_recommended_agents(phase)
    if verbose:
        print(
            f"[INFO] Running Kilo Specialist Pipeline for Phase {phase}: {', '.join(specialist_roles)}"
        )

    results: list[KiloExecutionResult] = []
    for role in specialist_roles:
        res = run_single_kilo_agent(
            phase=phase,
            agent_role=role,
            repo_root=root,
            timeout_seconds=timeout_seconds,
            model=model,
            thinking=thinking,
            verbose=verbose,
            output_dir=output_dir,
            save_artifact=True,
        )
        results.append(res)

    # Determine overall status
    has_blocked = any(r.status == KiloReviewStatus.BLOCKED for r in results)
    has_conditions = any(
        r.status == KiloReviewStatus.PASS_WITH_CONDITIONS for r in results
    )
    all_passed = all(r.status == KiloReviewStatus.PASS for r in results)

    if has_blocked:
        overall_status = KiloReviewStatus.BLOCKED
        overall_verdict = "BLOCKED (Specialist Finding Block)"
    elif has_conditions:
        overall_status = KiloReviewStatus.PASS_WITH_CONDITIONS
        overall_verdict = "PASS WITH CONDITIONS"
    elif all_passed:
        overall_status = KiloReviewStatus.PASS
        overall_verdict = "PASS (All Specialists Agreed)"
    else:
        overall_status = KiloReviewStatus.BLOCKED
        overall_verdict = "BLOCKED (Pipeline Failure)"

    # Format Combined Artifact
    target_dir = output_dir or (root / "docs" / "reviews" / "prime")
    target_dir.mkdir(parents=True, exist_ok=True)
    ts_slug = start_time.strftime("%Y%m%d_%H%M%S")
    combined_filename = f"PHASE_{phase.upper()}_COMBINED_REVIEW_{ts_slug}.md"
    combined_path = target_dir / combined_filename

    combined_lines = [
        f"# METFI PHASE {phase.upper()} COMBINED SPECIALIST REVIEW",
        "",
        f"Timestamp: {start_time.isoformat()}",
        "Repository: METFI",
        f"Pipeline Verdict: **{overall_verdict}**",
        f"Total Specialists: {len(results)}",
        "",
        "## Specialist Execution Summary",
        "",
        "| Specialist Role | Kilo Agent | Verdict | Duration | Findings Count |",
        "|---|---|---|---|---|",
    ]

    for r in results:
        combined_lines.append(
            f"| {r.agent_role.upper()} | `{r.resolved_kilo_agent}` | **{r.verdict_text}** | {r.duration_seconds:.2f}s | {len(r.findings)} |"
        )

    combined_lines.extend(
        [
            "",
            "---",
            "",
            "## Aggregated Findings by Role",
            "",
        ]
    )

    for r in results:
        combined_lines.append(
            f"### Role: {r.agent_role.upper()} ({r.resolved_kilo_agent})"
        )
        if r.findings:
            for f in r.findings:
                combined_lines.append(f"- **[{f.severity.value}]** {f.title}")
        else:
            combined_lines.append("- *(No blocking severity findings reported)*")
        combined_lines.append("")

    combined_path.write_text("\n".join(combined_lines), encoding="utf-8")
    if verbose:
        print(f"[INFO] Saved combined review artifact: {combined_path}")

    return overall_status, overall_verdict, combined_path


def main() -> None:
    parser = argparse.ArgumentParser(description="METFI Kilo Code Review Runner")
    parser.add_argument(
        "--phase", required=True, help="Phase identifier (e.g. 0, 1, 2, 3, generic)"
    )
    parser.add_argument(
        "--agent",
        default="reviewer",
        help="Kilo specialist role (reviewer, debugger, tester, planner, orchestrator)",
    )
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="Run full multi-agent specialist pipeline for phase",
    )
    parser.add_argument("--model", default=None, help="Custom AI model for Kilo CLI")
    parser.add_argument(
        "--timeout", type=int, default=600, help="Execution timeout in seconds"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument("--output-dir", default=None, help="Custom output directory")

    args = parser.parse_args()
    out_dir = Path(args.output_dir) if args.output_dir else None

    if args.pipeline:
        status, verdict, path = run_kilo_pipeline(
            phase=args.phase,
            timeout_seconds=args.timeout,
            model=args.model,
            verbose=args.verbose,
            output_dir=out_dir,
        )
        print(f"\nPipeline Complete: {verdict} ({status.value})")
        if path:
            print(f"Combined Artifact: {path}")
        sys.exit(KILO_EXIT_CODES.get(status, 1))
    else:
        result = run_single_kilo_agent(
            phase=args.phase,
            agent_role=args.agent,
            timeout_seconds=args.timeout,
            model=args.model,
            verbose=args.verbose,
            output_dir=out_dir,
        )
        print(f"\nReview Complete: {result.verdict_text} ({result.status.value})")
        if result.artifact_path:
            print(f"Artifact Saved: {result.artifact_path}")
        sys.exit(KILO_EXIT_CODES.get(result.status, 1))


if __name__ == "__main__":
    main()
