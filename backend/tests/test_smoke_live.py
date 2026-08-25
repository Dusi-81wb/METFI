"""Pytest smoke test verifying live FastAPI server lifecycle."""

import subprocess
import sys
import time

import httpx
import pytest


@pytest.mark.smoke
def test_live_server_smoke_startup() -> None:
    """Verify that the FastAPI application starts via uvicorn and answers health requests."""
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8015", "--host", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        max_attempts = 20
        connected = False
        data = None

        for _ in range(max_attempts):
            time.sleep(0.3)
            try:
                resp = httpx.get("http://127.0.0.1:8015/api/v1/health", timeout=1.0)
                if resp.status_code == 200:
                    connected = True
                    data = resp.json()
                    break
            except Exception:
                pass

        if not connected:
            stdout, stderr = proc.communicate(timeout=2)
            print(f"Uvicorn stdout: {stdout}")
            print(f"Uvicorn stderr: {stderr}")

        assert connected, "Live server failed to respond within timeout."
        assert data is not None
        assert data.get("version") == "0.1.0"
        assert "subsystems" in data

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except Exception:
            proc.kill()
