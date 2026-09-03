"""Unit tests for SampleDataService: enumeration, pagination, search, and generation."""

from app.schemas.data import RandomGenerationRequest
from app.services.sample_data_service import SampleDataService


def test_available_datasets_enumeration() -> None:
    """Ensure catalog lists standard fixtures including dev_500 and case_demo_101."""
    service = SampleDataService()
    datasets = service.get_available_datasets()

    dataset_ids = [d.dataset_id for d in datasets]
    assert "dev_500" in dataset_ids
    assert "case_demo_101" in dataset_ids

    demo_case = next(d for d in datasets if d.dataset_id == "case_demo_101")
    assert demo_case.payments_count == 1
    assert demo_case.settlements_count == 1
    assert demo_case.ledger_count == 2
    assert demo_case.is_live_fixture is True


def test_sample_data_pagination_and_source_filter() -> None:
    """Verify pagination and source slicing for operational feeds."""
    service = SampleDataService()

    # Payments feed pagination
    res_payments = service.get_sample_data(
        dataset_id="dev_500", source="payments", offset=0, limit=10
    )
    assert res_payments.dataset_id == "dev_500"
    assert res_payments.source == "payments"
    assert len(res_payments.payments) <= 10
    assert res_payments.total_count > 0

    # Settlements feed pagination
    res_settlements = service.get_sample_data(
        dataset_id="dev_500", source="settlements", offset=0, limit=5
    )
    assert len(res_settlements.settlements) <= 5

    # Ledger feed pagination
    res_ledger = service.get_sample_data(dataset_id="dev_500", source="ledger", offset=0, limit=5)
    assert len(res_ledger.ledger_entries) <= 5


def test_sample_data_search_filtering() -> None:
    """Verify keyword filtering on accounts, amounts, or IDs."""
    service = SampleDataService()
    res = service.get_sample_data(dataset_id="case_demo_101", source="all", search="10000.00")
    assert len(res.payments) == 1
    assert res.payments[0]["amount"] == "10000.00"

    res_empty = service.get_sample_data(
        dataset_id="case_demo_101", source="all", search="NON_EXISTENT_STRING_9999"
    )
    assert len(res_empty.payments) == 0
    assert len(res_empty.settlements) == 0


def test_random_generation_clean_match_temp_zero() -> None:
    """At temperature 0.0 with EXACT_MATCH, generated amounts and fees balance cleanly."""
    service = SampleDataService()
    req = RandomGenerationRequest(count=3, temperature=0.0, anomaly_profile="EXACT_MATCH", seed=42)
    res = service.generate_random_records(req)

    assert len(res.payments) == 3
    assert len(res.settlements) == 3
    assert len(res.ledger_entries) == 6  # 2 balanced double-entry records per case
    assert res.seed == 42
    assert "Clean exact match" in res.anomaly_summary

    # Ensure reproducibility with same seed
    res2 = service.generate_random_records(req)
    assert res.payments[0]["payment_id"] == res2.payments[0]["payment_id"]
    assert res.payments[0]["amount"] == res2.payments[0]["amount"]


def test_random_generation_fee_discrepancy() -> None:
    """At FEE_DISCREPANCY, settlement fee exceeds payment fee."""
    service = SampleDataService()
    req = RandomGenerationRequest(
        count=2, temperature=0.5, anomaly_profile="FEE_DISCREPANCY", seed=101
    )
    res = service.generate_random_records(req)

    assert len(res.payments) == 2
    assert len(res.settlements) == 2
    assert "Fee discrepancy" in res.anomaly_summary


def test_random_generation_missing_settlement() -> None:
    """At MISSING_SETTLEMENT, payment is generated but settlement is absent."""
    service = SampleDataService()
    req = RandomGenerationRequest(
        count=1, temperature=0.8, anomaly_profile="MISSING_SETTLEMENT", seed=777
    )
    res = service.generate_random_records(req)

    assert len(res.payments) == 1
    assert len(res.settlements) == 0  # Missing!
    assert len(res.ledger_entries) == 1
    assert "Missing settlement" in res.anomaly_summary
