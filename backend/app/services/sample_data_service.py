"""Service providing operational sample dataset inspection and on-demand randomized generation."""

import json
import random
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any

from app.schemas.data import (
    DatasetMetadata,
    RandomGenerationRequest,
    RandomGenerationResponse,
    SampleDataResponse,
)


class SampleDataService:
    """Provides access to actual demo fixtures and synthesizes temperature-controlled test cases."""

    def __init__(self, repo_root: Path | None = None) -> None:
        if repo_root is None:
            # Anchor to backend/.. directory
            self.repo_root = Path(__file__).resolve().parents[3]
        else:
            self.repo_root = repo_root

        self.generated_dir = self.repo_root / "data" / "generated"
        self.fixtures_dir = self.repo_root / "data" / "fixtures"

    def get_available_datasets(self) -> list[DatasetMetadata]:
        """List all available demo and reference datasets."""
        datasets: list[DatasetMetadata] = []

        # 1. dev_500 primary benchmark dataset
        dev_dir = self.generated_dir / "dev_500" / "input"
        if dev_dir.exists():
            p_count, s_count, l_count, size_kb = self._get_feed_metrics(dev_dir)
            datasets.append(
                DatasetMetadata(
                    dataset_id="dev_500",
                    name="Production Sample Batch (500 Transactions)",
                    description=(
                        "Standard operational day batch containing exact matches, "
                        "fee discrepancies, and timing delays."
                    ),
                    payments_count=p_count,
                    settlements_count=s_count,
                    ledger_count=l_count,
                    total_records=p_count + s_count + l_count,
                    file_size_kb=size_kb,
                    is_live_fixture=True,
                )
            )

        # 2. Showcase Primary Case Fixtures
        datasets.append(
            DatasetMetadata(
                dataset_id="case_demo_101",
                name="Fee Discrepancy Case (case_demo_101)",
                description=(
                    "Multi-source fee variance case (-₹50.00 fee discrepancy, 0.5% schedule)."
                ),
                payments_count=1,
                settlements_count=1,
                ledger_count=2,
                total_records=4,
                file_size_kb=3.2,
                is_live_fixture=True,
            )
        )
        datasets.append(
            DatasetMetadata(
                dataset_id="case_demo_102",
                name="Timing SLA Breach Case (case_demo_102)",
                description=(
                    "Settlement payout delayed beyond 48-hour SLA window (58h transit lag)."
                ),
                payments_count=1,
                settlements_count=1,
                ledger_count=2,
                total_records=4,
                file_size_kb=3.1,
                is_live_fixture=True,
            )
        )
        datasets.append(
            DatasetMetadata(
                dataset_id="case_demo_103",
                name="Missing Settlement Case (case_demo_103)",
                description=(
                    "Unsettled gateway payment with zero bank payout record (-₹18,200.00 leakage)."
                ),
                payments_count=1,
                settlements_count=0,
                ledger_count=2,
                total_records=3,
                file_size_kb=2.8,
                is_live_fixture=True,
            )
        )

        # 3. stress_5000 scale dataset if available
        stress_dir = self.generated_dir / "stress_5000" / "input"
        if stress_dir.exists():
            p_count, s_count, l_count, size_kb = self._get_feed_metrics(stress_dir)
            datasets.append(
                DatasetMetadata(
                    dataset_id="stress_5000",
                    name="High-Volume Scale Batch (5,000 Transactions)",
                    description="Stress-testing dataset for high-throughput reconciliation.",
                    payments_count=p_count,
                    settlements_count=s_count,
                    ledger_count=l_count,
                    total_records=p_count + s_count + l_count,
                    file_size_kb=size_kb,
                    is_live_fixture=False,
                )
            )

        # 4. Adversarial Edge Suite
        adv_file = self.fixtures_dir / "adversarial_evaluation_dataset.json"
        if adv_file.exists():
            datasets.append(
                DatasetMetadata(
                    dataset_id="adversarial_24",
                    name="Adversarial Edge Test Suite (24 Cases)",
                    description="Edge cases covering Unicode and timestamp boundaries.",
                    payments_count=24,
                    settlements_count=24,
                    ledger_count=48,
                    total_records=96,
                    file_size_kb=18.5,
                    is_live_fixture=False,
                )
            )

        return datasets

    def get_sample_data(
        self,
        dataset_id: str = "dev_500",
        source: str = "all",
        offset: int = 0,
        limit: int = 25,
        search: str | None = None,
    ) -> SampleDataResponse:
        """Fetch paginated records for a specified dataset with optional search."""
        payments: list[dict[str, Any]] = []
        settlements: list[dict[str, Any]] = []
        ledger: list[dict[str, Any]] = []

        if dataset_id == "case_demo_101":
            payments, settlements, ledger = self._get_showcase_case_records()
        elif dataset_id == "case_demo_102":
            payments, settlements, ledger = self._get_case_demo_102_records()
        elif dataset_id == "case_demo_103":
            payments, settlements, ledger = self._get_case_demo_103_records()
        else:
            input_dir = self.generated_dir / dataset_id / "input"
            if not input_dir.exists():
                # Fallback to dev_500 if requested dataset does not exist on disk
                input_dir = self.generated_dir / "dev_500" / "input"

            if (input_dir / "payments.json").exists():
                payments = json.loads((input_dir / "payments.json").read_text(encoding="utf-8"))
            if (input_dir / "settlements.json").exists():
                settlements = json.loads(
                    (input_dir / "settlements.json").read_text(encoding="utf-8")
                )
            if (input_dir / "ledger.json").exists():
                ledger = json.loads((input_dir / "ledger.json").read_text(encoding="utf-8"))

        # Apply search filter if provided
        if search:
            q = search.lower().strip()
            payments = [
                p
                for p in payments
                if q in str(p.get("payment_id", "")).lower()
                or q in str(p.get("order_id", "")).lower()
                or q in str(p.get("merchant_id", "")).lower()
                or q in str(p.get("amount", "")).lower()
            ]
            settlements = [
                s
                for s in settlements
                if q in str(s.get("settlement_id", "")).lower()
                or q in str(s.get("utr", "")).lower()
                or q in str(s.get("amount", "")).lower()
                or any(q in str(pid).lower() for pid in s.get("payment_ids", []))
            ]
            ledger = [
                entry
                for entry in ledger
                if q in str(entry.get("entry_id", "")).lower()
                or q in str(entry.get("account", "")).lower()
                or q in str(entry.get("reference_id", "")).lower()
                or q in str(entry.get("amount", "")).lower()
            ]

        # Calculate counts and slice by source
        if source == "payments":
            total = len(payments)
            paginated_payments = payments[offset : offset + limit]
            return SampleDataResponse(
                dataset_id=dataset_id,
                source=source,
                total_count=total,
                offset=offset,
                limit=limit,
                payments=paginated_payments,
            )
        elif source == "settlements":
            total = len(settlements)
            paginated_settlements = settlements[offset : offset + limit]
            return SampleDataResponse(
                dataset_id=dataset_id,
                source=source,
                total_count=total,
                offset=offset,
                limit=limit,
                settlements=paginated_settlements,
            )
        elif source == "ledger":
            total = len(ledger)
            paginated_ledger = ledger[offset : offset + limit]
            return SampleDataResponse(
                dataset_id=dataset_id,
                source=source,
                total_count=total,
                offset=offset,
                limit=limit,
                ledger_entries=paginated_ledger,
            )
        else:
            # "all" - return interleaved top records
            total = max(len(payments), len(settlements), len(ledger))
            return SampleDataResponse(
                dataset_id=dataset_id,
                source="all",
                total_count=total,
                offset=offset,
                limit=limit,
                payments=payments[offset : offset + limit],
                settlements=settlements[offset : offset + limit],
                ledger_entries=ledger[offset : offset + limit],
            )

    def generate_random_records(self, req: RandomGenerationRequest) -> RandomGenerationResponse:
        """
        Synthesize multi-source transaction sets with entropy/temperature parameter.

        Temperature ranges:
        - 0.00: Strict exact match (clean payment, settlement, and double-entry ledger).
        - 0.10 - 0.40: Low entropy (minor fee variations, slight gateway delays).
        - 0.50 - 0.80: Medium entropy (interchange tax miscalculations, rounding, drift).
        - 0.81 - 1.00: High entropy (unsettled transactions, missing records, ambiguity).
        """
        seed = req.seed if req.seed is not None else int(time.time() * 1000) % 1_000_000_007
        rng = random.Random(seed)

        payments: list[dict[str, Any]] = []
        settlements: list[dict[str, Any]] = []
        ledger_entries: list[dict[str, Any]] = []
        summaries: list[str] = []

        now = datetime.now(UTC)

        for i in range(req.count):
            case_idx = i + 1
            suffix = f"{rng.randint(10000, 99999)}"
            payment_id = f"pay_rand_{suffix}"
            order_id = f"ord_rand_{suffix}"
            merchant_id = f"mer_rand_{rng.randint(100, 999)}"
            utr = f"UTR{rng.randint(100000000, 999999999)}"

            # Base amount between ₹500 and ₹25,000 in whole paise
            base_amount_val = Decimal(
                f"{rng.randint(500, 25000)}.{rng.choice(['00', '50', '25', '75'])}"
            )
            base_fee_val = Decimal(f"{round(float(base_amount_val) * 0.02, 2):.2f}")
            base_tax_val = Decimal(f"{round(float(base_fee_val) * 0.18, 2):.2f}")

            created_time = now - timedelta(hours=rng.randint(1, 48))
            settled_time = created_time + timedelta(minutes=rng.randint(15, 120))

            # Determine anomaly mode based on profile or temperature
            mode = req.anomaly_profile.upper()
            if mode == "AUTO":
                roll = rng.random()
                if roll > req.temperature:
                    mode = "EXACT_MATCH"
                else:
                    anomaly_choices = [
                        "FEE_DISCREPANCY",
                        "AMOUNT_MISMATCH",
                        "MISSING_SETTLEMENT",
                        "DATE_MISMATCH",
                    ]
                    mode = rng.choice(anomaly_choices)

            # Apply anomaly mutations
            if mode == "EXACT_MATCH":
                payment_fee = base_fee_val
                payment_tax = base_tax_val
                payment_net = base_amount_val - payment_fee - payment_tax
                settlement_amount = payment_net
                settlement_fee = payment_fee
                settlement_tax = payment_tax
                summaries.append(f"Case {case_idx}: Clean exact match (Amount: ₹{base_amount_val})")

                # Payment Feed
                payments.append(
                    {
                        "payment_id": payment_id,
                        "order_id": order_id,
                        "merchant_id": merchant_id,
                        "customer_id": f"cust_rand_{rng.randint(100, 999)}",
                        "amount": f"{base_amount_val:.2f}",
                        "currency": "INR",
                        "fee": f"{payment_fee:.2f}",
                        "tax": f"{payment_tax:.2f}",
                        "net": f"{payment_net:.2f}",
                        "status": "SUCCESS",
                        "payment_method": rng.choice(["UPI", "CARD", "NETBANKING"]),
                        "payment_timestamp": created_time.isoformat(),
                        "created_at": created_time.isoformat(),
                        "settled_at": settled_time.isoformat(),
                        "gateway_reference": f"gw_ref_{suffix}",
                        "metadata": {"payment_method": "card", "order_id": order_id},
                    }
                )

                # Settlement Feed
                settlements.append(
                    {
                        "settlement_id": f"set_rand_{suffix}",
                        "payment_id": payment_id,
                        "settled_amount": f"{settlement_amount:.2f}",
                        "amount": f"{settlement_amount:.2f}",
                        "fee": f"{settlement_fee:.2f}",
                        "fee_tax": f"{settlement_tax:.2f}",
                        "tax": f"{settlement_tax:.2f}",
                        "net": f"{settlement_amount:.2f}",
                        "currency": "INR",
                        "settlement_timestamp": settled_time.isoformat(),
                        "settlement_date": settled_time.date().isoformat(),
                        "status": "SETTLED",
                        "utr": utr,
                        "payment_ids": [payment_id],
                        "metadata": {"acquirer": "HDFC"},
                    }
                )

                # Internal Ledger Feed
                ledger_entries.append(
                    {
                        "ledger_id": f"led_deb_{suffix}",
                        "entry_id": f"led_deb_{suffix}",
                        "order_id": order_id,
                        "debit": f"{base_amount_val:.2f}",
                        "credit": "0.00",
                        "amount": f"{base_amount_val:.2f}",
                        "currency": "INR",
                        "entry_timestamp": created_time.isoformat(),
                        "timestamp": created_time.isoformat(),
                        "account": "PAYMENT_GATEWAY_CLEARING",
                        "direction": "DEBIT",
                        "status": "POSTED",
                        "reference_id": payment_id,
                        "metadata": {"order_id": order_id, "category": "CUSTOMER_PAYMENT"},
                    }
                )
                ledger_entries.append(
                    {
                        "ledger_id": f"led_crd_{suffix}",
                        "entry_id": f"led_crd_{suffix}",
                        "order_id": order_id,
                        "debit": "0.00",
                        "credit": f"{base_amount_val:.2f}",
                        "amount": f"{base_amount_val:.2f}",
                        "currency": "INR",
                        "entry_timestamp": created_time.isoformat(),
                        "timestamp": created_time.isoformat(),
                        "account": "ACCOUNTS_RECEIVABLE",
                        "direction": "CREDIT",
                        "status": "POSTED",
                        "reference_id": payment_id,
                        "metadata": {"order_id": order_id, "category": "REVENUE_RECOGNITION"},
                    }
                )

            elif mode == "FEE_DISCREPANCY":
                delta = Decimal(f"{rng.choice([15.00, 25.50, 50.00, 75.00, 100.00]):.2f}")
                payment_fee = base_fee_val
                payment_tax = base_tax_val
                payment_net = base_amount_val - payment_fee - payment_tax

                settlement_fee = payment_fee + delta
                settlement_tax = payment_tax
                settlement_amount = base_amount_val - settlement_fee - settlement_tax
                summaries.append(f"Case {case_idx}: Fee discrepancy (Diff -₹{delta})")

                payments.append(
                    {
                        "payment_id": payment_id,
                        "order_id": order_id,
                        "merchant_id": merchant_id,
                        "customer_id": f"cust_rand_{rng.randint(100, 999)}",
                        "amount": f"{base_amount_val:.2f}",
                        "currency": "INR",
                        "fee": f"{payment_fee:.2f}",
                        "tax": f"{payment_tax:.2f}",
                        "net": f"{payment_net:.2f}",
                        "status": "SUCCESS",
                        "payment_method": "CARD",
                        "payment_timestamp": created_time.isoformat(),
                        "created_at": created_time.isoformat(),
                        "settled_at": settled_time.isoformat(),
                        "gateway_reference": f"gw_ref_{suffix}",
                        "metadata": {"payment_method": "card", "order_id": order_id},
                    }
                )
                settlements.append(
                    {
                        "settlement_id": f"set_rand_{suffix}",
                        "payment_id": payment_id,
                        "settled_amount": f"{settlement_amount:.2f}",
                        "amount": f"{settlement_amount:.2f}",
                        "fee": f"{settlement_fee:.2f}",
                        "fee_tax": f"{settlement_tax:.2f}",
                        "tax": f"{settlement_tax:.2f}",
                        "net": f"{settlement_amount:.2f}",
                        "currency": "INR",
                        "settlement_timestamp": settled_time.isoformat(),
                        "settlement_date": settled_time.date().isoformat(),
                        "status": "SETTLED",
                        "utr": utr,
                        "payment_ids": [payment_id],
                        "metadata": {"acquirer": "HDFC"},
                    }
                )
                ledger_entries.append(
                    {
                        "ledger_id": f"led_deb_{suffix}",
                        "entry_id": f"led_deb_{suffix}",
                        "order_id": order_id,
                        "debit": f"{base_amount_val:.2f}",
                        "credit": "0.00",
                        "amount": f"{base_amount_val:.2f}",
                        "currency": "INR",
                        "entry_timestamp": created_time.isoformat(),
                        "timestamp": created_time.isoformat(),
                        "account": "PAYMENT_GATEWAY_CLEARING",
                        "direction": "DEBIT",
                        "status": "POSTED",
                        "reference_id": payment_id,
                        "metadata": {"order_id": order_id},
                    }
                )

            elif mode == "AMOUNT_MISMATCH":
                diff = Decimal(f"{rng.choice([10.00, 20.00, 50.00, 100.00]):.2f}")
                ledger_amount = base_amount_val - diff
                summaries.append(f"Case {case_idx}: Amount mismatch (Diff -₹{diff})")

                payments.append(
                    {
                        "payment_id": payment_id,
                        "order_id": order_id,
                        "merchant_id": merchant_id,
                        "customer_id": f"cust_rand_{rng.randint(100, 999)}",
                        "amount": f"{base_amount_val:.2f}",
                        "currency": "INR",
                        "fee": f"{base_fee_val:.2f}",
                        "tax": f"{base_tax_val:.2f}",
                        "net": f"{(base_amount_val - base_fee_val - base_tax_val):.2f}",
                        "status": "SUCCESS",
                        "payment_method": "UPI",
                        "payment_timestamp": created_time.isoformat(),
                        "created_at": created_time.isoformat(),
                        "settled_at": settled_time.isoformat(),
                        "gateway_reference": f"gw_ref_{suffix}",
                        "metadata": {"payment_method": "upi", "order_id": order_id},
                    }
                )
                settlements.append(
                    {
                        "settlement_id": f"set_rand_{suffix}",
                        "payment_id": payment_id,
                        "settled_amount": f"{(base_amount_val - base_fee_val - base_tax_val):.2f}",
                        "amount": f"{(base_amount_val - base_fee_val - base_tax_val):.2f}",
                        "fee": f"{base_fee_val:.2f}",
                        "fee_tax": f"{base_tax_val:.2f}",
                        "tax": f"{base_tax_val:.2f}",
                        "net": f"{(base_amount_val - base_fee_val - base_tax_val):.2f}",
                        "currency": "INR",
                        "settlement_timestamp": settled_time.isoformat(),
                        "settlement_date": settled_time.date().isoformat(),
                        "status": "SETTLED",
                        "utr": utr,
                        "payment_ids": [payment_id],
                        "metadata": {"acquirer": "AXIS"},
                    }
                )
                ledger_entries.append(
                    {
                        "ledger_id": f"led_deb_{suffix}",
                        "entry_id": f"led_deb_{suffix}",
                        "order_id": order_id,
                        "debit": f"{ledger_amount:.2f}",
                        "credit": "0.00",
                        "amount": f"{ledger_amount:.2f}",
                        "currency": "INR",
                        "entry_timestamp": created_time.isoformat(),
                        "timestamp": created_time.isoformat(),
                        "account": "PAYMENT_GATEWAY_CLEARING",
                        "direction": "DEBIT",
                        "status": "POSTED",
                        "reference_id": payment_id,
                        "metadata": {"order_id": order_id},
                    }
                )

            elif mode == "MISSING_SETTLEMENT":
                summaries.append(f"Case {case_idx}: Missing settlement (₹{base_amount_val})")
                payments.append(
                    {
                        "payment_id": payment_id,
                        "order_id": order_id,
                        "merchant_id": merchant_id,
                        "customer_id": f"cust_rand_{rng.randint(100, 999)}",
                        "amount": f"{base_amount_val:.2f}",
                        "currency": "INR",
                        "fee": f"{base_fee_val:.2f}",
                        "tax": f"{base_tax_val:.2f}",
                        "net": f"{(base_amount_val - base_fee_val - base_tax_val):.2f}",
                        "status": "SUCCESS",
                        "payment_method": "CARD",
                        "payment_timestamp": created_time.isoformat(),
                        "created_at": created_time.isoformat(),
                        "settled_at": None,
                        "gateway_reference": f"gw_ref_{suffix}",
                        "metadata": {"payment_method": "card", "order_id": order_id},
                    }
                )
                ledger_entries.append(
                    {
                        "ledger_id": f"led_deb_{suffix}",
                        "entry_id": f"led_deb_{suffix}",
                        "order_id": order_id,
                        "debit": f"{base_amount_val:.2f}",
                        "credit": "0.00",
                        "amount": f"{base_amount_val:.2f}",
                        "currency": "INR",
                        "entry_timestamp": created_time.isoformat(),
                        "timestamp": created_time.isoformat(),
                        "account": "PAYMENT_GATEWAY_CLEARING",
                        "direction": "DEBIT",
                        "status": "POSTED",
                        "reference_id": payment_id,
                        "metadata": {"order_id": order_id},
                    }
                )

            else:  # DATE_MISMATCH
                lag_days = rng.randint(3, 7)
                lagged_date = (settled_time + timedelta(days=lag_days)).date()
                summaries.append(f"Case {case_idx}: Date mismatch (Lagged {lag_days}d)")
                payments.append(
                    {
                        "payment_id": payment_id,
                        "order_id": order_id,
                        "customer_id": f"cust_rand_{rng.randint(100, 999)}",
                        "amount": f"{base_amount_val:.2f}",
                        "currency": "INR",
                        "fee": f"{base_fee_val:.2f}",
                        "tax": f"{base_tax_val:.2f}",
                        "net": f"{(base_amount_val - base_fee_val - base_tax_val):.2f}",
                        "status": "SUCCESS",
                        "payment_method": "NETBANKING",
                        "payment_timestamp": created_time.isoformat(),
                        "created_at": created_time.isoformat(),
                        "settled_at": (settled_time + timedelta(days=lag_days)).isoformat(),
                        "gateway_reference": f"gw_ref_{suffix}",
                        "metadata": {"payment_method": "netbanking", "order_id": order_id},
                    }
                )
                settlements.append(
                    {
                        "settlement_id": f"set_rand_{suffix}",
                        "payment_id": payment_id,
                        "settled_amount": f"{(base_amount_val - base_fee_val - base_tax_val):.2f}",
                        "amount": f"{(base_amount_val - base_fee_val - base_tax_val):.2f}",
                        "fee": f"{base_fee_val:.2f}",
                        "fee_tax": f"{base_tax_val:.2f}",
                        "tax": f"{base_tax_val:.2f}",
                        "net": f"{(base_amount_val - base_fee_val - base_tax_val):.2f}",
                        "currency": "INR",
                        "settlement_timestamp": (
                            settled_time + timedelta(days=lag_days)
                        ).isoformat(),
                        "settlement_date": lagged_date.isoformat(),
                        "status": "SETTLED",
                        "utr": utr,
                        "payment_ids": [payment_id],
                        "metadata": {"acquirer": "ICICI"},
                    }
                )
                ledger_entries.append(
                    {
                        "ledger_id": f"led_deb_{suffix}",
                        "entry_id": f"led_deb_{suffix}",
                        "order_id": order_id,
                        "debit": f"{base_amount_val:.2f}",
                        "credit": "0.00",
                        "amount": f"{base_amount_val:.2f}",
                        "currency": "INR",
                        "entry_timestamp": created_time.isoformat(),
                        "timestamp": created_time.isoformat(),
                        "account": "PAYMENT_GATEWAY_CLEARING",
                        "direction": "DEBIT",
                        "status": "POSTED",
                        "reference_id": payment_id,
                        "metadata": {"order_id": order_id},
                    }
                )

        generated_dataset_id = f"synth_t{int(req.temperature * 100)}_{seed % 100000}"
        return RandomGenerationResponse(
            generated_dataset_id=generated_dataset_id,
            seed=seed,
            temperature=req.temperature,
            anomaly_profile=req.anomaly_profile,
            anomaly_summary="; ".join(summaries),
            payments=payments,
            settlements=settlements,
            ledger_entries=ledger_entries,
            record_counts={
                "payments": len(payments),
                "settlements": len(settlements),
                "ledger_entries": len(ledger_entries),
                "total": len(payments) + len(settlements) + len(ledger_entries),
            },
        )

    def _get_feed_metrics(self, input_dir: Path) -> tuple[int, int, int, float]:
        """Compute record counts and file size in KB."""
        p_count, s_count, l_count = 0, 0, 0
        total_bytes = 0

        p_path = input_dir / "payments.json"
        s_path = input_dir / "settlements.json"
        l_path = input_dir / "ledger.json"

        if p_path.exists():
            total_bytes += p_path.stat().st_size
            try:
                p_count = len(json.loads(p_path.read_text(encoding="utf-8")))
            except Exception:
                pass

        if s_path.exists():
            total_bytes += s_path.stat().st_size
            try:
                s_count = len(json.loads(s_path.read_text(encoding="utf-8")))
            except Exception:
                pass

        if l_path.exists():
            total_bytes += l_path.stat().st_size
            try:
                l_count = len(json.loads(l_path.read_text(encoding="utf-8")))
            except Exception:
                pass

        return p_count, s_count, l_count, round(total_bytes / 1024.0, 1)

    def _get_showcase_case_records(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Return the exact multi-source records for showcase case_demo_101."""
        payments = [
            {
                "payment_id": "pay_live_demo_101",
                "order_id": "ord_live_2026_0902",
                "customer_id": "cust_live_demo_101",
                "amount": "10000.00",
                "currency": "INR",
                "fee": "200.00",
                "tax": "36.00",
                "net": "9764.00",
                "status": "SUCCESS",
                "payment_timestamp": "2026-09-02T10:15:00Z",
                "metadata": {
                    "payment_method": "CARD",
                    "merchant_id": "mer_cloud_scale_in",
                    "gateway_reference": "gw_ref_demo_101",
                },
            }
        ]
        settlements = [
            {
                "settlement_id": "set_live_demo_101",
                "payment_id": "pay_live_demo_101",
                "settled_amount": "9714.00",
                "fee": "250.00",
                "fee_tax": "36.00",
                "currency": "INR",
                "settlement_timestamp": "2026-09-02T12:30:00Z",
                "status": "SETTLED",
                "metadata": {"utr": "UTR20260902998811"},
            }
        ]
        ledger = [
            {
                "ledger_id": "led_demo_101_deb",
                "order_id": "ord_live_2026_0902",
                "account": "PAYMENT_GATEWAY_CLEARING",
                "debit": "10000.00",
                "credit": "0.00",
                "currency": "INR",
                "entry_timestamp": "2026-09-02T10:15:00Z",
                "status": "POSTED",
                "metadata": {"case_id": "case_demo_101", "reference_id": "pay_live_demo_101"},
            },
            {
                "ledger_id": "led_demo_101_crd",
                "order_id": "ord_live_2026_0902",
                "account": "SALES_REVENUE",
                "debit": "0.00",
                "credit": "10000.00",
                "currency": "INR",
                "entry_timestamp": "2026-09-02T10:15:00Z",
                "status": "POSTED",
                "metadata": {"case_id": "case_demo_101", "reference_id": "pay_live_demo_101"},
            },
        ]
        return payments, settlements, ledger

    def _get_case_demo_102_records(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Return the exact multi-source records for showcase case_demo_102 (Timing SLA breach)."""
        payments = [
            {
                "payment_id": "pay_live_demo_102",
                "order_id": "ORD-99813-IN",
                "customer_id": "cust_live_demo_102",
                "amount": "4500.00",
                "currency": "INR",
                "fee": "90.00",
                "tax": "16.20",
                "net": "4393.80",
                "status": "SUCCESS",
                "payment_timestamp": "2026-09-01T08:00:00Z",
                "metadata": {
                    "payment_method": "UPI",
                    "merchant_id": "mer_cloud_scale_in",
                    "gateway_reference": "gw_ref_demo_102",
                },
            }
        ]
        settlements = [
            {
                "settlement_id": "set_live_demo_102",
                "payment_id": "pay_live_demo_102",
                "settled_amount": "4393.80",
                "fee": "90.00",
                "fee_tax": "16.20",
                "currency": "INR",
                "settlement_timestamp": "2026-08-30T10:00:00Z",
                "status": "SETTLED",
                "metadata": {"utr": "UTR20260903887722"},
            }
        ]
        ledger = [
            {
                "ledger_id": "led_demo_102_deb",
                "order_id": "ORD-99813-IN",
                "account": "PAYMENT_GATEWAY_CLEARING",
                "debit": "4500.00",
                "credit": "0.00",
                "currency": "INR",
                "entry_timestamp": "2026-09-01T08:00:00Z",
                "status": "POSTED",
                "metadata": {"case_id": "case_demo_102", "reference_id": "pay_live_demo_102"},
            },
            {
                "ledger_id": "led_demo_102_crd",
                "order_id": "ORD-99813-IN",
                "account": "SALES_REVENUE",
                "debit": "0.00",
                "credit": "4500.00",
                "currency": "INR",
                "entry_timestamp": "2026-09-01T08:00:00Z",
                "status": "POSTED",
                "metadata": {"case_id": "case_demo_102", "reference_id": "pay_live_demo_102"},
            },
        ]
        return payments, settlements, ledger

    def _get_case_demo_103_records(
        self,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        """Return the exact multi-source records for showcase case_demo_103 (Missing settlement)."""
        payments = [
            {
                "payment_id": "pay_live_demo_103",
                "order_id": "ORD-99814-IN",
                "customer_id": "cust_live_demo_103",
                "amount": "18200.00",
                "currency": "INR",
                "fee": "364.00",
                "tax": "65.52",
                "net": "17770.48",
                "status": "SUCCESS",
                "payment_timestamp": "2026-09-02T05:20:00Z",
                "metadata": {
                    "payment_method": "NETBANKING",
                    "merchant_id": "mer_cloud_scale_in",
                    "gateway_reference": "gw_ref_demo_103",
                },
            }
        ]
        settlements: list[dict[str, Any]] = []
        ledger = [
            {
                "ledger_id": "led_demo_103_deb",
                "order_id": "ORD-99814-IN",
                "account": "PAYMENT_GATEWAY_CLEARING",
                "debit": "18200.00",
                "credit": "0.00",
                "currency": "INR",
                "entry_timestamp": "2026-09-02T05:20:00Z",
                "status": "POSTED",
                "metadata": {"case_id": "case_demo_103", "reference_id": "pay_live_demo_103"},
            },
            {
                "ledger_id": "led_demo_103_crd",
                "order_id": "ORD-99814-IN",
                "account": "SALES_REVENUE",
                "debit": "0.00",
                "credit": "18200.00",
                "currency": "INR",
                "entry_timestamp": "2026-09-02T05:20:00Z",
                "status": "POSTED",
                "metadata": {"case_id": "case_demo_103", "reference_id": "pay_live_demo_103"},
            },
        ]
        return payments, settlements, ledger
