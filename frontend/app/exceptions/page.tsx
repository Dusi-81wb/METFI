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
      <div className="space-y-6">
        {/* Top Header Banner */}
        <div className="p-6 rounded-2xl bg-white border border-slate-200 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-rose-50 border border-rose-200 text-rose-700 text-[10px] font-mono font-bold mb-1.5">
              <AlertTriangle className="w-3 h-3 text-rose-600" />
              <span>HONEST EXCEPTION LIST (TRACK 04)</span>
            </div>
            <h1 className="text-xl md:text-2xl font-bold text-slate-900 tracking-tight">
              Financial Exceptions Manager
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Non-cherry-picked triage board displaying unresolvable discrepancies, fee leakages, and timing cut-offs.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={loadExceptions}
              disabled={loading}
              className="px-3.5 py-2 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-xs font-mono text-slate-700 flex items-center gap-2 transition-colors shadow-xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin text-indigo-600" : ""}`} />
              <span>Refresh Feed</span>
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Case ID, Order ID, or reason..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-white border border-slate-200 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-400 font-mono shadow-xs"
            />
          </div>

          <div className="flex items-center gap-2 flex-wrap sm:flex-nowrap">
            <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-xl px-3 py-1 shadow-xs">
              <Filter className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="bg-transparent text-xs text-slate-700 font-mono focus:outline-none py-1.5"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical</option>
                <option value="HIGH">High</option>
                <option value="MEDIUM">Medium</option>
              </select>
            </div>

            <div className="flex items-center gap-1.5 bg-white border border-slate-200 rounded-xl px-3 py-1 shadow-xs">
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={classFilter}
                onChange={(e) => setClassFilter(e.target.value)}
                className="bg-transparent text-xs text-slate-700 font-mono focus:outline-none py-1.5"
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
          <div className="p-12 rounded-2xl bg-white border border-slate-200 text-center space-y-3 shadow-xs">
            <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
            <p className="text-sm font-mono text-slate-800">
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
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs font-mono text-slate-500 px-1">
              <span>Showing {filtered.length} of {exceptions.length} honest exceptions</span>
              <span className="text-slate-400">Click any card to inspect full agent story</span>
            </div>

            {filtered.map((exc) => (
              <div
                key={exc.case_id}
                className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-indigo-300 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xs"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex flex-wrap items-center gap-2.5">
                    <span className="font-mono text-sm font-bold text-slate-900">{exc.case_id}</span>
                    <span className="text-xs font-mono text-indigo-600 font-semibold">{exc.order_id}</span>
                    <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                      exc.severity === "CRITICAL"
                        ? "bg-rose-50 text-rose-700 border-rose-200"
                        : exc.severity === "HIGH"
                        ? "bg-amber-50 text-amber-700 border-amber-200"
                        : "bg-blue-50 text-blue-700 border-blue-200"
                    }`}>
                      {exc.severity}
                    </span>
                    <StatusBadge status={exc.classification} type="priority" />
                    <span className="text-[10px] font-mono text-slate-600 px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
                      Action: {exc.action_type}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600 font-sans leading-relaxed">{exc.reason}</p>

                  <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-slate-500 pt-1">
                    <span>Gross Volume: <strong className="text-slate-900">{formatINR(exc.amount)}</strong></span>
                    <span>Discrepancy: <strong className="text-rose-600">{formatINR(exc.variance)}</strong></span>
                    <span>Reconciled: <span className="text-slate-400">{exc.reconciled_at}</span></span>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <Link
                    href={`/cases/${exc.case_id}`}
                    className="px-3.5 py-2 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 hover:border-indigo-300 text-slate-700 hover:text-indigo-600 text-xs font-semibold font-mono flex items-center gap-2 transition-all shadow-xs"
                  >
                    <span>Inspect Story</span>
                    <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
                  </Link>
                </div>
              </div>
            ))}

            {filtered.length === 0 && (
              <div className="p-12 rounded-2xl bg-white border border-slate-200 text-center text-xs font-mono text-slate-400 shadow-xs">
                No exceptions match the selected filter criteria.
              </div>
            )}
          </div>
        )}
      </div>
    </AppShell>
  );
}
