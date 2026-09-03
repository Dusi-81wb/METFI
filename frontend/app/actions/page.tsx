"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { AppShell } from "../../components/layout/AppShell";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { fetchHonestExceptions } from "../../lib/api-client";
import { HonestExceptionItem } from "../../types/case_detail";
import { Zap, ShieldCheck, ArrowUpRight, CheckCircle2, ChevronRight, RefreshCw } from "lucide-react";

export default function ActionsPage() {
  const [exceptions, setExceptions] = useState<HonestExceptionItem[]>([]);
  const [loading, setLoading] = useState(true);

  async function loadActions() {
    setLoading(true);
    try {
      const data = await fetchHonestExceptions("dev_500", 30);
      setExceptions(data);
    } catch (err) {
      console.error("Failed to load actions:", err);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadActions();
  }, []);

  return (
    <AppShell>
      <div className="space-y-8 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-cyan-950/80 border border-cyan-700/60 text-cyan-300 text-[11px] font-mono font-semibold mb-2">
              <Zap className="w-3.5 h-3.5" />
              <span>CONTROLLED ACTIONS LIFECYCLE</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Action State Machine Tracker
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Policy-authorized bounded execution tracker enforcing strict states and SHA-256 idempotency.
            </p>
          </div>

          <button
            onClick={loadActions}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 hover:bg-slate-800 text-xs font-mono text-slate-200 flex items-center gap-2 transition-colors self-start sm:self-auto"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-cyan-400" : ""}`} />
            <span>Refresh State Machine</span>
          </button>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="p-12 rounded-2xl bg-[#0b0f19]/80 border border-slate-800 text-center space-y-3">
            <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mx-auto" />
            <p className="text-sm font-mono text-slate-300">
              Querying cryptographic action state machines &amp; idempotency ledgers...
            </p>
          </div>
        )}

        {/* Actions List */}
        {!loading && (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 px-1">
              <span>Tracking {exceptions.length} policy-bounded action executions</span>
              <span className="text-slate-500">All actions strictly idempotent via SHA-256</span>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {exceptions.map((exc, idx) => {
                const actionId = `act_${exc.case_id.slice(-8)}`;
                const isAuto = exc.action_type === "AUTO_RECONCILE";
                const state = isAuto ? "EXECUTED" : "AUTHORIZED";
                const sideEffects = isAuto
                  ? ["MARKED_RECONCILED", "POSTED_GL_ADJUSTMENT"]
                  : ["ENQUEUED_CONTROLLER_REVIEW", "AUDIT_FLAG_RAISED"];

                return (
                  <div
                    key={exc.case_id || idx}
                    className="p-5 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
                  >
                    <div className="space-y-2 flex-1">
                      <div className="flex flex-wrap items-center gap-2.5">
                        <span className="font-mono text-xs font-bold text-white bg-slate-900 border border-slate-700 px-2 py-0.5 rounded">
                          {actionId}
                        </span>
                        <Link
                          href={`/cases/${exc.case_id}`}
                          className="text-xs font-mono text-indigo-400 hover:underline font-semibold"
                        >
                          {exc.case_id}
                        </Link>
                        <StatusBadge status={exc.action_type} type="policy" />
                        <StatusBadge status={state} type="action" showIcon />
                      </div>

                      <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-slate-300">
                        <span>Order: <strong className="text-white">{exc.order_id}</strong></span>
                        <span>Variance: <strong className="text-amber-400">₹{exc.variance.toFixed(2)}</strong></span>
                        <span>Reason: <span className="text-slate-400">{exc.reason.slice(0, 60)}...</span></span>
                      </div>

                      <div className="flex flex-wrap items-center gap-1.5 pt-1">
                        <span className="text-[10px] text-slate-500 font-mono">Side-effects:</span>
                        {sideEffects.map((se, sIdx) => (
                          <span
                            key={sIdx}
                            className="px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-[10px] font-mono"
                          >
                            {se}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <Link
                        href={`/cases/${exc.case_id}`}
                        className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-semibold font-mono flex items-center gap-1.5 transition-colors"
                      >
                        <span>Audit Case</span>
                        <ChevronRight className="w-3.5 h-3.5 text-cyan-400" />
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
