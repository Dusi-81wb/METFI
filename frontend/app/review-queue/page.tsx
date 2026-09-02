"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "../../components/layout/AppShell";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { fetchReviewQueue, claimReviewItem, resolveReviewItem, escalateReviewItem } from "../../lib/api-client";
import { ReviewItem } from "../../types/models";
import {
  ListTodo,
  CheckCircle,
  AlertOctagon,
  UserCheck,
  ArrowUpRight,
  Search,
  Filter,
  ShieldCheck,
  ChevronRight,
  AlertTriangle,
} from "lucide-react";

export default function ReviewQueuePage() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [priorityFilter, setPriorityFilter] = useState("ALL");
  const [searchTerm, setSearchTerm] = useState("");

  async function loadQueue() {
    try {
      setLoading(true);
      const data = await fetchReviewQueue();
      setItems(data.items || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load review queue");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadQueue();
  }, []);

  async function handleClaim(reviewId: string) {
    try {
      setActionLoading(reviewId);
      await claimReviewItem(reviewId, "user_fin_controller");
      await loadQueue();
    } catch (err) {
      alert(`Claim failed: ${err instanceof Error ? err.message : err}`);
    } finally {
      setActionLoading(null);
    }
  }

  async function handleResolve(reviewId: string) {
    try {
      setActionLoading(reviewId);
      await resolveReviewItem(reviewId, "AUTO_RECONCILE", "user_fin_controller", "Verified bank statement manually.");
      await loadQueue();
    } catch (err) {
      alert(`Resolution failed: ${err instanceof Error ? err.message : err}`);
    } finally {
      setActionLoading(null);
    }
  }

  async function handleEscalate(reviewId: string) {
    try {
      setActionLoading(reviewId);
      await escalateReviewItem(reviewId, "user_fin_controller", "Unresolved variance exceeds standard tolerance.");
      await loadQueue();
    } catch (err) {
      alert(`Escalation failed: ${err instanceof Error ? err.message : err}`);
    } finally {
      setActionLoading(null);
    }
  }

  const filteredItems = items.filter((it) => {
    const matchPriority = priorityFilter === "ALL" || it.priority === priorityFilter;
    const matchSearch =
      searchTerm === "" ||
      it.review_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      it.case_id.toLowerCase().includes(searchTerm.toLowerCase());
    return matchPriority && matchSearch;
  });

  return (
    <AppShell>
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-amber-950/80 border border-amber-700/60 text-amber-300 text-[11px] font-mono font-semibold mb-2">
              <ListTodo className="w-3.5 h-3.5" />
              <span>HUMAN-IN-THE-LOOP CONTROL</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Controller Review Queue
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Human controller triage queue for high-value variances, policy rejections, and ambiguous matches.
            </p>
          </div>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-200 text-xs font-mono">
            {error}
          </div>
        )}

        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Review ID or Case ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-[#0b0f19] border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="bg-[#0b0f19] border border-slate-800 text-xs text-slate-300 rounded-xl px-3 py-2.5 font-mono focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Priorities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>
        </div>

        {/* Review Items List */}
        <div className="space-y-3.5">
          {loading ? (
            <div className="p-12 text-center text-slate-400 font-mono text-xs bg-[#0b0f19]/80 rounded-2xl border border-slate-800">
              Loading active review queue from backend...
            </div>
          ) : filteredItems.length > 0 ? (
            filteredItems.map((item) => (
              <div
                key={item.review_id}
                className="p-5 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
              >
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="font-mono text-sm font-extrabold text-white">{item.review_id}</span>
                    <StatusBadge status={item.priority} type="priority" showIcon />
                    <StatusBadge status={item.status} type="action" showIcon />
                  </div>
                  <div className="text-xs text-slate-300 font-sans">
                    <span className="font-mono text-slate-400">Related Case: </span>
                    <Link href={`/cases/${item.case_id}`} className="text-indigo-400 hover:text-indigo-300 font-mono font-bold hover:underline">
                      {item.case_id} →
                    </Link>
                  </div>
                  <div className="text-xs text-slate-400 font-sans">
                    <span className="font-mono text-slate-500">Reasons: </span>
                    <span className="text-slate-300">{item.reasons.join(", ")}</span>
                  </div>
                </div>

                {/* Controller Action Controls */}
                <div className="flex flex-wrap items-center gap-2 shrink-0">
                  {item.status === "PENDING" && (
                    <button
                      onClick={() => handleClaim(item.review_id)}
                      disabled={actionLoading === item.review_id}
                      className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors font-mono"
                    >
                      <UserCheck className="w-3.5 h-3.5 text-cyan-400" />
                      <span>Claim</span>
                    </button>
                  )}
                  {item.status !== "RESOLVED" && item.status !== "ESCALATED" && (
                    <>
                      <button
                        onClick={() => handleResolve(item.review_id)}
                        disabled={actionLoading === item.review_id}
                        className="px-3.5 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1.5 transition-colors font-mono shadow-md shadow-emerald-600/20"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        <span>Resolve</span>
                      </button>
                      <button
                        onClick={() => handleEscalate(item.review_id)}
                        disabled={actionLoading === item.review_id}
                        className="px-3.5 py-2 rounded-xl bg-rose-950/80 border border-rose-700 hover:bg-rose-900 text-rose-200 text-xs font-bold flex items-center gap-1.5 transition-colors font-mono"
                      >
                        <AlertOctagon className="w-3.5 h-3.5 text-rose-400" />
                        <span>Escalate</span>
                      </button>
                    </>
                  )}
                </div>
              </div>
            ))
          ) : (
            <div className="p-12 rounded-2xl bg-[#0b0f19]/60 border border-slate-800/80 text-center text-slate-400 font-mono text-xs space-y-2">
              <CheckCircle className="w-8 h-8 text-emerald-400 mx-auto" />
              <p className="font-bold text-slate-200">Review queue is currently clear.</p>
              <p className="text-slate-500">All financial exceptions have been resolved or automated.</p>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
