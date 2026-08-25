"""Integration tests for end-to-end dataset generation, validation, and file serialization."""

import json
import tempfile
from pathlib import Path

import pytest

from app.domain.normalizer import (
    normalize_ledger,
    normalize_payment,
    normalize_settlement,
)
from app.services.data_generator import (
    SyntheticFinancialGenerator,
    export_dataset,
)


@pytest.mark.integration
def test_end_to_end_dataset_generation_and_normalization() -> None:
    """Verify end-to-end generation, serialization, reloading, and normalization."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        generator = SyntheticFinancialGenerator(seed=42)
        result = generator.generate(size=100, dataset_id="pipeline_test_100")
        export_paths = export_dataset(result, base_dir=tmp_path)

        for key, path in export_paths.items():
            assert path.exists(), f"File {key} at {path} was not created."

        # Load and normalize raw payments
        with open(export_paths["payments"], encoding="utf-8") as f:
            payments_raw = json.load(f)
        assert len(payments_raw) == len(result.payments)
        for p in payments_raw:
            canonical_p = normalize_payment(p)
            assert canonical_p.payment_id.startswith("pay_")

        # Load and normalize raw settlements
        with open(export_paths["settlements"], encoding="utf-8") as f:
            settlements_raw = json.load(f)
        assert len(settlements_raw) == len(result.settlements)
        for s in settlements_raw:
            canonical_s = normalize_settlement(s)
            assert canonical_s.settlement_id.startswith("set_")

        # Load and normalize raw ledger entries
        with open(export_paths["ledger"], encoding="utf-8") as f:
            ledger_raw = json.load(f)
        assert len(ledger_raw) == len(result.ledger_entries)
        for le in ledger_raw:
            canonical_le = normalize_ledger(le)
            assert canonical_le.ledger_id.startswith("led_")

        # Verify ground truth manifest
        with open(export_paths["gt_manifest"], encoding="utf-8") as f:
            manifest = json.load(f)
        assert manifest["record_count"] == 100
        assert "checksums" in manifest
        assert len(manifest["checksums"]) == 4
