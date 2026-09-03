/**
 * TypeScript definitions for live case details and honest exceptions.
 */

export interface CaseFinancialFacts {
  ledger_expected_amount: number;
  settled_net_amount: number;
  gross_payment_amount: number;
  fee_deducted: number;
  tax_deducted: number;
  financial_variance: number;
  variance_percentage: number;
  variance_rule_code: string;
}

export interface CaseAIAnalysis {
  root_cause_category: string;
  confidence_score: number;
  narrative_explanation: string;
  recommended_action: string;
  evidence_citations: string[];
}

export interface CaseVerifierAudit {
  status: string;
  grounded_claims: string[];
  contradiction_claims: string[];
  verification_notes: string;
  hallucination_detected: boolean;
}

export interface CasePolicyDecision {
  decision: string;
  action_type: string;
  safe_variance_cap: number;
  policy_version: string;
  justification: string;
}

export interface CaseActionExecution {
  action_id: string;
  state: string;
  idempotency_key: string;
  executed_at: string;
  side_effects: string[];
}

export interface CaseDetailFullResponse {
  case_id: string;
  order_id: string;
  classification: string;
  severity: string;
  status: string;
  summary: string;
  reconciled_at: string;

  facts: CaseFinancialFacts;
  ai_investigation: CaseAIAnalysis;
  ai_verifier: CaseVerifierAudit;
  policy: CasePolicyDecision;
  action: CaseActionExecution;

  payment_records: Record<string, any>[];
  settlement_records: Record<string, any>[];
  ledger_records: Record<string, any>[];

  sha256_audit_hash: string;
}

export interface HonestExceptionItem {
  case_id: string;
  order_id: string;
  classification: string;
  severity: string;
  status: string;
  amount: number;
  variance: number;
  reason: string;
  action_type: string;
  reconciled_at: string;
}
