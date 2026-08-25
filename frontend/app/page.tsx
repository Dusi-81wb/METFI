import React from "react";
import { HealthStatusWidget } from "../components/HealthStatusWidget";
import { 
  ShieldCheck, 
  Layers, 
  Terminal, 
  ArrowRight, 
  CheckCircle,
  FileSpreadsheet,
  AlertTriangle,
  GitBranch
} from "lucide-react";

export default function HomePage() {
  const taxonomyClasses = [
    { label: "EXACT_MATCH", type: "clean", count: "Target: 65%" },
    { label: "AMOUNT_MISMATCH", type: "variance", count: "Target: 10%" },
    { label: "MISSING_SETTLEMENT", type: "timing", count: "Target: 6%" },
    { label: "DUPLICATE_RECORD", type: "duplicate", count: "Target: 5%" },
    { label: "DATE_MISMATCH", type: "timing", count: "Target: 5%" },
    { label: "REFERENCE_MISMATCH", type: "metadata", count: "Target: 4%" },
    { label: "PARTIAL_SETTLEMENT", type: "variance", count: "Target: 3%" },
    { label: "FEE_DISCREPANCY", type: "fee", count: "Target: 2%" },
    { label: "CURRENCY_MISMATCH", type: "currency", count: "Target: 2.5%" },
    { label: "AMBIGUOUS", type: "reasoning", count: "Target: 2.5%" },
  ];

  return (
    <div className="space-y-10">
      {/* Hero Section */}
      <div className="rounded-2xl border border-slate-800 bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900 p-8 shadow-2xl relative overflow-hidden">
        <div className="absolute right-0 top-0 -mt-8 -mr-8 h-64 w-64 rounded-full bg-blue-600/10 blur-3xl pointer-events-none"></div>
        <div className="max-w-3xl space-y-4 relative z-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/30 bg-blue-950/40 px-3 py-1 text-xs font-semibold text-blue-400">
            <span>Razorpay AI Buildathon</span>
            <span className="text-slate-500">•</span>
            <span>Track 04: AI Finance Controller</span>
          </div>

          <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
            Autonomous Multi-Source Financial Reconciliation
          </h1>

          <p className="text-base text-slate-300 leading-relaxed">
            METFI enforces a strict separation of concerns: <span className="font-semibold text-white">deterministic financial rules</span> own mathematical truth and policy gates, while <span className="font-semibold text-blue-400">bounded AI agents</span> investigate anomalies, correlate multi-source evidence, and explain discrepancies with full audit lineage.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-4 text-xs font-mono text-slate-400">
            <div className="flex items-center gap-1.5 bg-slate-950/80 px-3 py-1.5 rounded-md border border-slate-800">
              <span className="h-2 w-2 rounded-full bg-blue-400"></span>
              <span>FastAPI Backend :8000</span>
            </div>
            <div className="flex items-center gap-1.5 bg-slate-950/80 px-3 py-1.5 rounded-md border border-slate-800">
              <span className="h-2 w-2 rounded-full bg-indigo-400"></span>
              <span>Next.js Frontend :3000</span>
            </div>
            <div className="flex items-center gap-1.5 bg-slate-950/80 px-3 py-1.5 rounded-md border border-slate-800">
              <span className="h-2 w-2 rounded-full bg-emerald-400"></span>
              <span>PostgreSQL 16 :5432</span>
            </div>
          </div>
        </div>
      </div>

      {/* Live System Health Monitor */}
      <HealthStatusWidget />

      {/* Core Reconciliation Taxonomy */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-base font-semibold text-white">Reconciliation Exception Taxonomy</h3>
            <p className="text-xs text-slate-400">10 canonical exception classes supported in METFI Master Spec v1.0</p>
          </div>
          <span className="rounded bg-slate-800 px-2.5 py-1 text-xs font-mono text-slate-300 border border-slate-700">
            10 Classes
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
          {taxonomyClasses.map((item, i) => (
            <div 
              key={i} 
              className="rounded-lg border border-slate-800/80 bg-slate-950/60 p-3 flex flex-col justify-between hover:border-slate-700 transition-colors"
            >
              <span className="text-xs font-mono font-semibold text-slate-200 truncate" title={item.label}>
                {item.label}
              </span>
              <span className="text-[11px] font-mono text-slate-500 mt-2">
                {item.count}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Phase Roadmap Progress */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-6">
        <h3 className="text-base font-semibold text-white mb-4">Development Phases & Milestones</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between rounded-lg border border-emerald-500/30 bg-emerald-950/10 p-3">
            <div className="flex items-center gap-3">
              <CheckCircle className="h-5 w-5 text-emerald-400" />
              <div>
                <p className="text-sm font-semibold text-white">Phase 0 — Repository Initialization & Governance</p>
                <p className="text-xs text-slate-400">Architecture docs, AGENTS.md, health check endpoints, docker compose, test harness</p>
              </div>
            </div>
            <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs font-bold text-emerald-400">
              ACTIVE
            </span>
          </div>

          <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/40 p-3 opacity-60">
            <div className="flex items-center gap-3">
              <div className="h-5 w-5 rounded-full border border-slate-700 flex items-center justify-center text-xs text-slate-500">1</div>
              <div>
                <p className="text-sm font-semibold text-slate-300">Phase 1 — Domain Schemas, Ingestion & Synthetic Data Generator</p>
                <p className="text-xs text-slate-500">500-dev & 5000-stress generators with isolated ground truth</p>
              </div>
            </div>
            <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-400">
              NEXT
            </span>
          </div>

          <div className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-950/40 p-3 opacity-60">
            <div className="flex items-center gap-3">
              <div className="h-5 w-5 rounded-full border border-slate-700 flex items-center justify-center text-xs text-slate-500">2</div>
              <div>
                <p className="text-sm font-semibold text-slate-300">Phase 2 — Deterministic Reconciliation Engine</p>
                <p className="text-xs text-slate-500">Candidate matching, rule evaluations, golden regression test suite</p>
              </div>
            </div>
            <span className="rounded bg-slate-800 px-2 py-0.5 text-xs font-medium text-slate-400">
              PLANNED
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
