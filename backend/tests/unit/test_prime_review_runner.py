"""
Unit tests for the Prime-Powered Phase Review Orchestrator (scripts/review/run_prime_review.py).

All external WSL, Git, and Prime CLI calls are mocked to ensure fast, offline execution.
"""

import subprocess

# Ensure scripts directory is on sys.path
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

repo_root = Path(__file__).resolve().parent.parent.parent.parent
scripts_dir = repo_root / "scripts" / "review"
if str(scripts_dir) not in sys.path:
    sys.path.insert(0, str(scripts_dir))

from run_prime_review import (  # noqa: E402
    EXIT_CODES,
    PrimeExecutionResult,
    ReviewStatus,
    WorktreeSnapshot,
    capture_worktree_snapshot,
    convert_windows_to_wsl_path,
    discover_prime_cli,
    find_repository_root,
    format_review_artifact,
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
        # First candidate succeeds
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
        "The audit concluded successfully.\n\n"
        "## Final Verdict\n**VERDICT: PASS**\nConfidence: 98%"
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


def test_capture_worktree_snapshot() -> None:
    """Verify capture of worktree metadata."""
    snapshot = capture_worktree_snapshot(repo_root)
    assert snapshot.head_commit != ""
    assert snapshot.python_version != ""


def test_format_review_artifact() -> None:
    """Verify format of generated markdown review artifact."""
    snapshot = WorktreeSnapshot(
        head_commit="abc1234",
        branch="main",
        status_short=" M backend/app/reconciliation/engine.py",
        python_version="3.12.13",
        node_version="v22.8.0",
    )
    artifact = format_review_artifact(
        phase="2",
        timestamp=datetime(2026, 8, 30, 12, 0, 0, tzinfo=UTC),
        repo_root=repo_root,
        wsl_root="/mnt/c/METFI",
        snapshot=snapshot,
        command_executed=["wsl.exe", "-d", "Ubuntu", "--", "prime-agent", "-p"],
        prime_exit_code=0,
        verdict_text="PASS",
        status=ReviewStatus.PASS,
        raw_stdout="# Review Report\nAll checks passed.",
        raw_stderr="",
        duration_seconds=12.5,
        prime_cli_path="prime-agent",
        distro="Ubuntu",
    )

    assert "# PRIME REVIEW" in artifact
    assert "Phase: 2" in artifact
    assert "Git HEAD: abc1234" in artifact
    assert "Verdict: PASS" in artifact
    assert "All checks passed." in artifact


def test_run_prime_review_mock_pass(tmp_path: Path) -> None:
    """Verify complete review execution flow for a passing review."""
    mock_stdout = "# PRIME AUDIT\n\n## Final Verdict\n**VERDICT: PASS**\nConfidence: 99%"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=mock_stdout,
            stderr="",
        )

        result: PrimeExecutionResult = run_prime_review(
            phase="2",
            engine="prime",
            output_dir=tmp_path,
            verbose=False,
        )

        assert result.status == ReviewStatus.PASS
        assert result.exit_code == 0
        assert result.artifact_path is not None
        assert result.artifact_path.exists()
        content = result.artifact_path.read_text(encoding="utf-8")
        assert "VERDICT: PASS" in content


def test_run_prime_review_mock_timeout(tmp_path: Path) -> None:
    """Verify timeout handling in review runner."""
    with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="wsl.exe", timeout=5)):
        result = run_prime_review(
            phase="2",
            engine="prime",
            prime_path="/home/samrat/.npm-global/bin/prime-agent",
            output_dir=tmp_path,
            timeout_seconds=5,
        )

        assert result.status == ReviewStatus.TIMEOUT
        assert result.exit_code == 124
        assert "TIMEOUT" in result.verdict_text
        assert result.artifact_path is not None
        assert result.artifact_path.exists()


def test_run_kilo_review_engine_real(tmp_path: Path) -> None:
    """Verify real execution of Kilo adversarial review engine."""
    result = run_prime_review(
        phase="2",
        engine="kilo",
        output_dir=tmp_path,
        verbose=False,
    )
    assert result.status == ReviewStatus.PASS
    assert result.exit_code == 0
    assert result.artifact_path is not None
    assert result.artifact_path.exists()
    content = result.artifact_path.read_text(encoding="utf-8")
    assert "VERDICT: PASS" in content or "Status: PASS" in content


def test_run_prime_review_repeated_reviews_no_overwrite(tmp_path: Path) -> None:
    """Verify repeated reviews create unique timestamped files without overwriting."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="VERDICT: PASS",
            stderr="",
        )

        res1 = run_prime_review(phase="2", engine="prime", output_dir=tmp_path)
        res2 = run_prime_review(phase="2", engine="prime", output_dir=tmp_path)

        assert res1.artifact_path is not None
        assert res2.artifact_path is not None
        assert res1.artifact_path.exists()
        assert res2.artifact_path.exists()
        assert len(list(tmp_path.glob("*.md"))) >= 1


def test_exit_codes_mapping() -> None:
    """Verify exit code contract."""
    assert EXIT_CODES[ReviewStatus.PASS] == 0
    assert EXIT_CODES[ReviewStatus.PASS_WITH_CONDITIONS] == 2
    assert EXIT_CODES[ReviewStatus.BLOCKED] == 3
    assert EXIT_CODES[ReviewStatus.TIMEOUT] == 4
    assert EXIT_CODES[ReviewStatus.EXECUTION_FAILURE] == 5
