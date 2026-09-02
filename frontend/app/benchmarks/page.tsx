"use client";

import React, { useEffect, useState } from "react";
import { AppShell } from "../../components/layout/AppShell";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { fetchBenchmarkSummary, runBenchmarks } from "../../lib/api-client";
import { UnifiedBenchmarkSummary } from "../../types/models";
import {
  BarChart3,
  ShieldCheck,
  CheckCircle2,
  Award,
  Zap,
  Brain,
  History,
  RefreshCw,
  Filter,
  Layers,
  Sparkles,
  AlertTriangle,
} from "lucide-react";

export default function BenchmarksPage() {
  const [summary, setSummary] = useState<UnifiedBenchmarkSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [categoryFilter, setCategoryFilter] = useState("ALL");

  async function loadSummary() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchBenchmarkSummary();
      setSummary(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load live benchmark data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSummary();
  }, []);

  async function handleRunBenchmarks() {
    try {
      setRunning(true);
      const updated = await runBenchmarks();
      setSummary(updated);
    } catch (err) {
      alert(`Benchmark execution failed: ${err instanceof Error ? err.message : err}`);
    } finally {
      setRunning(false);
    }
  }

  const suites = summary?.suites || [];
  const filteredSuites = suites.filter((s) => {
    if (categoryFilter === "ALL") return true;
    return s.category === categoryFilter;
  });

  return (
    <AppShell>
      <div className="space-y-8 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-indigo-950/80 border border-indigo-700/60 text-indigo-300 text-[11px] font-mono font-semibold mb-2">
              <Award className="w-3.5 h-3.5" />
              <span>INDEPENDENT EVALUATION BENCHMARKS</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Evaluation &amp; Governance Benchmarks
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Rigorous empirical evaluation results across deterministic matching, AI reasoning, policy gating, and audit integrity.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <button
              onClick={handleRunBenchmarks}
              disabled={running}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold font-mono shadow-md shadow-indigo-600/20 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${running ? "animate-spin" : ""}`} />
              <span>{running ? "Running Evaluation..." : "Run Live Benchmarks"}</span>
            </button>

            <div className="flex items-center gap-2 px-3.5 py-2 rounded-xl bg-emerald-950/60 border border-emerald-700/70 text-emerald-300 font-mono text-xs font-bold shadow-md shadow-emerald-950/30">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Status: {summary?.overall_status || "PASS"}</span>
            </div>
          </div>
        </div>

        {/* Metadata Banner */}
        {summary && (
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-400">
            <div>Evaluation Spec: <span className="text-white font-bold">v{summary.evaluation_version}</span></div>
            <div>Git HEAD: <span className="text-indigo-400 font-bold">{summary.git_head.slice(0, 10)}</span></div>
            <div>Deterministic Seed: <span className="text-emerald-400 font-bold">{summary.seed}</span></div>
            <div>Total Cases Evaluated: <span className="text-cyan-300 font-bold">{summary.total_cases_evaluated}</span></div>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-200 text-xs font-mono">
            {error}
          </div>
        )}

        {/* Category Filter Pills */}
        <div className="flex flex-wrap items-center gap-2">
          {["ALL", "INDEPENDENT", "ADVERSARIAL", "AI", "POLICY", "AUDIT", "SYNTHETIC", "END_TO_END"].map((cat) => (
            <button
              key={cat}
              onClick={() => setCategoryFilter(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-mono font-semibold transition-all ${
                categoryFilter === cat
                  ? "bg-indigo-600 text-white shadow-md shadow-indigo-600/30"
                  : "bg-slate-900/70 text-slate-400 hover:text-slate-200 border border-slate-800"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Benchmark Suites Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {loading ? (
            <div className="col-span-full p-12 text-center text-slate-400 font-mono text-xs bg-[#0b0f19]/80 rounded-2xl border border-slate-800">
              Loading empirical evaluation benchmark reports from backend...
            </div>
          ) : filteredSuites.length > 0 ? (
            filteredSuites.map((suite) => (
              <div
                key={suite.suite_id}
                className="p-6 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 hover:border-slate-700 transition-all space-y-4"
              >
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <div>
                    <span className="text-[10px] font-mono font-bold text-indigo-400 uppercase tracking-widest">
                      {suite.category}
                    </span>
                    <h2 className="text-sm font-extrabold text-white font-mono mt-0.5">{suite.name}</h2>
                    <p className="text-[11px] text-slate-400 font-sans mt-0.5">
                      Evaluated {suite.cases_evaluated} cases in {suite.duration_ms}ms
                    </p>
                  </div>
                  <StatusBadge status={suite.passed ? "PASS" : "FAIL"} type="verifier" showIcon />
                </div>

                <div className="space-y-3 font-mono text-xs">
                  {suite.metrics.map((m) => (
                    <div key={m.label} className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/60 flex items-center justify-between">
                      <div>
                        <span className="text-slate-300 font-semibold">{m.label}</span>
                        <p className="text-[10px] text-slate-500 mt-0.5">Target: {m.target}</p>
                        {m.details && <p className="text-[10px] text-slate-400 mt-0.5 font-sans">{m.details}</p>}
                      </div>
                      <div className="text-right">
                        <span className="text-emerald-400 font-extrabold text-sm">{m.score}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <div className="col-span-full p-12 rounded-2xl bg-[#0b0f19]/60 border border-slate-800/80 text-center text-slate-400 font-mono text-xs">
              No benchmark suites match category filter &quot;{categoryFilter}&quot;.
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
