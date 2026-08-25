"""Unit tests for synthetic dataset generator reproducibility and distribution."""

from app.domain.enums import ExceptionType
from app.services.data_generator import SyntheticFinancialGenerator


def test_generator_deterministic_reproducibility() -> None:
    """Verify that same seed produces identical payments, settlements, and ground truth."""
    gen1 = SyntheticFinancialGenerator(seed=42)
    res1 = gen1.generate(size=50, dataset_id="test_50")

    gen2 = SyntheticFinancialGenerator(seed=42)
    res2 = gen2.generate(size=50, dataset_id="test_50")

    assert len(res1.payments) == len(res2.payments)
    assert len(res1.settlements) == len(res2.settlements)
    assert len(res1.ground_truth) == len(res2.ground_truth)

    for p1, p2 in zip(res1.payments, res2.payments, strict=True):
        assert p1.payment_id == p2.payment_id
        assert p1.amount == p2.amount

    for gt1, gt2 in zip(res1.ground_truth, res2.ground_truth, strict=True):
        assert gt1.case_id == gt2.case_id
        assert gt1.expected_classification == gt2.expected_classification
        assert gt1.expected_policy_outcome == gt2.expected_policy_outcome


def test_generator_different_seeds_produce_different_data() -> None:
    """Verify that different seeds produce distinct datasets."""
    gen1 = SyntheticFinancialGenerator(seed=42)
    res1 = gen1.generate(size=50, dataset_id="test_50_a")

    gen2 = SyntheticFinancialGenerator(seed=999)
    res2 = gen2.generate(size=50, dataset_id="test_50_b")

    # Payment IDs or order IDs will differ
    assert res1.payments[0].payment_id != res2.payments[0].payment_id


def test_generator_class_distribution_sums_to_total() -> None:
    """Verify that class distribution counts match requested total size."""
    size = 500
    gen = SyntheticFinancialGenerator(seed=42)
    res = gen.generate(size=size, dataset_id="dev_500")

    assert len(res.ground_truth) == size
    total_in_dist = sum(res.manifest.class_distribution.values())
    assert total_in_dist == size

    # Verify all 10 classes are present in manifest
    assert len(res.manifest.class_distribution) == len(ExceptionType)
    # Check that exact match is the majority class (~65%)
    assert res.manifest.class_distribution[ExceptionType.EXACT_MATCH.value] >= 300
