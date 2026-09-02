"""
Integration tests for Policy Evaluation, Controlled Action Authorization, Execution,
and Controller Review Queue FastAPI routes.
"""

from decimal import Decimal

from fastapi.testclient import TestClient

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


def _build_test_envelope(case_id: str = "case_api_01") -> VerifiedInvestigationEnvelope:
    m = MonetaryEvidence(
        payment_gross=Decimal("2000.00"), settled_net=Decimal("2000.00"), is_fee_policy_known=True
    )
    ev = ReconciliationEvidence(
        monetary=m,
        currency=CurrencyEvidence(is_currency_matched=True),
        timing=TimingEvidence(
            payment_timestamp="2026-08-30T10:00:00Z",
            settlement_timestamp="2026-08-30T12:00:00Z",
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
        reconciled_at="2026-08-30T12:00:00Z",
    )
    inv = InvestigationResult(
        case_id=case_id,
        status=InvestigationStatus.INVESTIGATED,
        root_cause_category=RootCauseCategory.PROCESSING_FEE_DEDUCTION,
        primary_explanation="Clean match",
        evidence_references=[
            EvidenceReference(
                field_path="monetary.payment_amount",
                observed_value="2000.00",
                significance="Amount",
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
        verifier_notes="Verified clean match",
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


def test_api_policy_evaluate() -> None:
    env = _build_test_envelope("case_eval_01")
    payload = {
        "case_id": "case_eval_01",
        "deterministic_result": env.deterministic_result.model_dump(mode="json"),
        "envelope": env.model_dump(mode="json"),
        "policy_config": DomainPolicyConfig().model_dump(mode="json"),
        "requested_action": "AUTO_RECONCILE",
    }

    resp = client.post("/api/v1/policy/evaluate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["case_id"] == "case_eval_01"
    assert data["decision"]["decision"] == "ALLOW"
    assert data["decision"]["is_autonomous_authorized"] is True


def test_api_action_authorize_and_execute_lifecycle() -> None:
    env = _build_test_envelope("case_auth_exec_01")
    auth_payload = {
        "case_id": "case_auth_exec_01",
        "deterministic_result": env.deterministic_result.model_dump(mode="json"),
        "envelope": env.model_dump(mode="json"),
        "requested_action": "AUTO_RECONCILE",
    }

    # 1. Authorize
    auth_resp = client.post("/api/v1/actions/authorize", json=auth_payload)
    assert auth_resp.status_code == 200
    auth_data = auth_resp.json()
    action = auth_data["action"]
    assert action["state"] == "AUTHORIZED"
    assert action["authorization_status"] == "AUTHORIZED"

    # 2. Execute
    exec_payload = {"action": action}
    exec_resp = client.post("/api/v1/actions/execute", json=exec_payload)
    assert exec_resp.status_code == 200
    exec_data = exec_resp.json()
    assert exec_data["action"]["state"] == "EXECUTED"
    assert exec_data["result"]["status"] == "EXECUTED"
    assert "SETTLEMENT_RECORD_MARKED_RECONCILED" in exec_data["result"]["side_effects_simulated"]


def test_api_execute_unauthorized_action_fails_with_403() -> None:
    # Action with DENIED authorization
    action = {
        "action_id": "act_unauth_123",
        "case_id": "case_unauth_01",
        "action_type": "AUTO_RECONCILE",
        "state": "REQUESTED",
        "authorization_status": "DENIED",
        "idempotency_key": "idemp_unauth_123",
        "policy_version": "1.0.0",
        "preconditions": {},
        "evidence_references": [],
        "payload": {},
        "requested_by": "attacker",
        "rejection_reasons": ["Unapproved action"],
    }

    exec_resp = client.post("/api/v1/actions/execute", json={"action": action})
    assert exec_resp.status_code == 403
    assert "Action execution forbidden" in exec_resp.json()["detail"]


def test_api_review_queue_endpoints() -> None:
    # 1. List review queue
    list_resp = client.get("/api/v1/actions/review-queue")
    assert list_resp.status_code == 200
    assert isinstance(list_resp.json(), list)
