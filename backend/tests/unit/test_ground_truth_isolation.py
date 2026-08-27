"""Rigorous adversarial leakage tests proving complete isolation of ground truth."""

import json
import re
import tempfile
from pathlib import Path

from app.domain.enums import ExceptionType
from app.domain.raw_models import RawLedgerRecord, RawPaymentRecord, RawSettlementRecord
from app.services.data_generator import SyntheticFinancialGenerator, export_dataset

# Opaque identifier format regex: prefix + underscore + 12 hex characters
OPAQUE_ID_REGEX = re.compile(r"^[a-z]+_[a-f0-9]{12}$")

# Strict blacklist of semantic markers, corruption labels, and generator internal tokens
FORBIDDEN_LEAKAGE_TOKENS = {
    # Class names
    "exact_match",
    "amount_mismatch",
    "missing_settlement",
    "duplicate_record",
    "date_mismatch",
    "reference_mismatch",
    "partial_settlement",
    "fee_discrepancy",
    "currency_mismatch",
    "ambiguous",
    # Specific leaked markers identified in audit
    "duplicate_flag",
    "reversal_notice",
    "partial_chargeback_split",
    "_dup",
    "dup",
    # Evaluation / Ground truth metadata tokens
    "expected_classification",
    "expected_policy_outcome",
    "injected_fault",
    "target_source",
    "field_mutated",
    "original_value",
    "mutated_value",
    "expected_amount_delta",
    "is_synthetic",
    "ground_truth",
    "corruption",
    "fault",
    # Policy outcomes
    "auto_reconcile",
    "review_required",
    "unresolved",
}


def _deep_extract_strings_and_keys(obj: object) -> list[str]:
    """Recursively extract all dictionary keys and string values from an arbitrary object."""
    results: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            results.append(str(k))
            results.extend(_deep_extract_strings_and_keys(v))
    elif isinstance(obj, list):
        for item in obj:
            results.extend(_deep_extract_strings_and_keys(item))
    elif isinstance(obj, str):
        results.append(obj)
    return results


def test_input_payload_schema_strictness() -> None:
    """Verify that inference records strictly match raw models with no unauthorized fields."""
    gen = SyntheticFinancialGenerator(seed=42)
    res = gen.generate(size=100, dataset_id="schema_test_100")

    payment_allowed_fields = set(RawPaymentRecord.model_fields.keys())
    settlement_allowed_fields = set(RawSettlementRecord.model_fields.keys())
    ledger_allowed_fields = set(RawLedgerRecord.model_fields.keys())

    for p in res.payments:
        d = p.model_dump()
        assert set(d.keys()) == payment_allowed_fields
        assert "metadata" in d
        assert isinstance(d["metadata"], dict)

    for s in res.settlements:
        d = s.model_dump()
        assert set(d.keys()) == settlement_allowed_fields
        assert "metadata" in d
        assert isinstance(d["metadata"], dict)

    for le in res.ledger_entries:
        d = le.model_dump()
        assert set(d.keys()) == ledger_allowed_fields
        assert "metadata" in d
        assert isinstance(d["metadata"], dict)


def test_adversarial_token_scan_across_all_inference_records() -> None:
    """Adversarially scan all keys and string values for forbidden tokens."""
    gen = SyntheticFinancialGenerator(seed=42)
    res = gen.generate(size=200, dataset_id="scan_test_200")

    all_records = (
        [p.model_dump() for p in res.payments]
        + [s.model_dump() for s in res.settlements]
        + [le.model_dump() for le in res.ledger_entries]
    )

    for record in all_records:
        tokens = _deep_extract_strings_and_keys(record)
        for token in tokens:
            lower_token = token.lower()
            for forbidden in FORBIDDEN_LEAKAGE_TOKENS:
                assert forbidden not in lower_token, (
                    f"Leaked token '{forbidden}' in string '{token}' of: {record}"
                )


def test_opaque_ids_do_not_leak_index_or_class() -> None:
    """Verify that all generated IDs are opaque, uniform, and do not leak index/class."""
    gen = SyntheticFinancialGenerator(seed=42)
    res = gen.generate(size=100, dataset_id="opaque_id_test")

    for p in res.payments:
        assert OPAQUE_ID_REGEX.match(p.payment_id)
        assert OPAQUE_ID_REGEX.match(p.order_id)
        assert OPAQUE_ID_REGEX.match(p.customer_id)
        # Ensure sequential indices like "00001", "00002" are not in the ID
        assert not re.search(r"_\d{5}$", p.payment_id)
        assert not re.search(r"_\d{5}$", p.order_id)

    for s in res.settlements:
        assert OPAQUE_ID_REGEX.match(s.settlement_id)
        assert OPAQUE_ID_REGEX.match(s.payment_id)
        assert "_dup" not in s.settlement_id.lower()
        assert not re.search(r"_\d{5}$", s.settlement_id)

    for le in res.ledger_entries:
        assert OPAQUE_ID_REGEX.match(le.ledger_id)
        assert "_dr" not in le.ledger_id.lower()
        assert "_cr" not in le.ledger_id.lower()
        assert not re.search(r"_\d{5}$", le.ledger_id)


def test_duplicate_record_metadata_and_id_invariance() -> None:
    """Verify DUPLICATE_RECORD cases contain zero duplicate metadata flags and use opaque IDs."""
    gen = SyntheticFinancialGenerator(seed=42)
    res = gen.generate(size=100, dataset_id="dup_test")

    # Find ground truth cases for duplicate records
    dup_cases = [
        gt
        for gt in res.ground_truth
        if gt.expected_classification == ExceptionType.DUPLICATE_RECORD
    ]
    assert len(dup_cases) > 0

    for gt in dup_cases:
        payment_id = gt.payment_id
        matching_settlements = [s for s in res.settlements if s.payment_id == payment_id]
        assert len(matching_settlements) == 2

        for s in matching_settlements:
            # Metadata must not contain duplicate_flag or any duplicate markers
            assert "duplicate_flag" not in s.metadata
            assert "duplicate" not in s.metadata
            assert "dup" not in s.metadata
            # Settlement ID must be standard opaque format without _DUP
            assert OPAQUE_ID_REGEX.match(s.settlement_id)
            assert "_dup" not in s.settlement_id.lower()


def test_ambiguous_metadata_invariance() -> None:
    """Verify AMBIGUOUS cases contain zero semantic reversal notices or class hints."""
    gen = SyntheticFinancialGenerator(seed=42)
    res = gen.generate(size=100, dataset_id="ambiguous_test")

    ambiguous_cases = [
        gt for gt in res.ground_truth if gt.expected_classification == ExceptionType.AMBIGUOUS
    ]
    assert len(ambiguous_cases) > 0

    for gt in ambiguous_cases:
        order_id = gt.order_id
        matching_payments = [p for p in res.payments if p.order_id == order_id]
        if matching_payments:
            payment_id = matching_payments[0].payment_id
            matching_settlements = [s for s in res.settlements if s.payment_id == payment_id]
            for s in matching_settlements:
                assert "reversal_notice" not in s.metadata
                assert "partial_chargeback_split" not in str(s.metadata)


def test_reference_mismatch_ledger_id_anti_correlation() -> None:
    """Verify that REFERENCE_MISMATCH ledger IDs do not reveal original order ID or index."""
    gen = SyntheticFinancialGenerator(seed=42)
    res = gen.generate(size=100, dataset_id="ref_mismatch_test")

    ref_mismatch_cases = [
        gt
        for gt in res.ground_truth
        if gt.expected_classification == ExceptionType.REFERENCE_MISMATCH
    ]
    assert len(ref_mismatch_cases) > 0

    for gt in ref_mismatch_cases:
        # Original order_id in ground truth
        orig_order_id = gt.order_id
        # Associated ledger entry IDs
        for led_id in gt.ledger_ids:
            # Find the actual ledger record
            matching_le = next(le for le in res.ledger_entries if le.ledger_id == led_id)
            # The mutated order ID in ledger does not match original
            # The ledger_id is completely opaque and cannot contain order ID fragments
            order_hash_part = orig_order_id.replace("ord_", "")
            assert order_hash_part not in matching_le.ledger_id


def test_exported_files_physical_isolation() -> None:
    """Verify exported directory structure strictly segregates input from ground truth."""
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
