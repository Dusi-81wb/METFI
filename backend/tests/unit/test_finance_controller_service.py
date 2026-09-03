"""
Unit tests for FinanceControllerService:
- Cash position calculations (settled, in-transit, leakage)
- Books status and double-entry balancing invariant
- 50+ record synthetic batch loop execution
- Honest exception list reporting and match rates
- Settlement Q&A natural language query processing
"""

from app.services.finance_controller_service import FinanceControllerService


def test_finance_ops_loop_execution_dev_500() -> None:
    """Run full loop on primary 500-record batch, verifying match rate and honest exceptions."""
    service = FinanceControllerService()
    report = service.run_finance_ops_loop(dataset_id="dev_500")

    assert report.batch_id == "dev_500"
    assert report.records_evaluated > 50  # 50+ record requirement explicitly satisfied
    assert report.total_cases == 500
    assert report.matched_cases_count == 300
    assert report.match_rate_pct == 60.0  # 300 / 500 = 60.0%
    assert report.unresolved_exceptions_count == 200
    assert len(report.honest_exception_list) == 200

    # Ensure throughput satisfies performance bar
    assert report.throughput_records_per_sec > 1000.0
    assert report.measured_accuracy_pct == 100.0


def test_books_status_double_entry_invariant() -> None:
    """Verify general ledger debits and credits balance to 0.00 difference."""
    service = FinanceControllerService()
    report = service.run_finance_ops_loop(dataset_id="dev_500")

    books = report.books_status
    assert books.total_debits > 0.0
    assert books.total_credits > 0.0
    # In double entry, total debits must equal total credits
    assert books.imbalance == 0.0
    assert books.is_balanced is True
    assert len(books.accounts) > 0


def test_cash_position_calculation() -> None:
    """Verify cash position breakdown: settled bank funds, in-transit, and disputed leakage."""
    service = FinanceControllerService()
    report = service.run_finance_ops_loop(dataset_id="dev_500")

    cash = report.cash_position
    assert cash.settled_cash_bank > 0.0
    assert cash.expected_gross_cash > 0.0
    assert cash.contractual_fees_tax > 0.0
    assert cash.net_reconciled_cash > 0.0
    assert cash.forward_projection_24h > 0.0
    assert cash.forward_projection_48h >= cash.forward_projection_24h


def test_honest_exception_list_transparency() -> None:
    """Verify honest exception list has concrete explanations and quarantine states."""
    service = FinanceControllerService()
    report = service.run_finance_ops_loop(dataset_id="dev_500")

    ex_list = report.honest_exception_list
    assert len(ex_list) > 0

    first_ex = ex_list[0]
    assert first_ex.case_id.startswith("case_")
    assert first_ex.policy_outcome in ["REVIEW_REQUIRED", "UNRESOLVED"]
    assert len(first_ex.reason_unresolved) > 10
    assert first_ex.quarantine_state in ["REVIEW_QUEUE", "UNMATCHED_POOL"]


def test_settlement_qa_queries() -> None:
    """Test natural language queries on the Settlement & Cash Position Q&A Agent."""
    service = FinanceControllerService()

    # Cash query
    res_cash = service.answer_controller_query("What is our settled bank cash position?")
    assert "Bank Settled Cash" in res_cash.answer
    assert res_cash.confidence == 1.0

    # Books query
    res_books = service.answer_controller_query("Is our general ledger balanced?")
    assert "BALANCED" in res_books.answer
    assert "Invariant verified" in res_books.answer

    # Exceptions query
    res_ex = service.answer_controller_query("Which exceptions could not be resolved?")
    assert "Honest Exception Report" in res_ex.answer
    assert "quarantined for controller review" in res_ex.answer
