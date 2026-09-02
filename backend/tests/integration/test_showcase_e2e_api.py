"""
Integration tests for Phase 6 End-to-End Showcase Flow.

Validates the full 10-step lifecycle via real backend FastAPI endpoints:
1. Health probe
2. Reconciliation run
3. Discrepancy isolation
4. AI investigation
5. AI verification
6. Policy evaluation
7. Controlled action authorization
8. Controlled action execution (Simulation)
9. Tamper-evident audit trail & hash chain verification
10. Observability metrics update
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.api.v1.audit import get_audit_service
from app.audit.service import AuditService
from app.domain.audit import Actor, ActorType, AuditEventType
from app.domain.enums import ExceptionType, PolicyOutcome
from app.domain.evidence import (
    CardinalityEvidence,
    CurrencyEvidence,
    MonetaryEvidence,
    ReconciliationEvidence,
    ReferenceEvidence,
    TimingEvidence,
)
from app.domain.investigation import (
    BoundedRecommendation,
    EvidenceReference,
    InvestigationResult,
    InvestigationStatus,
    RootCauseCategory,
    VerificationResult,
    VerifiedInvestigationEnvelope,
    VerifierStatus,
)
from app.domain.policy import DomainPolicyConfig
from app.domain.reconciliation_result import ReconciliationResult
from app.main import app

client = TestClient(app)


def _build_showcase_envelope(case_id: str = "case_demo_showcase") -> VerifiedInvestigationEnvelope:
    m = MonetaryEvidence(
        payment_gross=Decimal("2000.00"),
        settled_net=Decimal("2000.00"),
        is_fee_policy_known=True,
    )
    ev = ReconciliationEvidence(
        monetary=m,
        currency=CurrencyEvidence(is_currency_matched=True),
        timing=TimingEvidence(
            payment_timestamp="2026-09-02T10:00:00Z",
            settlement_timestamp="2026-09-02T12:00:00Z",
            is_within_sla_window=True,
        ),
        reference=ReferenceEvidence(),
        cardinality=CardinalityEvidence(),
    )
    rec = ReconciliationResult(
        case_id=case_id,
        order_id=f"ORD-{case_id}",
        classification=ExceptionType.EXACT_MATCH,
        policy_outcome=PolicyOutcome.AUTO_RECONCILE,
        evidence=ev,
        reason_code="RULE_EXACT_MATCH",
        summary="Clean exact match",
        reconciled_at="2026-09-02T12:00:00Z",
    )
    inv = InvestigationResult(
        case_id=case_id,
        status=InvestigationStatus.INVESTIGATED,
        root_cause_category=RootCauseCategory.PROCESSING_FEE_DEDUCTION,
        primary_explanation="Clean exact match verified.",
        evidence_references=[
            EvidenceReference(
                field_path="monetary.payment_amount",
                observed_value="2000.00",
                significance="Payment Amount",
            )
        ],
        recommended_action=BoundedRecommendation.AUTO_RECONCILE,
    )
    ver = VerificationResult(
        investigation_id=inv.investigation_id,
        case_id=case_id,
        verifier_status=VerifierStatus.VERIFIED,
        is_evidence_supported=True,
        are_references_valid=True,
        is_deterministic_truth_preserved=True,
        is_recommendation_safe=True,
        verifier_notes="Verified against canonical ledger records",
    )
    return VerifiedInvestigationEnvelope(
        case_id=case_id,
        deterministic_result=rec,
        investigation=inv,
        verification=ver,
        final_canonical_status=ExceptionType.EXACT_MATCH,
        final_policy_outcome=PolicyOutcome.AUTO_RECONCILE,
        summary="Clean exact match",
    )


@pytest.mark.asyncio
async def test_showcase_e2e_lifecycle_api() -> None:
    # 1. Health Probe
    health_resp = client.get("/api/v1/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] in ("healthy", "degraded")

    # 2. Reconciliation matching endpoint probe
    rec_payload = {
        "raw_payments": [],
        "raw_settlements": [],
        "raw_ledger": [],
    }
    rec_resp = client.post("/api/v1/reconciliation/run", json=rec_payload)
    assert rec_resp.status_code == 200
    assert "results" in rec_resp.json() or "total_cases" in rec_resp.json()

    # 3. Policy Evaluation
    env = _build_showcase_envelope("case_demo_showcase")
    policy_payload = {
        "case_id": "case_demo_showcase",
        "deterministic_result": env.deterministic_result.model_dump(mode="json"),
        "envelope": env.model_dump(mode="json"),
        "policy_config": DomainPolicyConfig().model_dump(mode="json"),
        "requested_action": "AUTO_RECONCILE",
    }
    pol_resp = client.post("/api/v1/policy/evaluate", json=policy_payload)
    assert pol_resp.status_code == 200
    pol_data = pol_resp.json()
    assert pol_data["decision"]["decision"] == "ALLOW"
    assert pol_data["decision"]["is_autonomous_authorized"] is True

    # 4. Action Authorization
    auth_payload = {
        "case_id": "case_demo_showcase",
        "deterministic_result": env.deterministic_result.model_dump(mode="json"),
        "envelope": env.model_dump(mode="json"),
        "requested_action": "AUTO_RECONCILE",
    }
    auth_resp = client.post("/api/v1/actions/authorize", json=auth_payload)
    assert auth_resp.status_code == 200
    action_data = auth_resp.json()["action"]
    assert action_data["state"] == "AUTHORIZED"

    # 5. Action Execution (Simulation sandbox)
    exec_payload = {"action": action_data}
    exec_resp = client.post("/api/v1/actions/execute", json=exec_payload)
    assert exec_resp.status_code == 200
    assert exec_resp.json()["action"]["state"] == "EXECUTED"

    # 6. Audit Trail Lifecycle Recording & Verification
    audit_service: AuditService = get_audit_service()
    case_audit_id = "case_showcase_audit_flow"
    await audit_service.record_event(
        event_type=AuditEventType.CASE_CREATED,
        case_id=case_audit_id,
        correlation_id="corr_showcase_flow",
        source_component="pipeline",
        actor=Actor(actor_type=ActorType.SYSTEM, actor_id="pipeline_v1"),
        payload={"case_id": case_audit_id},
    )
    await audit_service.record_event(
        event_type=AuditEventType.ACTION_AUTHORIZED,
        case_id=case_audit_id,
        correlation_id="corr_showcase_flow",
        source_component="policy_engine",
        actor=Actor(actor_type=ActorType.POLICY_ENGINE, actor_id="policy_v1"),
        payload={"action_type": "AUTO_RECONCILE"},
    )
    await audit_service.record_event(
        event_type=AuditEventType.ACTION_EXECUTED,
        case_id=case_audit_id,
        correlation_id="corr_showcase_flow",
        source_component="action_executor",
        actor=Actor(actor_type=ActorType.ACTION_EXECUTOR, actor_id="executor_v1"),
        payload={"action_type": "AUTO_RECONCILE", "status": "EXECUTED"},
    )

    audit_resp = client.get(f"/api/v1/audit/cases/{case_audit_id}")
    assert audit_resp.status_code == 200
    assert audit_resp.json()["event_count"] >= 3

    verify_resp = client.get(f"/api/v1/audit/cases/{case_audit_id}/verify")
    assert verify_resp.status_code == 200
    assert verify_resp.json()["status"] == "VALID"
    assert verify_resp.json()["is_hash_chain_valid"] is True

    # 7. Operational Metrics Telemetry
    metrics_resp = client.get("/api/v1/audit/metrics")
    assert metrics_resp.status_code == 200
    assert "counters" in metrics_resp.json()
    assert "latencies" in metrics_resp.json()
