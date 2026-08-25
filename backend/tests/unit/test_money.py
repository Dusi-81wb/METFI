"""Unit tests for exact monetary arithmetic and currency validation."""

from decimal import Decimal

import pytest

from app.domain.money import (
    MonetaryValidationError,
    is_amount_equal,
    normalize_currency,
    quantize_money,
    validate_money_amount,
)


def test_quantize_money_valid_types() -> None:
    """Verify quantize_money with Decimal, string, and integer inputs."""
    assert quantize_money(Decimal("123.456")) == Decimal("123.46")
    assert quantize_money("123.454") == Decimal("123.45")
    assert quantize_money(100) == Decimal("100.00")
    assert quantize_money("  500.50  ") == Decimal("500.50")


def test_quantize_money_rejects_float() -> None:
    """Verify that binary floating point inputs are strictly rejected."""
    with pytest.raises(MonetaryValidationError, match="Binary float .* is prohibited"):
        quantize_money(123.45)


def test_quantize_money_rejects_invalid_strings() -> None:
    """Verify that unparseable monetary strings raise validation error."""
    with pytest.raises(MonetaryValidationError, match="Cannot parse monetary value"):
        quantize_money("not_a_number")


def test_validate_money_amount_negative_checks() -> None:
    """Verify that negative amounts are rejected unless explicitly allowed."""
    with pytest.raises(MonetaryValidationError, match="amount cannot be negative"):
        validate_money_amount("-10.00", allow_negative=False)

    # Allowed negative
    assert validate_money_amount("-10.00", allow_negative=True) == Decimal("-10.00")


def test_normalize_currency_valid_iso() -> None:
    """Verify ISO 4217 currency normalization."""
    assert normalize_currency("inr") == "INR"
    assert normalize_currency(" USD ") == "USD"
    assert normalize_currency("eur") == "EUR"


def test_normalize_currency_invalid_codes() -> None:
    """Verify rejection of invalid currency code formats."""
    with pytest.raises(MonetaryValidationError, match="Invalid currency code format"):
        normalize_currency("US")
    with pytest.raises(MonetaryValidationError, match="Invalid currency code format"):
        normalize_currency("USDD")
    with pytest.raises(MonetaryValidationError, match="Invalid currency code format"):
        normalize_currency("123")


def test_is_amount_equal_with_tolerance() -> None:
    """Verify decimal equality checks with tolerance."""
    a = Decimal("100.00")
    b = Decimal("100.00")
    c = Decimal("100.05")

    assert is_amount_equal(a, b)
    assert not is_amount_equal(a, c)
    assert is_amount_equal(a, c, tolerance=Decimal("0.10"))
