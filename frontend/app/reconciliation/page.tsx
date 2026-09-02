"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AppShell } from "../../components/layout/AppShell";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { Layers, Play, Search, Filter, ArrowUpRight, CheckCircle2, AlertTriangle, Sparkles, ChevronRight } from "lucide-react";

export default function ReconciliationPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterType, setFilterType] = useState("ALL");

  const sampleRuns = [
    {
      id: "REC-RUN-20260902-01",
      name: "Gateway Settlement vs Bank Ledger Batch #881",
      recordsCount: 1250,
      matchedCount: 1228,
      exceptionCount: 22,
      accuracy: "98.24%",
      latency: "0.45ms",
      status: "COMPLETED",
      timestamp: "2026-09-02T07:15:00Z",
    },
    {
      id: "REC-RUN-20260902-02",
      name: "UPI QR Collections vs Settlement Statement",
      recordsCount: 3400,
      matchedCount: 3385,
      exceptionCount: 15,
      accuracy: "99.55%",
      latency: "0.82ms",
      status: "COMPLETED",
      timestamp: "2026-09-02T06:45:00Z",
    },
    {
      id: "REC-RUN-20260902-03",
      name: "Card Acquiring Interchange vs Merchant Settlement",
      recordsCount: 5200,
      matchedCount: 5188,
      exceptionCount: 12,
      accuracy: "99.76%",
      latency: "1.12ms",
      status: "COMPLETED",
      timestamp: "2026-09-02T05:30:00Z",
    },
  ];

  const filteredRuns = sampleRuns.filter((r) => {
    return (
      searchTerm === "" ||
      r.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      r.name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  });

  return (
    <AppShell>
      <div className="space-y-8 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-700/60 text-emerald-300 text-[11px] font-mono font-semibold mb-2">
              <Layers className="w-3.5 h-3.5" />
              <span>DETERMINISTIC RECONCILIATION</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Reconciliation Workspace
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Rule-based deterministic matching engine executing strict multi-source reconciliation.
            </p>
          </div>

          <Link
            href="/showcase"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold font-mono shadow-md shadow-indigo-600/20 transition-all shrink-0"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Run New Batch</span>
          </Link>
        </div>

        {/* Filters & Search */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search batches by ID or name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-[#0b0f19] border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
        </div>

        {/* Batch Runs List */}
        <div className="space-y-3.5">
          {filteredRuns.map((run) => (
            <div
              key={run.id}
              className="p-5 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2.5">
                  <span className="font-mono text-sm font-extrabold text-white">{run.id}</span>
                  <StatusBadge status="MATCHED" type="verifier" showIcon />
                </div>
                <p className="text-xs font-semibold text-slate-200">{run.name}</p>
                <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-slate-400">
                  <span>Processed: <strong className="text-white">{run.recordsCount.toLocaleString()}</strong> records</span>
                  <span>Matched: <strong className="text-emerald-400">{run.matchedCount.toLocaleString()}</strong></span>
                  <span>Exceptions: <strong className="text-amber-400">{run.exceptionCount}</strong></span>
                  <span>Speed: <strong className="text-indigo-300">{run.latency}</strong></span>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <div className="text-right font-mono">
                  <div className="text-xs text-slate-400">Match Rate</div>
                  <div className="text-base font-extrabold text-emerald-400">{run.accuracy}</div>
                </div>
                <Link
                  href={`/exceptions`}
                  className="p-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-300 hover:text-white transition-colors"
                  title="View Exceptions"
                >
                  <ChevronRight className="w-4 h-4" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
