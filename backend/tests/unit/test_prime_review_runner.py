"""
Unit tests for the METFI Multi-Agent Phase Review Orchestrator
(scripts/review/run_prime_review.py and kilo_runner.py).

All external WSL, Git, Prime CLI, and Kilo CLI calls are mocked for fast, offline testing.
"""

import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

repo_root = Path(__file__).resolve().parent.parent.parent.parent
scripts_dir = repo_root / "scripts" / "review"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from kilo_capabilities import (  # noqa: E402
    KiloAgentInfo,
    KiloCapabilities,
    get_phase_recommended_agents,
    resolve_kilo_agent,
)
from kilo_runner import (  # noqa: E402
    FindingSeverity,
    KiloFinding,
    KiloReviewStatus,
    format_kilo_review_artifact,
    parse_kilo_findings,
    parse_kilo_verdict,
    run_kilo_pipeline,
    run_single_kilo_agent,
)
from run_prime_review import (  # noqa: E402
    EXIT_CODES,
    ReviewStatus,
    convert_windows_to_wsl_path,
    discover_prime_cli,
    find_repository_root,
    load_phase_prompt,
    parse_prime_verdict,
    run_prime_review,
)


def test_find_repository_root_success() -> None:
    """Verify repository root detection from within project tree."""
    detected_root = find_repository_root()
    assert (detected_root / ".git").exists()
    assert (detected_root / "METFI_MASTER_SPEC_v1.0.md").exists()
    assert (detected_root / "AGENTS.md").exists()


def test_find_repository_root_missing_markers(tmp_path: Path) -> None:
    """Verify explicit FileNotFoundError when repository markers are missing."""
    empty_dir = tmp_path / "non_repo"
    empty_dir.mkdir()
    with pytest.raises(FileNotFoundError, match="Could not locate valid METFI repository root"):
        find_repository_root(start_dir=empty_dir)


def test_convert_windows_to_wsl_path_with_wslpath() -> None:
    """Verify conversion using mocked wslpath."""
    win_path = Path("C:/Users/Samrat/Documents/METFI")
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="/mnt/c/Users/Samrat/Documents/METFI\n",
        )
        wsl_path = convert_windows_to_wsl_path(win_path, distro="Ubuntu")
        assert wsl_path == "/mnt/c/Users/Samrat/Documents/METFI"


def test_convert_windows_to_wsl_path_fallback() -> None:
    """Verify deterministic fallback conversion when wslpath fails."""
    win_path = Path("C:/Users/Samrat/Documents/METFI")
    with patch("subprocess.run", side_effect=subprocess.SubprocessError("WSL not available")):
        wsl_path = convert_windows_to_wsl_path(win_path, distro="Ubuntu")
        assert wsl_path.startswith("/mnt/c/")
        assert "METFI" in wsl_path


def test_discover_prime_cli_explicit() -> None:
    """Verify explicit path is respected directly."""
    res = discover_prime_cli(distro="Ubuntu", explicit_path="/custom/prime-agent")
    assert res == "/custom/prime-agent"


def test_discover_prime_cli_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify PRIME_CLI_PATH environment variable override."""
    monkeypatch.setenv("PRIME_CLI_PATH", "/env/prime-agent")
    res = discover_prime_cli(distro="Ubuntu")
    assert res == "/env/prime-agent"


def test_discover_prime_cli_auto_discovery() -> None:
    """Verify auto-discovery probes candidates."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="0.8.1\n")
        res = discover_prime_cli(distro="Ubuntu")
        assert "prime-agent" in res


def test_discover_prime_cli_not_found() -> None:
    """Verify FileNotFoundError when Prime CLI cannot be found."""
    with patch("subprocess.run", side_effect=subprocess.SubprocessError("Command not found")):
        with pytest.raises(FileNotFoundError, match="Could not discover Prime CLI"):
            discover_prime_cli(distro="Ubuntu")


def test_load_phase_prompt_existing() -> None:
    """Verify loading phase 2 prompt template."""
    content, path = load_phase_prompt(repo_root, "2")
    assert "PHASE 2 ADVERSARIAL AUDIT PROMPT" in content
    assert path.name == "phase_2.md"


def test_load_phase_prompt_generic() -> None:
    """Verify loading generic prompt template."""
    content, path = load_phase_prompt(repo_root, "generic")
    assert "ADVERSARIAL" in content
    assert path.name == "generic.md"


def test_load_phase_prompt_missing() -> None:
    """Verify FileNotFoundError on non-existent phase."""
    with pytest.raises(FileNotFoundError, match="No prompt template found for phase '99'"):
        load_phase_prompt(repo_root, "99")


def test_parse_prime_verdict_pass() -> None:
    """Verify PASS detection."""
    sample = (
        "The audit concluded successfully.\n\n## Final Verdict\n**VERDICT: PASS**\nConfidence: 98%"
    )
    status, text = parse_prime_verdict(sample)
    assert status == ReviewStatus.PASS
    assert text == "PASS"


def test_parse_prime_verdict_pass_with_conditions() -> None:
    """Verify PASS WITH CONDITIONS detection."""
    sample = "Executive Verdict: PASS WITH CONDITIONS\nConfidence: 95%\nFix Ruff issues."
    status, text = parse_prime_verdict(sample)
    assert status == ReviewStatus.PASS_WITH_CONDITIONS
    assert text == "PASS WITH CONDITIONS"


def test_parse_prime_verdict_blocked() -> None:
    """Verify BLOCKED verdict detection."""
    sample = "Critical overfitting detected.\nVERDICT: BLOCKED\nDo not proceed."
    status, text = parse_prime_verdict(sample)
    assert status == ReviewStatus.BLOCKED
    assert text == "BLOCKED"


def test_kilo_role_resolution() -> None:
    """Verify resolution of METFI review roles to Kilo agents."""
    assert resolve_kilo_agent("reviewer") == "ask"
    assert resolve_kilo_agent("debugger") == "debug"
    assert resolve_kilo_agent("planner") == "plan"
    assert resolve_kilo_agent("orchestrator") == "orchestrator"
    assert resolve_kilo_agent("tester") == "ask"
    assert resolve_kilo_agent("ask") == "ask"
    assert resolve_kilo_agent("debug") == "debug"


def test_phase_recommended_agents() -> None:
    """Verify recommended agents per phase."""
    assert "reviewer" in get_phase_recommended_agents("2")
    assert "debugger" in get_phase_recommended_agents("2")
    assert "tester" in get_phase_recommended_agents("2")
    assert "planner" in get_phase_recommended_agents("3")


def test_parse_kilo_findings() -> None:
    """Verify structured parsing of Kilo findings with severities."""
    output = (
        "Analysis complete.\n"
        "CRITICAL: Ground truth leakage detected in test\n"
        "HIGH: Unhandled exception in fee rounding\n"
        "INFO: Variable naming could be improved\n"
    )
    findings = parse_kilo_findings(output, agent="reviewer")
    assert len(findings) == 3
    assert findings[0].severity == FindingSeverity.CRITICAL
    assert "Ground truth leakage" in findings[0].title
    assert findings[1].severity == FindingSeverity.HIGH
    assert findings[2].severity == FindingSeverity.INFO


def test_parse_kilo_verdict_with_critical_finding() -> None:
    """Verify critical finding forces BLOCKED verdict."""
    output = "All tests passed. VERDICT: PASS"
    findings = [
        KiloFinding(
            severity=FindingSeverity.CRITICAL,
            title="Overfitting bug",
            description="Found critical overfitting",
        )
    ]
    status, text = parse_kilo_verdict(output, findings=findings)
    assert status == KiloReviewStatus.BLOCKED
    assert "critical finding" in text


def test_format_kilo_review_artifact(tmp_path: Path) -> None:
    """Verify Kilo review artifact generation format."""
    artifact = format_kilo_review_artifact(
        phase="2",
        timestamp=datetime(2026, 8, 30, 12, 0, 0, tzinfo=UTC),
        repo_root=repo_root,
        agent_role="reviewer",
        resolved_agent="ask",
        command_executed=["kilo", "run", "--agent", "ask"],
        exit_code=0,
        verdict_text="PASS",
        status=KiloReviewStatus.PASS,
        raw_stdout="Review complete. VERDICT: PASS",
        raw_stderr="",
        duration_seconds=5.2,
        kilo_version="7.5.6",
        git_head="head123",
        git_branch="main",
        git_status="M file.py",
        is_fallback=True,
        primary_failure_reason="Prime timeout",
    )

    assert "# KILO CODE REVIEW" in artifact
    assert "FALLBACK REVIEW ACTIVE" in artifact
    assert "Prime — unavailable (Prime timeout)" in artifact
    assert "Agent Role: reviewer" in artifact
    assert "Resolved Kilo Agent: ask" in artifact
    assert "Verdict: PASS (KILO_REVIEW_PASS)" in artifact


def test_run_single_kilo_agent_mock_pass(tmp_path: Path) -> None:
    """Verify single Kilo agent execution with mocked CLI."""
    mock_caps = KiloCapabilities(
        available=True,
        executable="C:/npm/kilo.cmd",
        version="7.5.6",
        agents=[KiloAgentInfo(name="ask", is_primary=True, is_read_only=True)],
        default_agent="ask",
        supported_flags=["--agent", "--dir"],
    )

    with patch("kilo_runner.discover_kilo_capabilities", return_value=mock_caps):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="VERDICT: PASS\nAll domain rules respected.",
                stderr="",
            )
            result = run_single_kilo_agent(
                phase="2",
                agent_role="reviewer",
                repo_root=repo_root,
                output_dir=tmp_path,
                verbose=False,
            )

            assert result.status == KiloReviewStatus.PASS
            assert result.exit_code == 0
            assert result.artifact_path is not None
            assert result.artifact_path.exists()
            content = result.artifact_path.read_text(encoding="utf-8")
            assert "VERDICT: PASS" in content


def test_run_kilo_pipeline_mock(tmp_path: Path) -> None:
    """Verify multi-agent Kilo pipeline execution."""
    mock_caps = KiloCapabilities(
        available=True,
        executable="C:/npm/kilo.cmd",
        version="7.5.6",
        agents=[
            KiloAgentInfo(name="ask", is_primary=True, is_read_only=True),
            KiloAgentInfo(name="debug", is_primary=False, is_read_only=False),
        ],
        default_agent="ask",
        supported_flags=["--agent", "--dir"],
    )

    with patch("kilo_runner.discover_kilo_capabilities", return_value=mock_caps):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="VERDICT: PASS\nRole checks passed.",
                stderr="",
            )
            status, verdict, path = run_kilo_pipeline(
                phase="2",
                repo_root=repo_root,
                output_dir=tmp_path,
                verbose=False,
            )

            assert status == KiloReviewStatus.PASS
            assert "PASS" in verdict
            assert path is not None
            assert path.exists()
            content = path.read_text(encoding="utf-8")
            assert "# METFI PHASE 2 COMBINED SPECIALIST REVIEW" in content


def test_run_prime_review_fallback_on_timeout(tmp_path: Path) -> None:
    """Verify that auto mode executes Kilo fallback when Prime times out."""
    mock_caps = KiloCapabilities(
        available=True,
        executable="C:/npm/kilo.cmd",
        version="7.5.6",
        agents=[KiloAgentInfo(name="ask", is_primary=True, is_read_only=True)],
        default_agent="ask",
        supported_flags=["--agent", "--dir"],
    )

    prime_bin = "/home/samrat/.npm-global/bin/prime-agent"
    with patch("run_prime_review.discover_prime_cli", return_value=prime_bin):
        with patch("kilo_runner.discover_kilo_capabilities", return_value=mock_caps):

            def mock_subproc_side_effect(*args, **kwargs):
                cmd = args[0] if args else kwargs.get("cmd", [])
                cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
                if "prime-agent" in cmd_str:
                    raise subprocess.TimeoutExpired(cmd="wsl.exe", timeout=5)
                # Git or kilo calls succeed
                is_kilo = "kilo" in cmd_str or (
                    isinstance(cmd, list) and len(cmd) > 0 and "kilo" in cmd[0].lower()
                )
                if is_kilo:
                    return MagicMock(
                        returncode=0,
                        stdout="VERDICT: PASS\nFallback review clean.",
                        stderr="",
                    )
                return MagicMock(returncode=0, stdout="main\n", stderr="")

            with patch("subprocess.run", side_effect=mock_subproc_side_effect):
                result = run_prime_review(
                    phase="2",
                    engine="auto",
                    output_dir=tmp_path,
                    timeout_seconds=5,
                )

                assert result.status == ReviewStatus.FALLBACK_REVIEW
                assert "FALLBACK_REVIEW" in result.verdict_text
                assert result.exit_code == 0
                assert result.artifact_path is not None
                assert result.artifact_path.exists()
                content = result.artifact_path.read_text(encoding="utf-8")
                assert "FALLBACK REVIEW ACTIVE" in content


def test_exit_codes_mapping() -> None:
    """Verify exit code contract."""
    assert EXIT_CODES[ReviewStatus.PASS] == 0
    assert EXIT_CODES[ReviewStatus.PASS_WITH_CONDITIONS] == 2
    assert EXIT_CODES[ReviewStatus.BLOCKED] == 3
    assert EXIT_CODES[ReviewStatus.TIMEOUT] == 4
    assert EXIT_CODES[ReviewStatus.EXECUTION_FAILURE] == 5
    assert EXIT_CODES[ReviewStatus.FALLBACK_REVIEW] == 0
    assert EXIT_CODES[ReviewStatus.CONFLICT] == 7
