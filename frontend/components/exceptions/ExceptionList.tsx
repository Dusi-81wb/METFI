"use client";

import React, { useState, useMemo } from "react";
import { AlertTriangle, ChevronRight, Star, Filter, ShieldAlert } from "lucide-react";
import { HonestExceptionItem } from "../../types/controller";

interface ExceptionListProps {
  exceptions: HonestExceptionItem[];
  loading?: boolean;
  onSelectException: (item: HonestExceptionItem) => void;
  selectedCaseId?: string | null;
  searchQuery?: string;
}

export const ExceptionList: React.FC<ExceptionListProps> = ({
  exceptions,
  loading = false,
  onSelectException,
  selectedCaseId,
  searchQuery = "",
}) => {
  const [activeCategory, setActiveCategory] = useState<string>("ALL");
  const [starredIds, setStarredIds] = useState<Record<string, boolean>>({});

  const toggleStar = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setStarredIds((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  // Categories count
  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = { ALL: exceptions.length };
    exceptions.forEach((e) => {
      const type = e.exception_type;
      counts[type] = (counts[type] || 0) + 1;
    });
    return counts;
  }, [exceptions]);

  // Filtered exceptions
  const filteredExceptions = useMemo(() => {
    return exceptions.filter((item) => {
      // Category filter
      if (activeCategory !== "ALL" && item.exception_type !== activeCategory) {
        return false;
      }
      // Search query filter
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchCase = item.case_id.toLowerCase().includes(q);
        const matchOrder = item.order_id?.toLowerCase().includes(q);
        const matchType = item.exception_type.toLowerCase().includes(q);
        const matchReason = item.reason_unresolved.toLowerCase().includes(q);
        const matchVar = String(item.financial_variance).includes(q);
        return matchCase || matchOrder || matchType || matchReason || matchVar;
      }
      return true;
    });
  }, [exceptions, activeCategory, searchQuery]);

  const getBadgeStyle = (type: string) => {
    switch (type) {
      case "AMOUNT_MISMATCH":
        return "bg-amber-950/40 text-amber-400 border-amber-800/60";
      case "DUPLICATE_RECORD":
        return "bg-rose-950/40 text-rose-400 border-rose-800/60";
      case "DATE_MISMATCH":
        return "bg-sky-950/40 text-sky-400 border-sky-800/60";
      case "PARTIAL_SETTLEMENT":
        return "bg-purple-950/40 text-purple-400 border-purple-800/60";
      case "CURRENCY_MISMATCH":
        return "bg-indigo-950/40 text-indigo-400 border-indigo-800/60";
      default:
        return "bg-zinc-800 text-zinc-300 border-zinc-700";
    }
  };

  if (loading) {
    return (
      <div className="saas-card p-12 flex flex-col items-center justify-center text-zinc-500 space-y-3 bg-[#111217] border border-zinc-800">
        <div className="w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
        <span className="text-xs font-medium">Loading exception records...</span>
      </div>
    );
  }

  return (
    <div className="saas-card overflow-hidden bg-[#111217] border border-zinc-800">
      {/* Category Pills Header */}
      <div className="p-3.5 border-b border-zinc-800 bg-zinc-900/60 flex items-center justify-between gap-2 overflow-x-auto">
        <div className="flex items-center space-x-1.5 shrink-0">
          {[
            { id: "ALL", label: "All Exceptions", count: categoryCounts["ALL"] || 0 },
            { id: "AMOUNT_MISMATCH", label: "Amount Delta", count: categoryCounts["AMOUNT_MISMATCH"] || 0 },
            { id: "DUPLICATE_RECORD", label: "Duplicate", count: categoryCounts["DUPLICATE_RECORD"] || 0 },
            { id: "DATE_MISMATCH", label: "Timing SLA", count: categoryCounts["DATE_MISMATCH"] || 0 },
            { id: "PARTIAL_SETTLEMENT", label: "Partial", count: categoryCounts["PARTIAL_SETTLEMENT"] || 0 },
          ].map((cat) => (
            <button
              key={cat.id}
              type="button"
              onClick={() => setActiveCategory(cat.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                activeCategory === cat.id
                  ? "bg-zinc-800 text-indigo-400 shadow-xs border border-zinc-700 font-semibold"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60"
              }`}
            >
              <span>{cat.label}</span>
              <span
                className={`ml-1.5 px-1.5 py-0.2 rounded-full text-[10px] font-mono ${
                  activeCategory === cat.id
                    ? "bg-indigo-950 text-indigo-300 border border-indigo-800/40"
                    : "bg-zinc-800 text-zinc-400"
                }`}
              >
                {cat.count}
              </span>
            </button>
          ))}
        </div>

        <div className="text-[11px] text-zinc-500 font-mono shrink-0 hidden sm:block">
          Showing {filteredExceptions.length} of {exceptions.length} cases
        </div>
      </div>

      {/* Exception Rows List */}
      {filteredExceptions.length === 0 ? (
        <div className="p-12 text-center text-zinc-500 space-y-2">
          <ShieldAlert className="w-8 h-8 text-zinc-600 mx-auto" />
          <p className="text-xs font-semibold text-zinc-300">No matching exceptions found</p>
          <p className="text-[11px] text-zinc-500">
            {searchQuery
              ? `No cases matched search term "${searchQuery}".`
              : "All records for this category resolved or clean."}
          </p>
        </div>
      ) : (
        <div className="divide-y divide-zinc-800/60 bg-[#111217]">
          {filteredExceptions.map((item) => {
            const isSelected = selectedCaseId === item.case_id;
            const isStarred = !!starredIds[item.case_id];

            return (
              <div
                key={item.case_id}
                onClick={() => onSelectException(item)}
                className={`group flex items-center justify-between px-5 py-3.5 hover:bg-zinc-900/80 transition-colors cursor-pointer text-xs ${
                  isSelected ? "bg-zinc-900 border-l-4 border-l-indigo-500" : ""
                }`}
              >
                {/* Left: Star + Case ID + Category Badge */}
                <div className="flex items-center space-x-3.5 min-w-0 flex-1 pr-4">
                  <button
                    type="button"
                    onClick={(e) => toggleStar(e, item.case_id)}
                    className="text-zinc-600 hover:text-amber-400 transition-colors shrink-0"
                  >
                    <Star
                      className={`w-4 h-4 ${
                        isStarred ? "text-amber-400 fill-amber-400" : ""
                      }`}
                    />
                  </button>

                  {/* Case & Order identifier */}
                  <div className="w-36 shrink-0 truncate">
                    <span className="font-mono font-bold text-zinc-100 block truncate">
                      {item.case_id}
                    </span>
                    <span className="font-mono text-[10px] text-zinc-500 block truncate">
                      {item.order_id || "no_order_ref"}
                    </span>
                  </div>

                  {/* Category Badge */}
                  <span
                    className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold border shrink-0 ${getBadgeStyle(
                      item.exception_type
                    )}`}
                  >
                    {item.exception_type}
                  </span>

                  {/* Reason Summary Snippet */}
                  <div className="min-w-0 flex-1 hidden md:block">
                    <p className="text-xs text-zinc-400 truncate">
                      {item.reason_unresolved || item.root_cause_summary}
                    </p>
                  </div>
                </div>

                {/* Right: Variance Amount + Policy Outcome + Action indicator */}
                <div className="flex items-center space-x-4 shrink-0 text-right">
                  {item.financial_variance > 0 ? (
                    <div className="font-mono font-bold text-rose-400">
                      ₹{item.financial_variance.toFixed(2)}
                      <span className="block text-[10px] text-zinc-500 font-normal">delta</span>
                    </div>
                  ) : (
                    <div className="font-mono font-medium text-zinc-500">
                      ₹0.00
                      <span className="block text-[10px] text-zinc-500 font-normal">metadata</span>
                    </div>
                  )}

                  <span className="hidden sm:inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold bg-amber-950/40 text-amber-400 border border-amber-800/60">
                    {item.policy_outcome}
                  </span>

                  <ChevronRight className="w-4 h-4 text-zinc-500 group-hover:text-indigo-400 transition-colors" />
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
