"""Invariant tests verifying mathematical and structural integrity of generated data."""

from decimal import Decimal

from app.domain.enums import PaymentStatus, SettlementStatus
from app.domain.money import CURRENCY_REGEX
from app.domain.time import ISO_8601_PATTERN
from app.services.data_generator import SyntheticFinancialGenerator


def test_data_invariants_dev_dataset() -> None:
    """Verify integrity invariants on standard 500-record dataset."""
    gen = SyntheticFinancialGenerator(seed=42)
    res = gen.generate(size=500, dataset_id="invariant_test_500")

    payment_ids = set()
    order_ids = set()

    for p in res.payments:
        # Unique payment IDs
        assert p.payment_id not in payment_ids
        payment_ids.add(p.payment_id)
        order_ids.add(p.order_id)

        # Amount invariants
        assert p.amount > Decimal("0.00")
        assert p.amount.as_tuple().exponent == -2
        assert CURRENCY_REGEX.match(p.currency)

        # Timestamp format
        assert ISO_8601_PATTERN.match(str(p.payment_timestamp))

        # Status
        assert p.status in [s.value for s in PaymentStatus]

    for s in res.settlements:
        assert s.settled_amount >= Decimal("0.00")
        assert s.settled_amount.as_tuple().exponent == -2
        assert s.fee >= Decimal("0.00")
        assert s.fee_tax >= Decimal("0.00")
        assert CURRENCY_REGEX.match(s.currency)
        assert ISO_8601_PATTERN.match(str(s.settlement_timestamp))
        assert s.status in [st.value for st in SettlementStatus]

    for le in res.ledger_entries:
        assert le.debit >= Decimal("0.00")
        assert le.credit >= Decimal("0.00")
        assert not (le.debit == Decimal("0.00") and le.credit == Decimal("0.00"))
        assert CURRENCY_REGEX.match(le.currency)
        assert ISO_8601_PATTERN.match(str(le.entry_timestamp))
