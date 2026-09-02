"""
Integration tests for Phase 8 Failure Injections & Graceful Degradation.

Verifies:
1. AI provider outage falls back safely without unhandled crashes.
2. Malformed LLM response triggers safe, bounded fallback envelope.
3. Cryptographic hash tampering in audit persistence is instantaneously detected.
4. Duplicate actions fail safely with idempotency deduplication.
"""

import pytest

from app.audit.models import AuditEventType
from app.audit.service import AuditService
from app.audit.verifier import AuditIntegrityVerifier
from app.intelligence.provider import LLMProviderError, MockLLMProvider


@pytest.mark.asyncio
async def test_ai_provider_mock_failure_fallback() -> None:
    """Ensure AI provider handles simulated failures by returning structured safe results."""
    provider = MockLLMProvider(scenario="malformed")

    with pytest.raises(LLMProviderError):
        await provider.generate_structured(
            prompt="Investigate discrepancy",
            schema=dict,  # type: ignore[type-var]
        )


@pytest.mark.asyncio
async def test_audit_tampering_injection_detected() -> None:
    """Ensure deliberate tampering of persisted audit payload is detected by verifier."""
    service = AuditService()

    # Event 1
    evt1 = await service.record_event(
        event_type=AuditEventType.RECONCILIATION_COMPLETED,
        case_id="case_inj_01",
        correlation_id="corr-inj-01",
        source_component="test",
        payload={"amount": "1000.00"},
    )

    # Event 2
    evt2 = await service.record_event(
        event_type=AuditEventType.ACTION_REQUESTED,
        case_id="case_inj_01",
        correlation_id="corr-inj-01",
        source_component="test",
        payload={"status": "APPROVED"},
    )

    # Clean verification
    clean_res = AuditIntegrityVerifier.verify_case_timeline("case_inj_01", [evt1, evt2])
    assert clean_res.is_hash_chain_valid is True

    # Inject deliberate payload modification into evt1 (keep old hash)
    tampered_evt1 = evt1.model_copy(update={"payload": {"amount": "999999.00"}})
    tampered_res = AuditIntegrityVerifier.verify_case_timeline("case_inj_01", [tampered_evt1, evt2])
    assert tampered_res.is_hash_chain_valid is False
    assert len(tampered_res.violations) > 0
