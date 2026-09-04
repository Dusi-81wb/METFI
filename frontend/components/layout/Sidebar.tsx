"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  AlertTriangle,
  SlidersHorizontal,
  ListTodo,
  History,
  BarChart3,
  PlayCircle,
  Database,
  ShieldCheck,
  Zap,
  Layers,
} from "lucide-react";

interface SidebarProps {
  onTriggerReconcile?: () => void;
  isReconciling?: boolean;
  exceptionCount?: number;
}

export function Sidebar({
  onTriggerReconcile,
  isReconciling = false,
  exceptionCount = 200,
}: SidebarProps) {
  const pathname = usePathname();

  const navItems = [
    {
      name: "Overview",
      href: "/",
      icon: LayoutDashboard,
      badge: undefined,
    },
    {
      name: "Honest Exceptions",
      href: "/exceptions",
      icon: AlertTriangle,
      badge: exceptionCount > 0 ? String(exceptionCount) : undefined,
      badgeColor: "bg-rose-100 text-rose-700",
    },
    {
      name: "Rule Studio",
      href: "/rules",
      icon: SlidersHorizontal,
      badge: "PURVIEW",
      badgeColor: "bg-purple-100 text-purple-700",
    },
    {
      name: "Review Queue",
      href: "/review-queue",
      icon: ListTodo,
      badge: undefined,
    },
    {
      name: "Sample Data",
      href: "/data",
      icon: Database,
      badge: undefined,
    },
    {
      name: "Audit Ledger",
      href: "/audit",
      icon: History,
      badge: "SHA-256",
      badgeColor: "bg-slate-100 text-slate-700",
    },
    {
      name: "Benchmarks",
      href: "/benchmarks",
      icon: BarChart3,
      badge: undefined,
    },
    {
      name: "1-Click Demo",
      href: "/showcase",
      icon: PlayCircle,
      badge: "SHOWCASE",
      badgeColor: "bg-cyan-100 text-cyan-800",
    },
  ];

  return (
    <aside className="w-64 bg-[#0d0e12] border-r border-zinc-800/80 flex flex-col h-screen shrink-0 select-none">
      {/* Brand Header matching email_scheduler style */}
      <div className="px-5 pt-5 pb-3">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-500 flex items-center justify-center text-white shadow-xs shrink-0 font-extrabold text-sm tracking-tight">
            M
          </div>
          <div className="min-w-0">
            <span className="text-sm font-bold tracking-tight text-zinc-100 block truncate">
              METFI
            </span>
            <span className="text-[10px] text-zinc-400 font-medium block truncate -mt-0.5">
              AI Finance Controller
            </span>
          </div>
        </div>
      </div>

      {/* User / Controller Profile Card */}
      <div className="px-4 py-2">
        <div className="flex items-center justify-between p-2 rounded-xl bg-zinc-900/80 border border-zinc-800">
          <div className="flex items-center space-x-2.5 overflow-hidden">
            <div className="w-8 h-8 rounded-full bg-indigo-950 text-indigo-300 font-bold text-xs flex items-center justify-center shrink-0 border border-indigo-800/50">
              FC
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-zinc-200 truncate">
                Finance Controller
              </p>
              <p className="text-[11px] text-zinc-400 truncate font-mono">
                dev_500 • Active
              </p>
            </div>
          </div>
          <span className="w-2 h-2 rounded-full bg-emerald-500 shrink-0" title="Connected" />
        </div>
      </div>

      {/* Primary Action Button: Reconcile Feed (like Compose Email in email_scheduler) */}
      <div className="px-4 py-3">
        <button
          type="button"
          onClick={onTriggerReconcile}
          disabled={isReconciling}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition-all shadow-xs hover:shadow-md active:scale-[0.98] disabled:opacity-50"
        >
          <Zap className={`w-3.5 h-3.5 ${isReconciling ? "animate-spin" : ""}`} />
          <span>{isReconciling ? "Reconciling Batch..." : "⚡ Reconcile Feed"}</span>
        </button>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto pt-1">
        {navItems.map((item) => {
          const isActive =
            item.href === "/"
              ? pathname === "/"
              : pathname === item.href ||
                (item.href !== "/" && pathname.startsWith(item.href) && item.href !== "/cases/case_demo_101");
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                isActive
                  ? "bg-indigo-950/40 text-indigo-300 font-semibold border border-indigo-900/40"
                  : "text-zinc-400 hover:bg-zinc-900 hover:text-zinc-100"
              }`}
            >
              <div className="flex items-center space-x-2.5 min-w-0">
                <Icon
                  className={`w-4 h-4 shrink-0 ${
                    isActive ? "text-indigo-400" : "text-zinc-400 group-hover:text-zinc-300"
                  }`}
                />
                <span className="truncate">{item.name}</span>
              </div>

              {item.badge && (
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                    item.badgeColor || "bg-zinc-800 text-zinc-300"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer Invariant Security Card */}
      <div className="p-4 border-t border-zinc-800/80 bg-zinc-950/40">
        <div className="flex items-center space-x-2 text-[11px] text-zinc-400">
          <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
          <div className="min-w-0">
            <span className="font-semibold text-zinc-200 block truncate">Deterministic Truth</span>
            <span className="text-[10px] text-zinc-500 block truncate">Immutable Invariant</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
