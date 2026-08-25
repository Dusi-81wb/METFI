"""Authoritative monetary arithmetic and currency validation for METFI."""

import re
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any

# Standard financial quantization: 2 decimal places with banker/half-up rounding
MONEY_EXPONENT = Decimal("0.01")
STANDARD_ROUNDING = ROUND_HALF_UP

# ISO 4217 uppercase 3-letter currency code pattern
CURRENCY_REGEX = re.compile(r"^[A-Z]{3}$")
SUPPORTED_CURRENCIES = frozenset({"INR", "USD", "EUR", "GBP", "SGD", "AED"})


class MonetaryValidationError(ValueError):
    """Raised when monetary amounts or currencies fail validation rules."""

    pass


def quantize_money(value: Decimal | str | int) -> Decimal:
    """
    Quantize monetary value to exact 2-decimal places using standard ROUND_HALF_UP.

    Rejects binary floats to prevent floating-point precision loss.
    """
    if isinstance(value, float):
        raise MonetaryValidationError(
            f"Binary float {value!r} is prohibited for monetary calculations. "
            "Use Decimal, str, or int."
        )

    try:
        if isinstance(value, (str, int)):
            dec_value = Decimal(str(value).strip())
        elif isinstance(value, Decimal):
            dec_value = value
        else:
            raise MonetaryValidationError(f"Invalid monetary value type: {type(value).__name__}")
    except (InvalidOperation, TypeError) as e:
        raise MonetaryValidationError(f"Cannot parse monetary value '{value}': {e}") from e

    if not dec_value.is_finite():
        raise MonetaryValidationError(f"Monetary value '{value}' must be finite.")

    return dec_value.quantize(MONEY_EXPONENT, rounding=STANDARD_ROUNDING)


def validate_money_amount(
    value: Any,
    allow_negative: bool = False,
    field_name: str = "amount",
) -> Decimal:
    """Validate and quantize monetary amount with sign checks."""
    quantized = quantize_money(value)
    if not allow_negative and quantized < Decimal("0.00"):
        raise MonetaryValidationError(f"{field_name} cannot be negative: {quantized}")
    return quantized


def normalize_currency(currency: str) -> str:
    """Normalize and validate ISO 4217 3-letter currency code."""
    if not isinstance(currency, str):
        raise MonetaryValidationError(f"Currency must be string, got: {type(currency).__name__}")

    normalized = currency.strip().upper()
    if not CURRENCY_REGEX.match(normalized):
        raise MonetaryValidationError(
            f"Invalid currency code format: '{currency}'. Must be 3-letter ISO code."
        )

    return normalized


def is_amount_equal(
    amount_a: Decimal,
    amount_b: Decimal,
    tolerance: Decimal = Decimal("0.00"),
) -> bool:
    """Determine if two Decimal amounts are equal within optional tolerance delta."""
    return abs(amount_a - amount_b) <= tolerance
