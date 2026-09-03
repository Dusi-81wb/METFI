/**
 * Centralized typed API client for METFI backend endpoints.
 *
 * Strict Rule: Never fabricate metrics or return fake data on backend failures.
 * Surfacing real loading, empty, and error states truthfully.
 */

import {
  AuditIntegrityResult,
  AuditMetricsResponse,
  AuditEvent,
  ControlledAction,
  HealthResponse,
  PolicyDecision,
  ReconciliationResult,
  ReviewItem,
  UnifiedBenchmarkSummary,
  VerifiedInvestigationEnvelope,
} from "../types/models";

const BACKEND_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${BACKEND_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(options?.headers || {}),
      },
      cache: "no-store",
    });

    if (!res.ok) {
      let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          errorDetail = typeof errorJson.detail === "string" ? errorJson.detail : JSON.stringify(errorJson.detail);
        }
      } catch {
        // Fallback to text status
      }
      throw new Error(errorDetail);
    }

    return await res.json();
  } catch (error) {
    console.error(`API request failed [${endpoint}]:`, error);
    throw error;
  }
}

// ----------------------------------------------------------------------------
// Health & Telemetry
// ----------------------------------------------------------------------------

export async function fetchHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/v1/health");
}

export const fetchHealthStatus = fetchHealth;

export async function fetchAuditMetrics(): Promise<AuditMetricsResponse> {
  return request<AuditMetricsResponse>("/api/v1/audit/metrics");
}

// ----------------------------------------------------------------------------
// Audit Trail & Cryptographic Verification
// ----------------------------------------------------------------------------

export async function fetchCaseAuditTrail(
  caseId: string
): Promise<{ case_id: string; event_count: number; events: AuditEvent[] }> {
  return request<{ case_id: string; event_count: number; events: AuditEvent[] }>(
    `/api/v1/audit/cases/${encodeURIComponent(caseId)}`
  );
}

export async function verifyCaseIntegrity(
  caseId: string
): Promise<AuditIntegrityResult> {
  return request<AuditIntegrityResult>(
    `/api/v1/audit/cases/${encodeURIComponent(caseId)}/verify`
  );
}

export async function fetchAuditEventById(
  eventId: string
): Promise<AuditEvent> {
  return request<AuditEvent>(`/api/v1/audit/events/${encodeURIComponent(eventId)}`);
}

// ----------------------------------------------------------------------------
// Review Queue
// ----------------------------------------------------------------------------

export async function fetchReviewQueue(
  statusFilter?: string
): Promise<{ items: ReviewItem[]; total_count: number }> {
  const query = statusFilter ? `?status=${encodeURIComponent(statusFilter)}` : "";
  const res = await request<any>(`/api/v1/actions/review-queue${query}`);
  if (Array.isArray(res)) {
    return { items: res, total_count: res.length };
  }
  if (res && Array.isArray(res.items)) {
    return { items: res.items, total_count: res.total_count ?? res.items.length };
  }
  return { items: [], total_count: 0 };
}

export async function claimReviewItem(
  reviewId: string,
  claimedBy: string
): Promise<ReviewItem> {
  return request<ReviewItem>(
    `/api/v1/actions/review-queue/${encodeURIComponent(reviewId)}/claim`,
    {
      method: "POST",
      body: JSON.stringify({ claimed_by: claimedBy }),
    }
  );
}

export async function resolveReviewItem(
  reviewId: string,
  resolutionAction: string,
  resolvedBy: string,
  notes: string
): Promise<ReviewItem> {
  return request<ReviewItem>(
    `/api/v1/actions/review-queue/${encodeURIComponent(reviewId)}/resolve`,
    {
      method: "POST",
      body: JSON.stringify({
        resolution_action: resolutionAction,
        resolved_by: resolvedBy,
        notes: notes,
      }),
    }
  );
}

export async function escalateReviewItem(
  reviewId: string,
  escalatedBy: string,
  reason: string
): Promise<ReviewItem> {
  return request<ReviewItem>(
    `/api/v1/actions/review-queue/${encodeURIComponent(reviewId)}/escalate`,
    {
      method: "POST",
      body: JSON.stringify({
        escalated_by: escalatedBy,
        reason: reason,
      }),
    }
  );
}

// ----------------------------------------------------------------------------
// Policy & Action Execution
// ----------------------------------------------------------------------------

export async function evaluatePolicyDecision(
  payload: Record<string, unknown>
): Promise<{ decision: PolicyDecision }> {
  return request<{ decision: PolicyDecision }>("/api/v1/policy/evaluate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function authorizeActionRequest(
  payload: Record<string, unknown>
): Promise<{ action: ControlledAction; audit_event?: AuditEvent }> {
  return request<{ action: ControlledAction; audit_event?: AuditEvent }>(
    "/api/v1/actions/authorize",
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

export async function executeAuthorizedAction(
  actionId: string,
  payload: Record<string, unknown>
): Promise<{ action: ControlledAction; result: Record<string, unknown> }> {
  return request<{ action: ControlledAction; result: Record<string, unknown> }>(
    "/api/v1/actions/execute",
    {
      method: "POST",
      body: JSON.stringify({ action_id: actionId, ...payload }),
    }
  );
}

// ----------------------------------------------------------------------------
// Reconciliation & AI Investigation
// ----------------------------------------------------------------------------

export async function runInvestigation(
  payload: Record<string, unknown>
): Promise<VerifiedInvestigationEnvelope> {
  return request<VerifiedInvestigationEnvelope>("/api/v1/investigation/investigate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function runReconciliationMatching(
  payload: Record<string, unknown>
): Promise<{ results: ReconciliationResult[]; total_cases: number }> {
  return request<{ results: ReconciliationResult[]; total_cases: number }>(
    "/api/v1/reconciliation/run",
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

// ----------------------------------------------------------------------------
// Evaluation & Governance Benchmarks
// ----------------------------------------------------------------------------

export async function fetchBenchmarkSummary(): Promise<UnifiedBenchmarkSummary> {
  return request<UnifiedBenchmarkSummary>("/api/v1/benchmarks/summary");
}

export async function runBenchmarks(): Promise<UnifiedBenchmarkSummary> {
  return request<UnifiedBenchmarkSummary>("/api/v1/benchmarks/run", {
    method: "POST",
  });
}

// ----------------------------------------------------------------------------
// Sample Data & Live Randomizer
// ----------------------------------------------------------------------------

import {
  DatasetMetadata,
  SampleDataResponse,
  RandomGenerationRequest,
  RandomGenerationResponse,
} from "../types/data";

export async function fetchAvailableDatasets(): Promise<DatasetMetadata[]> {
  return request<DatasetMetadata[]>("/api/v1/data/datasets");
}

export async function fetchSampleData(params: {
  dataset_id?: string;
  source?: string;
  offset?: number;
  limit?: number;
  search?: string;
}): Promise<SampleDataResponse> {
  const query = new URLSearchParams();
  if (params.dataset_id) query.set("dataset_id", params.dataset_id);
  if (params.source) query.set("source", params.source);
  if (params.offset !== undefined) query.set("offset", String(params.offset));
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.search) query.set("search", params.search);

  const qs = query.toString() ? `?${query.toString()}` : "";
  return request<SampleDataResponse>(`/api/v1/data/sample${qs}`);
}

export async function generateRandomData(
  req: RandomGenerationRequest
): Promise<RandomGenerationResponse> {
  return request<RandomGenerationResponse>("/api/v1/data/generate-random", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function testReconcileGeneratedData(payload: {
  dataset_id?: string;
  payments: Record<string, any>[];
  settlements: Record<string, any>[];
  ledger_entries: Record<string, any>[];
}): Promise<{ results: ReconciliationResult[]; total_cases?: number; performance_metrics?: any }> {
  return request<{ results: ReconciliationResult[]; total_cases?: number; performance_metrics?: any }>(
    "/api/v1/data/test-reconciliation",
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}

// ----------------------------------------------------------------------------
// Track 04: AI Finance Controller (Books, Cash Position, 50+ Batch Loop, QA)
// ----------------------------------------------------------------------------

import {
  FinanceOpsLoopReport,
  RunFinanceOpsLoopRequest,
  SettlementQAQuery,
  SettlementQAResponse,
} from "../types/controller";

export async function fetchControllerSummary(
  datasetId: string = "dev_500"
): Promise<FinanceOpsLoopReport> {
  return request<FinanceOpsLoopReport>(
    `/api/v1/controller/summary?dataset_id=${encodeURIComponent(datasetId)}`
  );
}

export async function runFinanceOpsLoop(
  req: RunFinanceOpsLoopRequest
): Promise<FinanceOpsLoopReport> {
  return request<FinanceOpsLoopReport>("/api/v1/controller/run-loop", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function askSettlementQA(
  req: SettlementQAQuery
): Promise<SettlementQAResponse> {
  return request<SettlementQAResponse>("/api/v1/controller/qa", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

// ----------------------------------------------------------------------------
// Microsoft Purview-style Rule Studio & Governance Center
// ----------------------------------------------------------------------------

import {
  CustomRule,
  CreateRuleRequest,
  ToggleRuleRequest,
} from "../types/rules";

export async function fetchRules(
  ruleType?: string,
  isEnabled?: boolean
): Promise<CustomRule[]> {
  const params = new URLSearchParams();
  if (ruleType) params.append("rule_type", ruleType);
  if (isEnabled !== undefined) params.append("is_enabled", String(isEnabled));
  const qs = params.toString() ? `?${params.toString()}` : "";
  return request<CustomRule[]>(`/api/v1/rules${qs}`);
}

export async function createCustomRule(
  req: CreateRuleRequest
): Promise<CustomRule> {
  return request<CustomRule>("/api/v1/rules", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export async function toggleRule(
  ruleId: string,
  isEnabled: boolean
): Promise<CustomRule> {
  return request<CustomRule>(`/api/v1/rules/${encodeURIComponent(ruleId)}/toggle`, {
    method: "PATCH",
    body: JSON.stringify({ is_enabled: isEnabled }),
  });
}

export async function deleteCustomRule(
  ruleId: string
): Promise<{ status: string; rule_id: string }> {
  return request<{ status: string; rule_id: string }>(
    `/api/v1/rules/${encodeURIComponent(ruleId)}`,
    { method: "DELETE" }
  );
}

export async function resetRules(): Promise<CustomRule[]> {
  return request<CustomRule[]>("/api/v1/rules/reset", {
    method: "POST",
  });
}

// ----------------------------------------------------------------------------
// Live Case Detail & Honest Exceptions (Track 04)
// ----------------------------------------------------------------------------

import { CaseDetailFullResponse, HonestExceptionItem } from "../types/case_detail";

export async function fetchCaseDetail(
  caseId: string,
  datasetId: string = "dev_500"
): Promise<CaseDetailFullResponse> {
  return request<CaseDetailFullResponse>(
    `/api/v1/reconciliation/cases/${encodeURIComponent(caseId)}?dataset_id=${encodeURIComponent(datasetId)}`
  );
}

export async function fetchHonestExceptions(
  datasetId: string = "dev_500",
  limit: number = 50
): Promise<HonestExceptionItem[]> {
  return request<HonestExceptionItem[]>(
    `/api/v1/reconciliation/exceptions?dataset_id=${encodeURIComponent(datasetId)}&limit=${limit}`
  );
}





