"""
Application service coordinating normalization and deterministic batch reconciliation execution.
"""

import json
from pathlib import Path

from app.domain.canonical import (
    CanonicalLedgerEntry,
    CanonicalPayment,
    CanonicalSettlement,
)
from app.domain.fee_policy import FeeTaxPolicy, UNSET_POLICY
from app.domain.normalizer import (
    normalize_ledger,
    normalize_payment,
    normalize_settlement,
)
from app.domain.raw_models import (
    RawLedgerRecord,
    RawPaymentRecord,
    RawSettlementRecord,
)
from app.domain.reconciliation_result import BatchReconciliationResult
from app.domain.sanitization import validate_dataset_id
from app.reconciliation.engine import DeterministicReconciliationEngine


def _find_generated_root() -> Path:
    candidates = [
        Path.cwd() / "data" / "generated",
        Path.cwd().parent / "data" / "generated",
        Path(__file__).resolve().parent.parent.parent.parent / "data" / "generated",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


class ReconciliationService:
    """Service layer coordinating batch ingestion, normalization, and reconciliation."""

    def __init__(self, engine: DeterministicReconciliationEngine | None = None) -> None:
        self.engine = engine or DeterministicReconciliationEngine()

    def reconcile_from_disk(
        self,
        dataset_id: str,
        base_dir: str | Path | None = None,
        policy: FeeTaxPolicy | None | object = UNSET_POLICY,
    ) -> BatchReconciliationResult:
        """
        Load inference records from data/generated/<dataset_id>/input/, normalize, and reconcile.

        Guarantees:
        - NEVER accesses ground truth files.
        - Validates dataset_id to prevent path traversal.
        """
        valid_id = validate_dataset_id(dataset_id)
        root = Path(base_dir) if base_dir else _find_generated_root()
        input_dir = root / valid_id / "input"

        if not input_dir.exists():
            raise FileNotFoundError(f"Dataset input directory does not exist: {input_dir}")

        with open(input_dir / "payments.json", encoding="utf-8") as f:
            raw_payments = json.load(f)

        with open(input_dir / "settlements.json", encoding="utf-8") as f:
            raw_settlements = json.load(f)

        with open(input_dir / "ledger.json", encoding="utf-8") as f:
            raw_ledger = json.load(f)

        # Normalize feeds
        canonical_payments = [
            normalize_payment(RawPaymentRecord.model_validate(p)) for p in raw_payments
        ]
        canonical_settlements = [
            normalize_settlement(RawSettlementRecord.model_validate(s)) for s in raw_settlements
        ]
        canonical_ledger = [
            normalize_ledger(RawLedgerRecord.model_validate(le)) for le in raw_ledger
        ]

        return self.engine.reconcile_batch(
            payments=canonical_payments,
            settlements=canonical_settlements,
            ledger_entries=canonical_ledger,
            dataset_id=valid_id,
            policy=policy,
        )

    def reconcile_records(
        self,
        raw_payments: list[dict],
        raw_settlements: list[dict],
        raw_ledger: list[dict],
        dataset_id: str = "custom_payload",
        policy: FeeTaxPolicy | None | object = UNSET_POLICY,
    ) -> BatchReconciliationResult:
        """
        Normalize and reconcile in-memory raw records.
        """
        canonical_payments: list[CanonicalPayment] = [
            normalize_payment(RawPaymentRecord.model_validate(p)) for p in raw_payments
        ]
        canonical_settlements: list[CanonicalSettlement] = [
            normalize_settlement(RawSettlementRecord.model_validate(s)) for s in raw_settlements
        ]
        canonical_ledger: list[CanonicalLedgerEntry] = [
            normalize_ledger(RawLedgerRecord.model_validate(le)) for le in raw_ledger
        ]

        return self.engine.reconcile_batch(
            payments=canonical_payments,
            settlements=canonical_settlements,
            ledger_entries=canonical_ledger,
            dataset_id=dataset_id,
            policy=policy,
        )
