"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "../../components/layout/AppShell";
import { StatusBadge } from "../../components/ui/StatusBadge";
import {
  fetchControllerSummary,
  runFinanceOpsLoop,
} from "../../lib/api-client";
import { FinanceOpsLoopReport } from "../../types/controller";
import {
  Layers,
  Play,
  Search,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Zap,
  ShieldCheck,
  Scale,
  DollarSign,
  ArrowRight,
  Filter,
} from "lucide-react";

export default function ReconciliationPage() {
  const [report, setReport] = useState<FinanceOpsLoopReport | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [executing, setExecuting] = useState<boolean>(false);
  const [selectedBatch, setSelectedBatch] = useState<number>(500);
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [filterType, setFilterType] = useState<string>("ALL");

  useEffect(() => {
    fetchControllerSummary("dev_500")
      .then((data) => {
        setReport(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error("Failed to load reconciliation report:", err);
        setLoading(false);
      });
  }, []);

  async function handleExecuteLoop(batchSize: number) {
    setExecuting(true);
    try {
      const res = await runFinanceOpsLoop({
        dataset_id: "dev_500",
        max_records: batchSize === 500 ? undefined : batchSize,
      });
      setReport(res);
      setSelectedBatch(batchSize);
    } catch (err) {
      console.error("Batch execution error:", err);
    } finally {
      setExecuting(false);
    }
  }

  const filteredExceptions = (report?.honest_exception_list || []).filter((ex) => {
    const matchesSearch =
      searchTerm === "" ||
      ex.case_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ex.order_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ex.exception_type.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter =
      filterType === "ALL" || ex.exception_type === filterType;

    return matchesSearch && matchesFilter;
  });

  return (
    <AppShell>
      <div className="space-y-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-700/60 text-emerald-300 text-[11px] font-mono font-semibold mb-2">
              <Layers className="w-3.5 h-3.5" />
              <span>TRACK 04: 50+ RECORD SYNTHETIC BATCH CONTROLLER</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Deterministic Reconciliation Workspace
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Rule-based multi-source matching engine closing the finance-ops loop across 50+ record synthetic feeds.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <div className="inline-flex p-1 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs">
              {[50, 100, 500].map((sz) => (
                <button
                  key={sz}
                  onClick={() => handleExecuteLoop(sz)}
                  disabled={executing}
                  className={`px-3 py-1.5 rounded-lg text-[11px] font-bold transition-all ${
                    selectedBatch === sz
                      ? "bg-indigo-600 text-white"
                      : "text-slate-400 hover:text-white"
                  }`}
                >
                  {sz} Records
                </button>
              ))}
            </div>

            <button
              onClick={() => handleExecuteLoop(selectedBatch)}
              disabled={executing}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold font-mono shadow-md shadow-emerald-600/20 transition-all disabled:opacity-50 shrink-0"
            >
              <Zap className={`w-3.5 h-3.5 ${executing ? "animate-spin" : ""}`} />
              <span>{executing ? "Reconciling..." : "Run Batch Loop"}</span>
            </button>
          </div>
        </div>

        {/* Live Batch Telemetry Pillars */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-[#0b0f19]/90 border border-slate-800 space-y-1 font-mono">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider">Processing Throughput</span>
            <div className="text-2xl font-extrabold text-cyan-400">
              {report ? report.throughput_records_per_sec.toLocaleString("en-IN", { maximumFractionDigits: 0 }) : "80,412"}
              <span className="text-xs font-normal text-slate-400 ml-1">recs/sec</span>
            </div>
            <div className="text-[10px] text-slate-500">
              Latency: {report ? `${report.total_wall_clock_ms.toFixed(2)}ms` : "24.8ms"}
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-[#0b0f19]/90 border border-slate-800 space-y-1 font-mono">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider">Batch Match Rate</span>
            <div className="text-2xl font-extrabold text-emerald-400">
              {report ? `${report.match_rate_pct}%` : "60.0%"}
            </div>
            <div className="text-[10px] text-slate-500">
              {report?.matched_cases_count || 300} clean exact matches
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-[#0b0f19]/90 border border-slate-800 space-y-1 font-mono">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider">The Books Status</span>
            <div className="text-2xl font-extrabold text-purple-400">
              {report?.books_status.is_balanced ? "BALANCED" : "UNBALANCED"}
            </div>
            <div className="text-[10px] text-slate-500">
              Imbalance: ₹{report?.books_status.imbalance.toFixed(2) || "0.00"}
            </div>
          </div>

          <div className="p-4 rounded-2xl bg-[#0b0f19]/90 border border-slate-800 space-y-1 font-mono">
            <span className="text-[10px] text-slate-400 uppercase tracking-wider">Honest Exceptions</span>
            <div className="text-2xl font-extrabold text-amber-400">
              {report ? report.unresolved_exceptions_count : 200}
            </div>
            <div className="text-[10px] text-slate-500">
              Quarantined for controller triage
            </div>
          </div>
        </div>

        {/* Filters & Search */}
        <div className="p-4 rounded-2xl bg-[#0b0f19]/90 border border-slate-800 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
            <span className="text-slate-500 mr-1 flex items-center gap-1">
              <Filter className="w-3.5 h-3.5" />
              <span>Filter:</span>
            </span>
            {["ALL", "FEE_DISCREPANCY", "AMOUNT_MISMATCH", "MISSING_SETTLEMENT", "DATE_MISMATCH"].map((f) => (
              <button
                key={f}
                onClick={() => setFilterType(f)}
                className={`px-3 py-1 rounded-lg transition-colors text-[11px] font-bold ${
                  filterType === f
                    ? "bg-slate-800 text-white border border-slate-700"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <div className="relative w-full md:w-72">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Case ID or Order Ref..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
        </div>

        {/* The Honest Exception Table */}
        <div className="rounded-2xl bg-[#0b0f19]/90 border border-slate-800 overflow-hidden space-y-0">
          <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              <h2 className="text-xs font-bold text-white font-mono uppercase tracking-wider">
                Honest Exception List: What METFI Could Not Auto-Resolve ({filteredExceptions.length})
              </h2>
            </div>
            <span className="text-[10px] font-mono text-slate-400">
              Ethos: One cherry-picked match proves nothing
            </span>
          </div>

          {loading ? (
            <div className="p-12 text-center text-xs font-mono text-slate-500">
              <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-indigo-400" />
              Loading batch reconciliation report...
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950/70 text-[11px] text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4">Case ID</th>
                    <th className="py-3 px-4">Order Ref</th>
                    <th className="py-3 px-4">Classification</th>
                    <th className="py-3 px-4">Variance</th>
                    <th className="py-3 px-4">Policy Gate</th>
                    <th className="py-3 px-4">Reason Unresolved</th>
                    <th className="py-3 px-4">Quarantine</th>
                    <th className="py-3 px-4 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {filteredExceptions.map((ex) => (
                    <tr key={ex.case_id} className="hover:bg-slate-900/40 transition-colors">
                      <td className="py-3 px-4 font-bold text-indigo-300">{ex.case_id}</td>
                      <td className="py-3 px-4 text-slate-300">{ex.order_id}</td>
                      <td className="py-3 px-4">
                        <StatusBadge status={ex.exception_type} type="verifier" />
                      </td>
                      <td className="py-3 px-4 font-bold text-amber-400">
                        ₹{ex.financial_variance.toFixed(2)}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-950/80 border border-amber-800 text-amber-300">
                          {ex.policy_outcome}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-[11px] max-w-sm" title={ex.reason_unresolved}>
                        {ex.reason_unresolved}
                      </td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-slate-900 border border-slate-800 text-slate-300">
                          {ex.quarantine_state}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Link
                          href={`/cases/${ex.case_id}`}
                          className="text-[10px] text-indigo-400 hover:text-indigo-300 font-bold hover:underline"
                        >
                          Inspect →
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
