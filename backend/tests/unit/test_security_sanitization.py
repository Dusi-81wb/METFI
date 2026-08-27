"""Unit tests for dataset ID security sanitization and path traversal prevention."""

import tempfile
from pathlib import Path

import pytest

from app.domain.sanitization import DatasetIdValidationError, validate_dataset_id
from app.services.data_generator import SyntheticFinancialGenerator, export_dataset


def test_validate_dataset_id_valid() -> None:
    """Verify that legitimate dataset identifiers pass validation."""
    valid_ids = [
        "dev_500",
        "stress_5000",
        "test-dataset-01",
        "benchmark_tier_3",
        "A1_b2_C3",
        "a" * 64,
    ]
    for dataset_id in valid_ids:
        assert validate_dataset_id(dataset_id) == dataset_id


@pytest.mark.parametrize(
    "invalid_id",
    [
        "../evil",
        "..\\evil",
        "../../etc/passwd",
        "/absolute/path",
        "\\absolute\\path",
        "C:\\Windows\\System32",
        "nested/../escape",
        "nested\\..\\escape",
        "dev 500",
        " dev_500",
        "dev_500 ",
        "dev\t500",
        "dev\n500",
        "dev_\0_500",
        "dev@500",
        "dev!500",
        "dev#500",
        "dev$500",
        "dev%500",
        "dev*500",
        "",
        "   ",
        "a" * 65,  # Exceeds max length of 64
    ],
)
def test_validate_dataset_id_rejects_malicious_and_invalid(invalid_id: str) -> None:
    """Verify that path traversal, absolute paths, special chars, and empty IDs are rejected."""
    with pytest.raises(DatasetIdValidationError):
        validate_dataset_id(invalid_id)


def test_validate_dataset_id_rejects_none() -> None:
    """Verify that None is rejected."""
    with pytest.raises(DatasetIdValidationError):
        validate_dataset_id(None)  # type: ignore[arg-type]


def test_export_dataset_rejects_path_traversal() -> None:
    """Verify that export_dataset rejects path traversal attempts."""
    gen = SyntheticFinancialGenerator(seed=42)
    res = gen.generate(size=10, dataset_id="dev_10")
    # Tamper with dataset_id post-generation
    res.dataset_id = "../evil_traversal"

    with tempfile.TemporaryDirectory() as tmp_dir:
        with pytest.raises(DatasetIdValidationError):
            export_dataset(res, base_dir=Path(tmp_dir))
