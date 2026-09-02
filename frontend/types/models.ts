/**
 * Frontend TypeScript domain models matching backend Pydantic schemas.
 */

export type MatchStatus = "MATCHED" | "EXCEPTION" | "AMBIGUOUS";

export type ExceptionCategory =
  | "EXACT_MATCH"
  | "AMOUNT_MISMATCH"
  | "TIMING_MISMATCH"
  | "FEE_VARIANCE"
  | "TAX_VARIANCE"
  | "CURRENCY_MISMATCH"
  | "PARTIAL_SETTLEMENT"
  | "DUPLICATE_RECORD"
  | "MISSING_LEDGER"
  | "MISSING_SETTLEMENT"
  | "MISSING_PAYMENT"
  | "FORMAT_CORRUPTION"
  | "AMBIGUOUS_MATCH"
  | "UNKNOWN_EXCEPTION";

export interface EvidenceReference {
  record_id: string;
  field_name: string;
  observed_value: unknown;
  expected_value: unknown;
  evidence_description: string;
  evidence_weight?: number;
}

export interface ReconciliationRecord {
  record_id: string;
  transaction_id: string;
  amount: number;
  currency: string;
  timestamp: string;
  source: string;
  metadata?: Record<string, unknown>;
}

export interface ReconciliationResult {
  match_id: string;
  status: MatchStatus;
  classification: ExceptionCategory;
  payment_id?: string | null;
  settlement_id?: string | null;
  ledger_id?: string | null;
  net_discrepancy: number;
  confidence_score: number;
  evidence_references: EvidenceReference[];
  rules_evaluated: string[];
  reconciled_at: string;
}

export type ActionType =
  | "AUTO_RECONCILE"
  | "MARK_FOR_REVIEW"
  | "ESCALATE"
  | "REQUEST_RETRY"
  | "REQUEST_MANUAL_VERIFICATION";

export type ActionState =
  | "REQUESTED"
  | "VALIDATING"
  | "AUTHORIZED"
  | "EXECUTING"
  | "EXECUTED"
  | "REJECTED"
  | "FAILED";

export interface ControlledAction {
  action_id: string;
  action_type: ActionType;
  state: ActionState;
  case_id: string;
  idempotency_key: string;
  reconciliation_id?: string | null;
  policy_decision_id?: string | null;
  requested_at: string;
  authorized_at?: string | null;
  executed_at?: string | null;
  rejection_reason?: string | null;
  failure_reason?: string | null;
  side_effects: string[];
}

export type PolicyDecisionOutcome = "ALLOW" | "DENY" | "REVIEW" | "UNRESOLVED";

export interface PolicyDecision {
  decision_id: string;
  case_id: string;
  outcome: PolicyDecisionOutcome;
  recommended_action: ActionType;
  evaluated_rules: string[];
  reason_codes: string[];
  policy_version: string;
  evaluated_at: string;
  autonomous_action_permitted: boolean;
}

export type VerifierStatus = "VERIFIED" | "REJECTED" | "INSUFFICIENT_EVIDENCE";

export interface AIInvestigation {
  investigation_id: string;
  case_id: string;
  provider: string;
  model_name: string;
  root_cause_explanation: string;
  primary_explanation: string;
  evidence_references: EvidenceReference[];
  recommended_action: ActionType;
  confidence_score: number;
  latency_ms: number;
  generated_at: string;
}

export interface AIVerification {
  verification_id: string;
  investigation_id: string;
  verifier_status: VerifierStatus;
  grounded_claims: string[];
  unsupported_claims: string[];
  has_contradiction: boolean;
  recommendation_safe: boolean;
  deterministic_truth_preserved: boolean;
  critique_notes: string;
  verified_at: string;
}

export interface VerifiedInvestigationEnvelope {
  investigation: AIInvestigation;
  verification: AIVerification;
  is_certified: boolean;
}

export type ReviewPriority = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type ReviewStatus = "PENDING" | "IN_REVIEW" | "RESOLVED" | "ESCALATED";

export interface ReviewItem {
  review_id: string;
  case_id: string;
  priority: ReviewPriority;
  status: ReviewStatus;
  reasons: string[];
  evidence_references: EvidenceReference[];
  investigation_summary?: string | null;
  verifier_status?: VerifierStatus | null;
  assigned_to?: string | null;
  resolution_notes?: string | null;
  created_at: string;
  claimed_at?: string | null;
  resolved_at?: string | null;
}

export type ActorType =
  | "SYSTEM"
  | "DETERMINISTIC_ENGINE"
  | "AI_INVESTIGATOR"
  | "AI_VERIFIER"
  | "POLICY_ENGINE"
  | "ACTION_EXECUTOR"
  | "HUMAN_REVIEWER";

export interface Actor {
  actor_type: ActorType;
  actor_id: string;
  display_name?: string | null;
}

export interface AuditEvent {
  event_id: string;
  event_type: string;
  case_id: string;
  correlation_id: string;
  sequence_number: number;
  timestamp: string;
  source_component: string;
  actor: Actor;
  event_version: string;
  payload: Record<string, unknown>;
  evidence_references: EvidenceReference[];
  policy_version?: string | null;
  reconciliation_id?: string | null;
  investigation_id?: string | null;
  verification_id?: string | null;
  policy_decision_id?: string | null;
  action_id?: string | null;
  review_id?: string | null;
  previous_event_hash: string;
  event_hash: string;
}

export interface AuditIntegrityResult {
  case_id: string;
  status: "VALID" | "INTEGRITY_FAILURE";
  events_verified_count: number;
  is_hash_chain_valid: boolean;
  is_sequence_monotonic: boolean;
  is_lifecycle_coherent: boolean;
  violations: string[];
  verified_at: string;
}

export interface AuditMetricsResponse {
  counters: Record<string, number>;
  errors: Record<string, number>;
  latencies: Record<
    string,
    { count: number; avg_ms: number; p95_ms: number; min_ms?: number; max_ms?: number }
  >;
}

export interface SubsystemStatus {
  data_plane?: string;
  deterministic_engine?: string;
  intelligence_layer?: string;
  policy_engine?: string;
  audit_layer?: string;
  evaluation_engine?: string;
  database?: string;
}


export interface SuiteMetric {
  label: string;
  score: string;
  target: string;
  passed: boolean;
  details?: string | null;
}

export interface EvaluationSuiteResult {
  suite_id: string;
  name: string;
  category: string;
  cases_evaluated: number;
  duration_ms: number;
  passed: boolean;
  metrics: SuiteMetric[];
}

export interface UnifiedBenchmarkSummary {
  evaluation_version: string;
  timestamp: string;
  git_head: string;
  seed: number;
  overall_status: string;
  total_suites: number;
  total_cases_evaluated: number;
  suites: EvaluationSuiteResult[];
}

export interface HealthResponse {
  status: string;
  version: string;
  environment: string;
  database?: string;
  timestamp: string;
  service?: string;
  subsystems?: SubsystemStatus;
  details?: {
    ai_provider?: string;
    default_model?: string;
    api_prefix?: string;
    [key: string]: unknown;
  };
}
