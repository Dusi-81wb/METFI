"use client";

import React, { useState } from "react";
import Link from "next/link";
import { AppShell } from "../../components/layout/AppShell";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { AlertTriangle, ArrowUpRight, Search, Filter, ChevronRight } from "lucide-react";

export default function ExceptionsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [severityFilter, setSeverityFilter] = useState("ALL");

  const sampleExceptions = [
    {
      caseId: "case_demo_101",
      orderId: "ORD-99812-IN",
      type: "FEE_VARIANCE",
      amount: "₹10,000.00",
      variance: "-₹50.00",
      reason: "Gateway fee variance within standard 0.5% merchant tier limit.",
      severity: "MEDIUM",
      status: "RESOLVED",
      timestamp: "2026-09-02T07:12:00Z",
    },
    {
      caseId: "case_demo_102",
      orderId: "ORD-99813-IN",
      type: "TIMING_SLA_BREACH",
      amount: "₹4,500.00",
      variance: "₹0.00",
      reason: "Settlement delayed past 48h SLA window.",
      severity: "HIGH",
      status: "PENDING_REVIEW",
      timestamp: "2026-09-02T06:40:00Z",
    },
    {
      caseId: "case_demo_103",
      orderId: "ORD-99814-IN",
      type: "MISSING_SETTLEMENT",
      amount: "₹18,200.00",
      variance: "-₹18,200.00",
      reason: "Ledger transaction exists with no matching settlement from acquirer.",
      severity: "CRITICAL",
      status: "ESCALATED",
      timestamp: "2026-09-02T05:20:00Z",
    },
  ];

  const filtered = sampleExceptions.filter((e) => {
    const matchSev = severityFilter === "ALL" || e.severity === severityFilter;
    const matchSearch =
      searchTerm === "" ||
      e.caseId.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.orderId.toLowerCase().includes(searchTerm.toLowerCase());
    return matchSev && matchSearch;
  });

  return (
    <AppShell>
      <div className="space-y-8 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-amber-950/80 border border-amber-700/60 text-amber-300 text-[11px] font-mono font-semibold mb-2">
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>DISCREPANCY ISOLATION</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Financial Exceptions Manager
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Dedicated triage dashboard for variances, timing delays, and un-reconciled transactions.
            </p>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search by Case ID or Order ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-4 py-2.5 rounded-xl bg-[#0b0f19] border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-slate-500" />
            <select
              value={severityFilter}
              onChange={(e) => setSeverityFilter(e.target.value)}
              className="bg-[#0b0f19] border border-slate-800 text-xs text-slate-300 rounded-xl px-3 py-2.5 font-mono focus:outline-none focus:border-indigo-500"
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
            </select>
          </div>
        </div>

        {/* Exceptions List */}
        <div className="space-y-3.5">
          {filtered.map((exc) => (
            <div
              key={exc.caseId}
              className="p-5 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-1.5">
                <div className="flex flex-wrap items-center gap-2.5">
                  <span className="font-mono text-sm font-extrabold text-white">{exc.caseId}</span>
                  <span className="text-xs font-mono text-indigo-400 font-semibold">{exc.orderId}</span>
                  <StatusBadge status={exc.severity} type="priority" showIcon />
                  <StatusBadge status={exc.type} type="fact" />
                </div>
                <p className="text-xs text-slate-300 font-sans">{exc.reason}</p>
                <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-slate-400">
                  <span>Gross: <strong className="text-white">{exc.amount}</strong></span>
                  <span>Variance: <strong className="text-amber-400">{exc.variance}</strong></span>
                  <span>Detected: <span className="text-slate-500">{exc.timestamp}</span></span>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <Link
                  href={`/cases/${exc.caseId}`}
                  className="px-4 py-2 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-slate-200 text-xs font-semibold font-mono flex items-center gap-1.5 transition-colors"
                >
                  <span>Inspect Story</span>
                  <ChevronRight className="w-3.5 h-3.5 text-indigo-400" />
                </Link>
              </div>
            </div>
          ))}
        </div>
      </div>
    </AppShell>
  );
}
