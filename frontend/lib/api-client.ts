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

