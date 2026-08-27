"""Timezone-aware timestamp utilities and normalization for METFI."""

import re
from datetime import UTC, datetime

# ISO 8601 regex pattern
ISO_8601_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$"
)


class TimestampValidationError(ValueError):
    """Raised when timestamp parsing or timezone validation fails."""

    pass


def ensure_utc(dt: datetime | str) -> datetime:
    """
    Ensure datetime is timezone-aware and normalized to UTC.

    If given a string, parses ISO 8601.
    If given a naive datetime, assigns UTC with warning/strict policy.
    """
    if isinstance(dt, str):
        return parse_iso_timestamp(dt)

    if not isinstance(dt, datetime):
        raise TimestampValidationError(f"Expected datetime or str, got {type(dt).__name__}")

    if dt.tzinfo is None:
        # Naive datetime: assume UTC
        return dt.replace(tzinfo=UTC)

    # Aware datetime: convert to UTC
    return dt.astimezone(UTC)


DATE_ONLY_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parse_iso_timestamp(ts_str: str) -> datetime:
    """
    Parse an ISO 8601 string into a UTC timezone-aware datetime.

    Date-only strings (e.g. '2026-08-25') are strictly rejected.
    """
    if not isinstance(ts_str, str):
        raise TimestampValidationError(f"Expected timestamp string, got {type(ts_str).__name__}")

    clean_str = ts_str.strip()
    if not clean_str:
        raise TimestampValidationError("Timestamp string cannot be empty.")

    if DATE_ONLY_PATTERN.match(clean_str):
        raise TimestampValidationError(
            f"Date-only timestamp '{ts_str}' is rejected. Expected full ISO 8601 timestamp."
        )

    if not ISO_8601_PATTERN.match(clean_str):
        raise TimestampValidationError(
            f"Invalid ISO 8601 timestamp format '{ts_str}'. Expected ISO 8601 with time/timezone."
        )

    # Handle standard 'Z' suffix
    normalized_str = clean_str.replace("Z", "+00:00")
    if " " in normalized_str and "T" not in normalized_str:
        normalized_str = normalized_str.replace(" ", "T")

    try:
        dt = datetime.fromisoformat(normalized_str)
    except ValueError as e:
        raise TimestampValidationError(f"Invalid ISO 8601 timestamp '{ts_str}': {e}") from e

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    else:
        dt = dt.astimezone(UTC)

    return dt


def to_iso_utc(dt: datetime | str) -> str:
    """Serialize datetime to canonical UTC ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ."""
    utc_dt = ensure_utc(dt)
    # Drop microseconds for canonical display if 0 or keep consistent ISO format
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def hours_between(dt_early: datetime | str, dt_late: datetime | str) -> float:
    """Compute difference in fractional hours between two timestamps."""
    early = ensure_utc(dt_early)
    late = ensure_utc(dt_late)
    diff = (late - early).total_seconds()
    return diff / 3600.0
