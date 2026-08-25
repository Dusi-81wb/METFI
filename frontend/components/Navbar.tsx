"use client";

import React from "react";
import { ShieldCheck, Activity, Terminal, Database, Layers } from "lucide-react";

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-800 bg-slate-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600/20 border border-blue-500/30 text-blue-400">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight text-white">METFI</span>
              <span className="rounded bg-blue-500/10 px-2 py-0.5 text-xs font-semibold text-blue-400 border border-blue-500/20">
                v0.1.0 • Phase 0
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous Finance Controller</p>
          </div>
        </div>

        <nav className="flex items-center gap-6 text-sm font-medium text-slate-300">
          <div className="flex items-center gap-1.5 text-slate-200">
            <Activity className="h-4 w-4 text-emerald-400" />
            <span>Controller Health</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400 hover:text-slate-200 transition-colors">
            <Layers className="h-4 w-4" />
            <span>Reconciliation</span>
          </div>
          <div className="flex items-center gap-1.5 text-slate-400 hover:text-slate-200 transition-colors">
            <Database className="h-4 w-4" />
            <span>Audit Trail</span>
          </div>
        </nav>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-950/40 px-3 py-1 text-xs text-emerald-400">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Deterministic Truth Active</span>
          </div>
        </div>
      </div>
    </header>
  );
}
