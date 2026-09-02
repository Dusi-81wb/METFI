"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { fetchHealth } from "../../lib/api-client";
import { HealthResponse } from "../../types/models";
import { ShieldCheck, Activity, Server, AlertCircle, Sparkles, ExternalLink } from "lucide-react";

export function Navbar() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth()
      .then((data) => {
        setHealth(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message || "Failed to reach backend");
        setLoading(false);
      });
  }, []);

  return (
    <header className="h-16 border-b border-slate-800/80 bg-[#030712]/90 backdrop-blur-xl px-6 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center space-x-4">
        <Link href="/" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 via-indigo-600 to-cyan-500 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
            <span className="tracking-tighter text-sm font-extrabold">M</span>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-base text-white tracking-tight group-hover:text-indigo-300 transition-colors">
                METFI
              </span>
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full bg-indigo-950/80 text-indigo-300 border border-indigo-700/60 uppercase">
                Ops Console
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-mono -mt-0.5">
              Autonomous Financial Reconciliation &amp; Audit Ledger
            </p>
          </div>
        </Link>
      </div>

      <div className="flex items-center space-x-4">
        <div className="hidden md:flex items-center space-x-2 text-xs font-mono px-3 py-1 rounded-lg bg-slate-900/60 border border-slate-800">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-slate-400">Deterministic Primacy:</span>
          <span className="text-emerald-400 font-semibold">ENFORCED</span>
        </div>

        <div className="h-4 w-px bg-slate-800 hidden md:block" />

        {/* Real Backend Status Badge */}
        {loading ? (
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-900/80 border border-slate-800 text-slate-400 text-xs font-mono">
            <Activity className="w-3 h-3 animate-spin text-indigo-400" />
            <span>Connecting API...</span>
          </div>
        ) : error ? (
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-rose-950/80 border border-rose-800 text-rose-300 text-xs font-mono">
            <AlertCircle className="w-3 h-3 text-rose-400" />
            <span>API Offline: {error.slice(0, 30)}</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-950/50 border border-emerald-800/80 text-emerald-300 text-xs font-mono shadow-[0_0_12px_-3px_rgba(16,185,129,0.2)]">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <Server className="w-3 h-3 text-emerald-400" />
            <span>API v{health?.version || "1.0.0"} ({health?.database || "connected"})</span>
          </div>
        )}

        <Link
          href="/showcase"
          className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600/90 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-500/20 transition-all font-mono"
        >
          <Sparkles className="w-3 h-3 text-cyan-300" />
          <span>Demo</span>
        </Link>
      </div>
    </header>
  );
}
