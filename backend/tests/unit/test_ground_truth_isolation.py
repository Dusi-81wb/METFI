"""Rigorous leakage tests proving complete isolation of ground-truth data from inference input."""

import json
import tempfile
from pathlib import Path

from app.services.data_generator import SyntheticFinancialGenerator, export_dataset


def test_input_payloads_have_zero_ground_truth_fields() -> None:
    """Verify that generated raw records contain no ground-truth or corruption labels."""
    gen = SyntheticFinancialGenerator(seed=42)
    res = gen.generate(size=100, dataset_id="leakage_test_100")

    forbidden_fields = {
        "expected_classification",
        "expected_policy_outcome",
        "injected_fault",
        "is_synthetic",
        "corruption_class",
        "ground_truth",
        "label",
        "fault",
    }

    # Inspect all raw payments
    for p in res.payments:
        d = p.model_dump()
        for forbidden in forbidden_fields:
            assert forbidden not in d
            assert forbidden not in d.get("metadata", {})

    # Inspect all raw settlements
    for s in res.settlements:
        d = s.model_dump()
        for forbidden in forbidden_fields:
            assert forbidden not in d
            assert forbidden not in d.get("metadata", {})

    # Inspect all raw ledger entries
    for le in res.ledger_entries:
        d = le.model_dump()
        for forbidden in forbidden_fields:
            assert forbidden not in d
            assert forbidden not in d.get("metadata", {})


def test_exported_files_physical_isolation() -> None:
    """Verify exported directory structure segregates input from ground truth."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        gen = SyntheticFinancialGenerator(seed=42)
        res = gen.generate(size=50, dataset_id="iso_test")
        exported = export_dataset(res, base_dir=tmp_path)

        # 1. Read input manifest
        with open(exported["input_manifest"], encoding="utf-8") as f:
            in_manifest = json.load(f)
        assert "class_distribution" not in in_manifest
        assert "ground_truth_sha256" not in in_manifest

        # 2. Read payments input file
        with open(exported["payments"], encoding="utf-8") as f:
            payments_data = json.load(f)
        for row in payments_data:
            assert "expected_classification" not in row
            assert "injected_fault" not in row

        # 3. Verify ground truth file is strictly in ground_truth/ folder
        assert "ground_truth" in str(exported["ground_truth"])
        assert "generated" in str(exported["payments"])
        assert not (tmp_path / "generated" / "iso_test" / "input" / "ground_truth.json").exists()
