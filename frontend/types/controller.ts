/**
 * Types for Track 04: AI Finance Controller.
 * Covers the cash position, ledger books status, 50+ record batch finance-ops loop,
 * the honest exception list, and the Settlement Q&A agent.
 */

export interface CashPosition {
  settled_cash_bank: number;
  expected_gross_cash: number;
  contractual_fees_tax: number;
  in_transit_cash: number;
  disputed_leakage_cash: number;
  net_reconciled_cash: number;
  forward_projection_24h: number;
  forward_projection_48h: number;
}

export interface AccountBalance {
  account: string;
  debits: number;
  credits: number;
  net_balance: number;
  status: string;
}

export interface BooksStatus {
  total_debits: number;
  total_credits: number;
  imbalance: number;
  is_balanced: boolean;
  total_journal_entries: number;
  accounts: AccountBalance[];
}

export interface HonestExceptionItem {
  case_id: string;
  order_id: string;
  exception_type: string;
  financial_variance: number;
  policy_outcome: string;
  reason_unresolved: string;
  quarantine_state: string;
  root_cause_summary: string;
}

export interface FinanceOpsLoopReport {
  batch_id: string;
  records_evaluated: number;
  total_cases: number;
  matched_cases_count: number;
  unresolved_exceptions_count: number;
  match_rate_pct: number;
  resolution_rate_pct: number;
  throughput_records_per_sec: number;
  total_wall_clock_ms: number;
  measured_accuracy_pct: number;
  cash_position: CashPosition;
  books_status: BooksStatus;
  honest_exception_list: HonestExceptionItem[];
  rule_hits?: Record<string, number>;
  logic_trace?: string[];
  engine_verdict: string;
}

export interface RunFinanceOpsLoopRequest {
  dataset_id?: string;
  max_records?: number;
  payments?: Record<string, any>[];
  settlements?: Record<string, any>[];
  ledger_entries?: Record<string, any>[];
}

export interface SettlementQAQuery {
  question: string;
  dataset_id?: string;
}

export interface SettlementQAResponse {
  query: string;
  answer: string;
  financial_data: Record<string, any>;
  cited_records: string[];
  confidence: number;
}
