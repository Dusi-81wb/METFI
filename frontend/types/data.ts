/**
 * Types and interfaces for Sample Data Explorer & On-Demand Randomizer.
 */

export interface DatasetMetadata {
  dataset_id: string;
  name: string;
  description: string;
  payments_count: number;
  settlements_count: number;
  ledger_count: number;
  total_records: number;
  file_size_kb: number;
  is_live_fixture: boolean;
}

export interface SampleDataResponse {
  dataset_id: string;
  source: string;
  total_count: number;
  offset: number;
  limit: number;
  payments?: Record<string, any>[];
  settlements?: Record<string, any>[];
  ledger_entries?: Record<string, any>[];
}

export interface RandomGenerationRequest {
  count: number;
  temperature: number;
  anomaly_profile: string;
  seed?: number;
}

export interface RandomGenerationResponse {
  generated_dataset_id: string;
  seed: number;
  temperature: number;
  anomaly_profile: string;
  anomaly_summary: string;
  payments: Record<string, any>[];
  settlements: Record<string, any>[];
  ledger_entries: Record<string, any>[];
  record_counts: {
    payments: number;
    settlements: number;
    ledger_entries: number;
    total: number;
  };
}
