"""Pydantic schemas for sample data inspection and on-demand synthetic generation."""

from typing import Any

from pydantic import BaseModel, Field


class DatasetMetadata(BaseModel):
    """Metadata summary of an available sample dataset."""

    dataset_id: str = Field(..., description="Unique dataset identifier")
    name: str = Field(..., description="Human-readable title")
    description: str = Field(..., description="Detailed description of dataset purpose")
    payments_count: int = Field(default=0, description="Total payment records")
    settlements_count: int = Field(default=0, description="Total settlement records")
    ledger_count: int = Field(default=0, description="Total ledger records")
    total_records: int = Field(default=0, description="Total combined records across feeds")
    file_size_kb: float = Field(default=0.0, description="Total payload size in kilobytes")
    is_live_fixture: bool = Field(
        default=False, description="Whether this is the primary live demo fixture"
    )


class SampleDataQuery(BaseModel):
    """Query parameters for fetching sample dataset records."""

    dataset_id: str = Field(default="dev_500", description="Dataset identifier")
    source: str = Field(
        default="all", description="Source feed: 'all', 'payments', 'settlements', 'ledger'"
    )
    offset: int = Field(default=0, ge=0, description="Pagination offset")
    limit: int = Field(default=25, ge=1, le=100, description="Records limit per page")
    search: str | None = Field(
        default=None, description="Optional text filter across IDs, accounts, and references"
    )


class SampleDataResponse(BaseModel):
    """Paginated response containing multi-source operational records."""

    dataset_id: str
    source: str
    total_count: int
    offset: int
    limit: int
    payments: list[dict[str, Any]] = Field(default_factory=list)
    settlements: list[dict[str, Any]] = Field(default_factory=list)
    ledger_entries: list[dict[str, Any]] = Field(default_factory=list)


class RandomGenerationRequest(BaseModel):
    """Request payload to generate randomized synthetic transactions with temperature controls."""

    count: int = Field(
        default=1, ge=1, le=100, description="Number of multi-source transaction sets to generate"
    )
    temperature: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Entropy level (0.0 = clean deterministic match, 1.0 = heavy anomaly / chaos)",
    )
    anomaly_profile: str = Field(
        default="AUTO",
        description="Target scenario: 'AUTO', 'EXACT_MATCH', 'FEE_DISCREPANCY', etc.",
    )
    seed: int | None = Field(
        default=None,
        description="Optional seed for reproducibility. If None, uses random entropy.",
    )


class RandomGenerationResponse(BaseModel):
    """Generated synthetic records ready for inspection and immediate platform reconciliation."""

    generated_dataset_id: str
    seed: int
    temperature: float
    anomaly_profile: str
    anomaly_summary: str
    payments: list[dict[str, Any]]
    settlements: list[dict[str, Any]]
    ledger_entries: list[dict[str, Any]]
    record_counts: dict[str, int]
