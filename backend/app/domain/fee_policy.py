"""Configurable fee and tax policy model for deterministic financial reconciliation."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.money import quantize_money

UNSET_POLICY = object()


class FeeTaxPolicy(BaseModel):
    """
    Explicit, configurable fee and tax policy for gateway settlements.

    Encapsulates contract fee rates, tax rates on fees (e.g. GST), applicable
    currencies/providers, and deterministic deduction calculation rules.
    """

    model_config = ConfigDict(frozen=True)

    fee_rate: Decimal = Field(
        default=Decimal("0.02"),
        description="Gateway contract fee rate as a decimal (e.g. 0.02 for 2.0%)",
    )
    tax_rate_on_fee: Decimal = Field(
        default=Decimal("0.18"),
        description="Applicable tax rate on gateway processing fee (e.g. 0.18 for 18% GST)",
    )
    currency: str | None = Field(
        default=None,
        description="Applicable ISO 4217 currency code or None for multi-currency applicability",
    )
    provider: str | None = Field(
        default=None,
        description="Applicable payment gateway / acquirer provider name or None",
    )
    rounding_rule: str = Field(
        default="ROUND_HALF_UP",
        description="Decimal rounding mode for fee and tax calculations",
    )

    def calculate_expected_fee(self, gross_amount: Decimal) -> Decimal:
        """Compute expected gateway fee quantized to standard 2-decimal precision."""
        return quantize_money(gross_amount * self.fee_rate)

    def calculate_expected_tax(self, fee_amount: Decimal) -> Decimal:
        """Compute expected tax on fee quantized to standard 2-decimal precision."""
        return quantize_money(fee_amount * self.tax_rate_on_fee)

    def calculate_expected_deductions(
        self, gross_amount: Decimal
    ) -> tuple[Decimal, Decimal, Decimal]:
        """
        Compute (expected_fee, expected_tax, total_expected_deductions).
        """
        fee = self.calculate_expected_fee(gross_amount)
        tax = self.calculate_expected_tax(fee)
        total = quantize_money(fee + tax)
        return fee, tax, total

    def calculate_expected_settled_amount(self, gross_amount: Decimal) -> Decimal:
        """Compute expected net settled amount after contract deductions."""
        _, _, total_deductions = self.calculate_expected_deductions(gross_amount)
        return quantize_money(gross_amount - total_deductions)
