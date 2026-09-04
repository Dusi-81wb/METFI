"use client";

import React from "react";
import { Search, RotateCw, Sparkles, ShieldCheck, Server, AlertCircle } from "lucide-react";
import { HealthResponse } from "../../types/models";

interface TopBarProps {
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
  onOpenQA?: () => void;
  health?: HealthResponse | null;
  isBalanced?: boolean;
}

export const TopBar: React.FC<TopBarProps> = ({
  searchQuery,
  onSearchChange,
  onRefresh,
  isRefreshing = false,
  onOpenQA,
  health,
  isBalanced = true,
}) => {
  return (
    <header className="h-16 px-6 flex items-center justify-between border-b border-zinc-800/80 bg-[#0d0e12] shrink-0 sticky top-0 z-20">
      {/* Search Bar matching email_scheduler style */}
      <div className="flex items-center space-x-3 w-full max-w-md">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-zinc-500" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search exceptions by Case ID, Order ID, or variance..."
            className="w-full pl-10 pr-4 py-2 bg-zinc-900/90 hover:bg-zinc-850 focus:bg-[#111217] text-xs text-zinc-200 placeholder-zinc-500 rounded-full border border-zinc-800 focus:border-indigo-500 focus:outline-none transition-all"
          />
        </div>

        {/* Refresh Circular Arrow Icon */}
        <button
          type="button"
          onClick={onRefresh}
          title="Refresh feeds & ledger"
          className={`p-2 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/80 rounded-full transition-colors ${
            isRefreshing ? "animate-spin text-indigo-400" : ""
          }`}
        >
          <RotateCw className="w-4 h-4" />
        </button>
      </div>

      {/* Right Controls: Invariant Badge + Q&A Assistant CTA + Health Badge */}
      <div className="flex items-center space-x-3">
        {/* Books Invariant Badge */}
        <div className="hidden lg:flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-950/40 border border-emerald-800/60 text-emerald-400 text-xs font-mono font-medium">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Ledger:</span>
          <span className="font-bold">{isBalanced ? "BALANCED (0.00)" : "UNBALANCED"}</span>
        </div>

        {/* Settlement Q&A Flyout Trigger */}
        {onOpenQA && (
          <button
            type="button"
            onClick={onOpenQA}
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-full bg-indigo-950/60 hover:bg-indigo-900/80 border border-indigo-800/60 text-indigo-300 text-xs font-semibold transition-all shadow-xs"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span>Ask Q&A</span>
          </button>
        )}

        {/* API Health Pill */}
        {health ? (
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-zinc-900 text-zinc-300 text-[11px] font-mono border border-zinc-800">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <Server className="w-3 h-3 text-zinc-400" />
            <span>v{health.version}</span>
          </div>
        ) : (
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-rose-950/60 text-rose-300 text-[11px] font-mono border border-rose-800/80">
            <AlertCircle className="w-3 h-3" />
            <span>Offline</span>
          </div>
        )}
      </div>
    </header>
  );
};
