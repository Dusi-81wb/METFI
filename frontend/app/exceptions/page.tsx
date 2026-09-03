"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { AppShell } from "../../components/layout/AppShell";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { fetchHonestExceptions } from "../../lib/api-client";
import { HonestExceptionItem } from "../../types/case_detail";
import {
  AlertTriangle,
  ArrowUpRight,
  Search,
  Filter,
  ChevronRight,
  RefreshCw,
  Layers,
  Sparkles,
} from "lucide-react";

export default function ExceptionsPage() {
  const [exceptions, setExceptions] = useState<HonestExceptionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");
  const [classFilter, setClassFilter] = useState("ALL");

  async function loadExceptions() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHonestExceptions("dev_500", 60);
      setExceptions(data);
    } catch (err: any) {
      console.error("Failed to load honest exceptions:", err);
      setError(err?.message || "Failed to load honest exceptions from pipeline");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadExceptions();
  }, []);

  const filtered = exceptions.filter((e) => {
    const matchSev = severityFilter === "ALL" || e.severity === severityFilter;
    const matchClass = classFilter === "ALL" || e.classification === classFilter;
    const matchSearch =
      searchTerm === "" ||
      e.case_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.order_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.reason.toLowerCase().includes(searchTerm.toLowerCase());
    return matchSev && matchClass && matchSearch;
  });

  const formatINR = (val: number) => {
    return `₹${val.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <AppShell>
      <div className="space-y-8 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-amber-950/80 border border-amber-700/60 text-amber-300 text-[11px] font-mono font-semibold mb-2">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>HONEST EXCEPTION LIST (TRACK 04 REQUIREMENT)</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Financial Exceptions Manager
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Non-cherry-picked triage dashboard displaying live unresolvable discrepancies, fee leakages, and timing delays.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadExceptions}
              disabled={loading}
              className="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-700 hover:bg-slate-800 text-xs font-mono text-slate-200 flex items-center gap-2 transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-indigo-400" : ""}`} />
              <span>Refresh Batch</span>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Case ID, Order ID, or reason keyword..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-[#0b0f19] border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>

          <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
            <div className="flex items-center gap-1.5 bg-[#0b0f19] border border-slate-800 rounded-xl px-3 py-1">
              <Filter className="w-3.5 h-3.5 text-slate-500" />
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-transparent text-xs text-slate-300 font-mono focus:outline-none py-1.5"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5 bg-[#0b0f19] border border-slate-800 rounded-xl px-3 py-1">
              <Layers className="w-3.5 h-3.5 text-slate-500" />
              <select
                value={classFilter}
                onChange={(e) => setClassFilter(e.target.value)}
                className="bg-transparent text-xs text-slate-300 font-mono focus:outline-none py-1.5"
              >
                <option value="ALL">All Exception Types</option>
                <option value="FEE_DISCREPANCY">Fee Discrepancy</option>
                <option value="MISSING_SETTLEMENT">Missing Settlement</option>
                <option value="DATE_MISMATCH">Date Mismatch / SLA Breach</option>
                <option value="AMOUNT_MISMATCH">Amount Mismatch</option>
                <option value="DUPLICATE_RECORD">Duplicate Record</option>
              </select>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="p-12 rounded-2xl bg-[#0b0f19]/80 border border-slate-800 text-center space-y-3">
            <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
            <p className="text-sm font-mono text-slate-300">
              Running 3-way multi-source reconciliation across 500 transactions...
            </p>
            <p className="text-xs text-slate-500 font-sans">
              Isolating honest exceptions across Gateway, Settlement, and General Ledger feeds
            </p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-800/60 space-y-3">
            <div className="flex items-center gap-2 text-rose-400 font-mono font-bold text-sm">
              <AlertTriangle className="w-5 h-5" />
              <span>Failed to load exceptions</span>
            </div>
            <p className="text-xs text-slate-300 font-sans">{error}</p>
            <button
              onClick={loadExceptions}
              className="px-3 py-1.5 rounded-lg bg-rose-900/60 border border-rose-700 text-rose-200 text-xs font-mono hover:bg-rose-800 transition-colors"
            >
              Retry Reconciling Dataset
            </button>
          </div>
        )}

        {/* Exceptions List */}
        {!loading && !error && (
          <div className="space-y-3.5">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400 px-1">
              <span>Showing {filtered.length} of {exceptions.length} honest exceptions</span>
              <span className="text-slate-500">Click any card to inspect full agent story</span>
            </div>

            {filtered.map((exc) => (
              <div
                key={exc.case_id}
                className="p-5 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 hover:border-indigo-700/60 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="font-mono text-sm font-extrabold text-white">{exc.case_id}</span>
                    <span className="text-xs font-mono text-indigo-400 font-semibold">{exc.order_id}</span>
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                      exc.severity === "CRITICAL"
                        ? "bg-rose-950/80 text-rose-300 border-rose-700/60"
                        : exc.severity === "HIGH"
                        ? "bg-amber-950/80 text-amber-300 border-amber-700/60"
                        : "bg-blue-950/80 text-blue-300 border-blue-700/60"
                    }`}>
                      {exc.severity}
                    </span>
                    <StatusBadge status={exc.classification} type="priority" />
                    <span className="text-[10px] font-mono text-slate-400 px-2 py-0.5 rounded bg-slate-900 border border-slate-800">
                      Action: {exc.action_type}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 font-sans leading-relaxed">{exc.reason}</p>

                  <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-slate-400 pt-1">
                    <span>Gross Volume: <strong className="text-white">{formatINR(exc.amount)}</strong></span>
                    <span>Discrepancy: <strong className="text-amber-400">{formatINR(exc.variance)}</strong></span>
                    <span>Reconciled: <span className="text-slate-500">{exc.reconciled_at}</span></span>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <Link
                    href={`/cases/${exc.case_id}`}
                    className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-indigo-950/80 border border-slate-700 hover:border-indigo-600 text-slate-200 hover:text-white text-xs font-semibold font-mono flex items-center gap-2 transition-all shadow-sm"
                  >
                    <span>Inspect Story</span>
                    <ChevronRight className="w-3.5 h-3.5 text-indigo-400" />
                  </Link>
                </div>
              </div>
            ))}

            {filtered.length === 0 && (
              <div className="p-12 rounded-2xl bg-[#0b0f19]/40 border border-slate-800 text-center text-xs font-mono text-slate-500">
                No exceptions match the selected filter criteria.
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
