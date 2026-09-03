"""
Pydantic schema for dynamic case detail deep-dive with multi-source evidence,
AI investigation, verifier safety audit, and policy action authorization.
"""

from typing import Any
from pydantic import BaseModel, Field


class CaseFinancialFacts(BaseModel):
    """Authoritative mathematical numbers isolated by deterministic reconciliation."""

    ledger_expected_amount: float = Field(description="Expected amount in Merchant General Ledger (₹)")
    settled_net_amount: float = Field(description="Net payout transferred by Acquirer Bank (₹)")
    gross_payment_amount: float = Field(description="Gross volume captured by Payment Gateway (₹)")
    fee_deducted: float = Field(description="Gateway processing fee deducted (₹)")
    tax_deducted: float = Field(description="Statutory tax deducted on fee (₹)")
    financial_variance: float = Field(description="Exact mathematical variance delta (₹)")
    variance_percentage: float = Field(description="Variance as percentage of gross volume")
    variance_rule_code: str = Field(description="Deterministic rule code that flagged the discrepancy")


class CaseAIAnalysis(BaseModel):
    """Live root cause analysis and hypothesis from the Autonomous AI Investigator."""

    root_cause_category: str
    confidence_score: float
    narrative_explanation: str
    recommended_action: str
    evidence_citations: list[str] = Field(default_factory=list)


class CaseVerifierAudit(BaseModel):
    """Adversarial mathematical verification certifying grounding and hallucination prevention."""

    status: str = Field(description="VERIFIED, REJECTED, or UNVERIFIED")
    grounded_claims: list[str] = Field(default_factory=list)
    contradiction_claims: list[str] = Field(default_factory=list)
    verification_notes: str = Field(default="")
    hallucination_detected: bool = Field(default=False)


class CasePolicyDecision(BaseModel):
    """Corporate governance policy evaluation for bounded action authorization."""

    decision: str = Field(description="ALLOW, DENY, or REVIEW_REQUIRED")
    action_type: str = Field(description="AUTO_RECONCILE, REVIEW_REQUIRED, or ESCALATE")
    safe_variance_cap: float = Field(description="Maximum permissible variance limit under policy (₹)")
    policy_version: str = Field(description="Active corporate policy ruleset version")
    justification: str = Field(description="Policy rule reason and justification")


class CaseActionExecution(BaseModel):
    """Controlled execution state machine tracking idempotency and side-effects."""

    action_id: str
    state: str = Field(description="EXECUTED, AUTHORIZED, or ENQUEUED_REVIEW")
    idempotency_key: str = Field(description="SHA-256 cryptographic idempotency token")
    executed_at: str
    side_effects: list[str] = Field(default_factory=list)


class CaseDetailFullResponse(BaseModel):
    """Complete, unified dynamic case record satisfying Track 04 requirements."""

    case_id: str
    order_id: str
    classification: str
    severity: str
    status: str
    summary: str
    reconciled_at: str

    facts: CaseFinancialFacts
    ai_investigation: CaseAIAnalysis
    ai_verifier: CaseVerifierAudit
    policy: CasePolicyDecision
    action: CaseActionExecution

    payment_records: list[dict[str, Any]] = Field(default_factory=list)
    settlement_records: list[dict[str, Any]] = Field(default_factory=list)
    ledger_records: list[dict[str, Any]] = Field(default_factory=list)

    sha256_audit_hash: str = Field(description="Leaf hash of the immutable audit trail")
