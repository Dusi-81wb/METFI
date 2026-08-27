"""Deterministic synthetic financial dataset generator and ground-truth isolator."""

import hashlib
import json
import random
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from app.domain.corruption import CORRUPTION_OPERATORS
from app.domain.enums import (
    ExceptionType,
    LedgerAccount,
    LedgerStatus,
    PaymentStatus,
    SettlementStatus,
)
from app.domain.ground_truth import (
    DatasetManifest,
    GroundTruthRecord,
)
from app.domain.identifiers import generate_opaque_id
from app.domain.money import quantize_money
from app.domain.raw_models import (
    RawLedgerRecord,
    RawPaymentRecord,
    RawSettlementRecord,
)
from app.domain.sanitization import validate_dataset_id
from app.domain.time import to_iso_utc

# Canonical distribution targets covering all 10 exception classes summing to exactly 1.000 (100%)
DEFAULT_DISTRIBUTION: dict[ExceptionType, float] = {
    ExceptionType.EXACT_MATCH: 0.60,
    ExceptionType.AMOUNT_MISMATCH: 0.10,
    ExceptionType.MISSING_SETTLEMENT: 0.06,
    ExceptionType.DUPLICATE_RECORD: 0.05,
    ExceptionType.DATE_MISMATCH: 0.05,
    ExceptionType.REFERENCE_MISMATCH: 0.04,
    ExceptionType.PARTIAL_SETTLEMENT: 0.03,
    ExceptionType.FEE_DISCREPANCY: 0.02,
    ExceptionType.CURRENCY_MISMATCH: 0.025,
    ExceptionType.AMBIGUOUS: 0.025,
}

GENERATOR_VERSION = "1.0.1"
SCHEMA_VERSION = "1.0.0"


class GeneratedDatasetResult:
    """Encapsulates generated input records, isolated ground truth, and audit manifests."""

    def __init__(
        self,
        dataset_id: str,
        seed: int,
        payments: list[RawPaymentRecord],
        settlements: list[RawSettlementRecord],
        ledger_entries: list[RawLedgerRecord],
        ground_truth: list[GroundTruthRecord],
        manifest: DatasetManifest,
    ) -> None:
        self.dataset_id = dataset_id
        self.seed = seed
        self.payments = payments
        self.settlements = settlements
        self.ledger_entries = ledger_entries
        self.ground_truth = ground_truth
        self.manifest = manifest


class SyntheticFinancialGenerator:
    """Deterministic generator for multi-source financial reconciliation datasets."""

    def __init__(
        self,
        seed: int = 42,
        distribution: dict[ExceptionType, float] | None = None,
    ) -> None:
        self.seed = seed
        self.rng = random.Random(seed)
        raw_dist = distribution or DEFAULT_DISTRIBUTION
        total_weight = sum(raw_dist.values())
        # Normalize weights so they sum to 1.0
        self.distribution = {k: v / total_weight for k, v in raw_dist.items()}

    def _allocate_class_counts(self, total_size: int) -> dict[ExceptionType, int]:
        """
        Deterministically allocate integer counts per class summing exactly to total_size
        using the Largest Remainder Method (Hamilton-Hare quota algorithm).
        """
        exact_counts = {cls: total_size * fraction for cls, fraction in self.distribution.items()}
        integer_counts = {cls: int(exact_counts[cls]) for cls in self.distribution}
        remainders = {cls: exact_counts[cls] - integer_counts[cls] for cls in self.distribution}

        remaining = total_size - sum(integer_counts.values())
        # Sort classes by largest remainder, breaking ties deterministically by class value
        sorted_by_remainder = sorted(
            remainders.keys(), key=lambda cls: (-remainders[cls], cls.value)
        )
        for i in range(remaining):
            cls = sorted_by_remainder[i % len(sorted_by_remainder)]
            integer_counts[cls] += 1

        return integer_counts

    def _generate_baseline_transaction(
        self, idx: int, base_time: datetime
    ) -> tuple[RawPaymentRecord, RawSettlementRecord, list[RawLedgerRecord]]:
        """Generate an internally coherent, perfect 3-way financial transaction."""
        order_id = generate_opaque_id("ord", self.seed, "order", idx)
        payment_id = generate_opaque_id("pay", self.seed, "payment", idx)
        settlement_id = generate_opaque_id("set", self.seed, "settlement", idx)
        ledger_id_dr = generate_opaque_id("led", self.seed, "ledger_dr", idx)
        ledger_id_cr = generate_opaque_id("led", self.seed, "ledger_cr", idx)
        customer_id = generate_opaque_id("cust", self.seed, "customer", idx)
        jv_id = generate_opaque_id("jv", self.seed, "voucher", idx).upper()

        # Amount between 100.00 and 15,000.00 INR
        raw_amt = self.rng.randint(100, 15000)
        cents = self.rng.choice([0, 50, 99, 25, 75])
        amount = quantize_money(Decimal(f"{raw_amt}.{cents:02d}"))
        currency = "INR"

        # Timestamp: staggered by index within past 30 days
        payment_dt = base_time + timedelta(minutes=idx * 7)
        payment_ts = to_iso_utc(payment_dt)

        # Standard fee: 2% + 18% GST on fee
        fee = quantize_money(amount * Decimal("0.02"))
        fee_tax = quantize_money(fee * Decimal("0.18"))
        settled_amount = quantize_money(amount - fee - fee_tax)

        # Settlement occurs 24h later
        settlement_dt = payment_dt + timedelta(hours=self.rng.randint(12, 36))
        settlement_ts = to_iso_utc(settlement_dt)

        # Raw Payment
        payment = RawPaymentRecord(
            payment_id=payment_id,
            order_id=order_id,
            customer_id=customer_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.SUCCESS.value,
            payment_timestamp=payment_ts,
            metadata={"payment_method": self.rng.choice(["upi", "card", "netbanking"])},
        )

        # Raw Settlement
        settlement = RawSettlementRecord(
            settlement_id=settlement_id,
            payment_id=payment_id,
            settled_amount=settled_amount,
            currency=currency,
            settlement_timestamp=settlement_ts,
            fee=fee,
            fee_tax=fee_tax,
            status=SettlementStatus.SETTLED.value,
            metadata={"acquirer": self.rng.choice(["HDFC", "ICICI", "AXIS", "SBIN"])},
        )

        # Raw Ledger entries (Double entry: Accounts Receivable and Clearing)
        ledger_dr = RawLedgerRecord(
            ledger_id=ledger_id_dr,
            order_id=order_id,
            debit=amount,
            credit=Decimal("0.00"),
            currency=currency,
            entry_timestamp=payment_ts,
            account=LedgerAccount.PAYMENT_GATEWAY_CLEARING.value,
            status=LedgerStatus.POSTED.value,
            metadata={"journal_voucher": jv_id},
        )
        ledger_cr = RawLedgerRecord(
            ledger_id=ledger_id_cr,
            order_id=order_id,
            debit=Decimal("0.00"),
            credit=amount,
            currency=currency,
            entry_timestamp=payment_ts,
            account=LedgerAccount.ACCOUNTS_RECEIVABLE.value,
            status=LedgerStatus.POSTED.value,
            metadata={"journal_voucher": jv_id},
        )

        return payment, settlement, [ledger_dr, ledger_cr]

    def generate(self, size: int = 500, dataset_id: str = "dev_500") -> GeneratedDatasetResult:
        """
        Generate complete dataset with controlled corruption distribution.

        Guarantees:
        - Deterministic output for same seed and size.
        - Exact class counts matching distribution.
        - Isolated ground truth metadata.
        """
        base_time = datetime(2026, 8, 1, 0, 0, 0, tzinfo=UTC)
        allocated_counts = self._allocate_class_counts(size)

        # Create class plan and shuffle with deterministic RNG
        class_plan: list[ExceptionType] = []
        for cls, count in allocated_counts.items():
            class_plan.extend([cls] * count)
        self.rng.shuffle(class_plan)

        all_payments: list[RawPaymentRecord] = []
        all_settlements: list[RawSettlementRecord] = []
        all_ledger_entries: list[RawLedgerRecord] = []
        all_ground_truth: list[GroundTruthRecord] = []
        actual_class_distribution: dict[str, int] = {cls.value: 0 for cls in ExceptionType}

        for idx, target_class in enumerate(class_plan):
            payment, settlement, ledger_entries = self._generate_baseline_transaction(
                idx, base_time
            )
            operator = CORRUPTION_OPERATORS[target_class]
            bundle = operator(payment, settlement, ledger_entries, self.rng)

            case_id = generate_opaque_id("case", self.seed, "case", idx)
            order_id = payment.order_id

            if bundle.payment:
                all_payments.append(bundle.payment)
            all_settlements.extend(bundle.settlements)
            all_ledger_entries.extend(bundle.ledger_entries)

            gt_record = GroundTruthRecord(
                case_id=case_id,
                order_id=order_id,
                expected_classification=bundle.expected_classification,
                expected_policy_outcome=bundle.expected_policy_outcome,
                payment_id=bundle.payment.payment_id if bundle.payment else None,
                settlement_id=bundle.settlements[0].settlement_id if bundle.settlements else None,
                ledger_ids=[le.ledger_id for le in bundle.ledger_entries],
                expected_amount_delta=bundle.expected_amount_delta,
                injected_fault=bundle.fault,
                is_synthetic=True,
            )
            all_ground_truth.append(gt_record)
            actual_class_distribution[bundle.expected_classification.value] += 1

        # Build audit manifest
        manifest = DatasetManifest(
            dataset_id=dataset_id,
            generator_version=GENERATOR_VERSION,
            schema_version=SCHEMA_VERSION,
            seed=self.seed,
            record_count=size,
            generation_timestamp=datetime.now(UTC).isoformat(),
            source_counts={
                "payments": len(all_payments),
                "settlements": len(all_settlements),
                "ledger_entries": len(all_ledger_entries),
            },
            class_distribution=actual_class_distribution,
        )

        return GeneratedDatasetResult(
            dataset_id=dataset_id,
            seed=self.seed,
            payments=all_payments,
            settlements=all_settlements,
            ledger_entries=all_ledger_entries,
            ground_truth=all_ground_truth,
            manifest=manifest,
        )


def _compute_sha256(file_path: Path) -> str:
    """Compute SHA256 hex digest of file contents."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def export_dataset(
    result: GeneratedDatasetResult, base_dir: Path | str | None = None
) -> dict[str, Path]:
    """
    Export generated dataset enforcing strict physical isolation:
    - Inference input files saved to data/generated/<dataset_id>/input/
    - Ground truth files saved to data/ground_truth/<dataset_id>/
    """
    validated_id = validate_dataset_id(result.dataset_id)
    root_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parents[3] / "data"
    input_dir = root_dir / "generated" / validated_id / "input"
    gt_dir = root_dir / "ground_truth" / validated_id

    input_dir.mkdir(parents=True, exist_ok=True)
    gt_dir.mkdir(parents=True, exist_ok=True)

    # 1. Write Input Files (ZERO ground truth labels present)
    payments_path = input_dir / "payments.json"
    settlements_path = input_dir / "settlements.json"
    ledger_path = input_dir / "ledger.json"
    input_manifest_path = input_dir / "manifest.json"

    with open(payments_path, "w", encoding="utf-8") as f:
        json.dump([p.model_dump(mode="json") for p in result.payments], f, indent=2)

    with open(settlements_path, "w", encoding="utf-8") as f:
        json.dump([s.model_dump(mode="json") for s in result.settlements], f, indent=2)

    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump([le.model_dump(mode="json") for le in result.ledger_entries], f, indent=2)

    # Input manifest includes only metadata and record counts (NO class distribution)
    input_manifest_payload = {
        "dataset_id": result.dataset_id,
        "generator_version": result.manifest.generator_version,
        "schema_version": result.manifest.schema_version,
        "seed": result.manifest.seed,
        "record_count": result.manifest.record_count,
        "source_counts": result.manifest.source_counts,
        "generation_timestamp": result.manifest.generation_timestamp,
    }
    with open(input_manifest_path, "w", encoding="utf-8") as f:
        json.dump(input_manifest_payload, f, indent=2)

    # 2. Write Isolated Ground Truth Files
    gt_path = gt_dir / "ground_truth.json"
    gt_manifest_path = gt_dir / "manifest.json"

    with open(gt_path, "w", encoding="utf-8") as f:
        json.dump([gt.model_dump(mode="json") for gt in result.ground_truth], f, indent=2)

    # Compute checksums
    checksums = {
        "payments_sha256": _compute_sha256(payments_path),
        "settlements_sha256": _compute_sha256(settlements_path),
        "ledger_sha256": _compute_sha256(ledger_path),
        "ground_truth_sha256": _compute_sha256(gt_path),
    }
    manifest_dict = result.manifest.model_dump(mode="json")
    manifest_dict["checksums"] = checksums

    with open(gt_manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_dict, f, indent=2)

    return {
        "payments": payments_path,
        "settlements": settlements_path,
        "ledger": ledger_path,
        "input_manifest": input_manifest_path,
        "ground_truth": gt_path,
        "gt_manifest": gt_manifest_path,
    }
