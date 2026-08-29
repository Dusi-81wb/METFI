"""Smoke test script for verifying local FastAPI live server startup and API response."""

import subprocess
import sys
import time

import httpx


def test_live_server() -> None:
    print("Starting FastAPI backend server via uvicorn...")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000", "--host", "127.0.0.1"],
        cwd="backend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Poll health endpoint up to 10 seconds
        max_attempts = 20
        connected = False
        data = None

        print("Polling http://127.0.0.1:8000/api/v1/health...")
        for i in range(max_attempts):
            time.sleep(0.5)
            try:
                resp = httpx.get("http://127.0.0.1:8000/api/v1/health", timeout=2.0)
                if resp.status_code == 200:
                    connected = True
                    data = resp.json()
                    print(f"Connection successful on attempt {i+1}!")
            except httpx.RequestError:
                continue

        if not connected:
            print("Failed to connect to backend server within timeout.")
            sys.exit(1)

        print("\n=== Live Health Check Response ===")
        print(f"Status: {data.get('status')}")
        print(f"Service: {data.get('service')}")
        print(f"Version: {data.get('version')}")
        print(f"Environment: {data.get('environment')}")
        print(f"Subsystems: {data.get('subsystems')}")
        print("==================================\n")

        assert data.get("status") == "healthy"
        assert data.get("version") == "0.1.0"
        assert "subsystems" in data

        # Test root endpoint
        root_resp = httpx.get("http://127.0.0.1:8000/", timeout=2.0)
        assert root_resp.status_code == 200
        print("Root endpoint verified successfully!")

        print("\nAll live server smoke tests passed!")

    finally:
        print("Terminating test uvicorn process...")
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
        print("Cleaned up server process.")


if __name__ == "__main__":
    test_live_server()
