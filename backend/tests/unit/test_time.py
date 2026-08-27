"""Unit tests for UTC timestamp normalization and utilities."""

from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.domain.time import (
    TimestampValidationError,
    ensure_utc,
    hours_between,
    parse_iso_timestamp,
    to_iso_utc,
)


def test_parse_iso_timestamp_valid_formats() -> None:
    """Verify parsing ISO 8601 strings with Z and offset notations."""
    dt_z = parse_iso_timestamp("2026-08-25T09:30:00Z")
    assert dt_z.tzinfo == UTC
    assert dt_z.year == 2026
    assert dt_z.hour == 9

    dt_offset = parse_iso_timestamp("2026-08-25T15:00:00+05:30")
    assert dt_offset.tzinfo == UTC
    assert dt_offset.hour == 9
    assert dt_offset.minute == 30


def test_parse_iso_timestamp_rejects_date_only() -> None:
    """Verify that date-only strings without time component are strictly rejected."""
    with pytest.raises(TimestampValidationError, match="Date-only timestamp"):
        parse_iso_timestamp("2026-08-25")

    with pytest.raises(TimestampValidationError, match="Date-only timestamp"):
        parse_iso_timestamp("2026-12-31")


def test_parse_iso_timestamp_invalid() -> None:
    """Verify rejection of invalid timestamp formats."""
    with pytest.raises(TimestampValidationError):
        parse_iso_timestamp("invalid-date")
    with pytest.raises(TimestampValidationError):
        parse_iso_timestamp("")
    with pytest.raises(TimestampValidationError):
        parse_iso_timestamp("2026-08-25 25:00:00Z")  # invalid hour
    with pytest.raises(TimestampValidationError):
        parse_iso_timestamp("2026/08/25 10:00:00")


def test_ensure_utc_naive_and_aware() -> None:
    """Verify that naive datetimes are converted to UTC and aware are converted."""
    naive = datetime(2026, 8, 25, 12, 0, 0)
    aware_utc = ensure_utc(naive)
    assert aware_utc.tzinfo == UTC
    assert aware_utc.hour == 12

    ist = timezone(timedelta(hours=5, minutes=30))
    aware_ist = datetime(2026, 8, 25, 17, 30, 0, tzinfo=ist)
    converted = ensure_utc(aware_ist)
    assert converted.tzinfo == UTC
    assert converted.hour == 12


def test_to_iso_utc() -> None:
    """Verify ISO UTC string formatting ends with 'Z'."""
    dt = datetime(2026, 8, 25, 10, 15, 30, tzinfo=UTC)
    assert to_iso_utc(dt) == "2026-08-25T10:15:30Z"


def test_hours_between() -> None:
    """Verify fractional hour difference calculation."""
    t1 = "2026-08-25T10:00:00Z"
    t2 = "2026-08-25T13:30:00Z"
    diff = hours_between(t1, t2)
    assert diff == 3.5
