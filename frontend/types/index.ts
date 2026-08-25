export interface SubsystemStatus {
  data_plane: string;
  deterministic_engine: string;
  intelligence_layer: string;
  policy_engine: string;
  audit_layer: string;
  evaluation_engine: string;
}

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  subsystems: SubsystemStatus;
  details: {
    ai_provider?: string;
    default_model?: string;
    api_prefix?: string;
    [key: string]: unknown;
  };
}

export type ExceptionType =
  | "EXACT_MATCH"
  | "AMOUNT_MISMATCH"
  | "MISSING_SETTLEMENT"
  | "DUPLICATE_RECORD"
  | "DATE_MISMATCH"
  | "REFERENCE_MISMATCH"
  | "PARTIAL_SETTLEMENT"
  | "FEE_DISCREPANCY"
  | "CURRENCY_MISMATCH"
  | "AMBIGUOUS";

export type PolicyOutcome = "AUTO_RECONCILE" | "REVIEW_REQUIRED" | "UNRESOLVED";
