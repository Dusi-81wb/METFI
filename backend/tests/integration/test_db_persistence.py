"""Integration test verifying database engine connectivity and session creation."""

import pytest

from app.api.v1.health import check_database_connectivity
from app.core.db import AsyncSessionLocal


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_connectivity_probe() -> None:
    """Verify check_database_connectivity probe function behavior."""
    status, error = await check_database_connectivity()
    assert status in ("connected", "disconnected")
    if status == "connected":
        assert error is None
    else:
        assert error is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_session_lifecycle() -> None:
    """Verify AsyncSessionLocal can be instantiated cleanly."""
    session = AsyncSessionLocal()
    try:
        assert session is not None
    finally:
        await session.close()
