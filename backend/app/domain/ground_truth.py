"""Isolated ground-truth data models and dataset manifests for METFI evaluation."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import ExceptionType, PolicyOutcome


class InjectedFaultDetails(BaseModel):
    """Structured description of synthetic fault injected into a transaction."""

    model_config = ConfigDict(frozen=True)

    exception_type: ExceptionType = Field(description="Injected corruption class")
    description: str = Field(description="Human-readable explanation of injected fault")
    target_source: str = Field(description="Source mutated: payment, settlement, ledger, or cross")
    field_mutated: str | None = Field(default=None, description="Specific field name modified")
    original_value: Any = Field(default=None, description="Original value before corruption")
    mutated_value: Any = Field(default=None, description="Value after corruption")
    delta: Decimal | None = Field(
        default=None, description="Monetary or timing delta if applicable"
    )


class GroundTruthRecord(BaseModel):
    """Isolated ground-truth label for a logical reconciliation case."""

    model_config = ConfigDict(frozen=True)

    case_id: str = Field(description="Unique reconciliation case identifier")
    order_id: str = Field(description="Merchant order reference")
    expected_classification: ExceptionType = Field(
        description="Ground-truth exception classification"
    )
    expected_policy_outcome: PolicyOutcome = Field(
        description="Ground-truth expected policy authorization outcome"
    )
    payment_id: str | None = Field(default=None, description="Associated payment ID")
    settlement_id: str | None = Field(default=None, description="Associated settlement ID")
    ledger_ids: list[str] = Field(default_factory=list, description="Associated ledger entry IDs")
    expected_amount_delta: Decimal = Field(
        default=Decimal("0.00"), description="Expected mathematical discrepancy delta"
    )
    injected_fault: InjectedFaultDetails | None = Field(
        default=None, description="Fault injection metadata if corrupted"
    )
    is_synthetic: bool = Field(
        default=True, description="Flag indicating synthetic evaluation case"
    )


class DatasetManifest(BaseModel):
    """Audit and provenance manifest for synthetic dataset generation."""

    dataset_id: str = Field(description="Unique dataset identifier, e.g. dev_500, stress_5000")
    generator_version: str = Field(default="1.0.0", description="Semantic version of generator")
    schema_version: str = Field(default="1.0.0", description="Semantic version of domain schema")
    seed: int = Field(description="Pseudorandom generator seed used for generation")
    record_count: int = Field(description="Total logical transactions generated")
    generation_timestamp: str = Field(description="UTC timestamp of generation")
    source_counts: dict[str, int] = Field(
        description="Counts of physical records per source: payments, settlements, ledger"
    )
    class_distribution: dict[str, int] = Field(
        description="Exact count of transactions per ExceptionType"
    )
    checksums: dict[str, str] = Field(
        default_factory=dict,
        description="SHA256 checksums of generated input and ground-truth files",
    )
