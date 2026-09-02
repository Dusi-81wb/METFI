"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Layers,
  AlertTriangle,
  ListTodo,
  Zap,
  History,
  BarChart3,
  PlayCircle,
  FileCheck2,
  ChevronRight,
  ShieldCheck,
} from "lucide-react";

interface NavGroup {
  label: string;
  items: {
    name: string;
    href: string;
    icon: React.ElementType;
    badge?: string;
    badgeColor?: string;
  }[];
}

const navGroups: NavGroup[] = [
  {
    label: "Main Navigation",
    items: [
      { name: "Dashboard", href: "/", icon: LayoutDashboard },
      {
        name: "Showcase Demo",
        href: "/showcase",
        icon: PlayCircle,
        badge: "1-CLICK",
        badgeColor: "from-cyan-500 to-indigo-500",
      },
      { name: "Case Detail", href: "/cases/case_demo_101", icon: FileCheck2 },
    ],
  },
  {
    label: "Operations & Triage",
    items: [
      { name: "Reconciliation", href: "/reconciliation", icon: Layers },
      { name: "Exceptions", href: "/exceptions", icon: AlertTriangle },
      { name: "Review Queue", href: "/review-queue", icon: ListTodo },
      { name: "Controlled Actions", href: "/actions", icon: Zap },
    ],
  },
  {
    label: "Trust & Verification",
    items: [
      { name: "Audit Trail", href: "/audit", icon: History },
      { name: "Benchmarks", href: "/benchmarks", icon: BarChart3 },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 border-r border-slate-800/80 bg-[#030712]/95 backdrop-blur-md p-4 flex flex-col justify-between shrink-0 min-h-[calc(100vh-4rem)]">
      <div className="space-y-6">
        {navGroups.map((group) => (
          <div key={group.label} className="space-y-1.5">
            <p className="px-3 text-[10px] font-bold text-slate-500 uppercase tracking-widest font-mono">
              {group.label}
            </p>
            <nav className="space-y-0.5">
              {group.items.map((item) => {
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
                    className={`group flex items-center justify-between px-3 py-2 text-xs font-medium rounded-xl transition-all duration-150 ${
                      isActive
                        ? "bg-indigo-950/70 text-indigo-200 border border-indigo-700/60 shadow-md shadow-indigo-950/40"
                        : "text-slate-400 hover:text-slate-100 hover:bg-slate-900/60"
                    }`}
                  >
                    <div className="flex items-center space-x-2.5">
                      <Icon
                        className={`w-4 h-4 transition-colors ${
                          isActive ? "text-indigo-400" : "text-slate-500 group-hover:text-slate-300"
                        }`}
                      />
                      <span className="font-semibold">{item.name}</span>
                    </div>

                    {item.badge ? (
                      <span
                        className={`px-1.5 py-0.5 text-[9px] font-bold font-mono rounded bg-gradient-to-r ${item.badgeColor} text-white shadow-sm`}
                      >
                        {item.badge}
                      </span>
                    ) : (
                      isActive && <ChevronRight className="w-3.5 h-3.5 text-indigo-400" />
                    )}
                  </Link>
                );
              })}
            </nav>
          </div>
        ))}

        {/* Architecture Guardrails Badge */}
        <div className="border-t border-slate-800/80 pt-4">
          <div className="px-3 py-3 rounded-xl bg-slate-900/40 border border-slate-800/60 text-[11px] text-slate-400 space-y-2">
            <div className="flex items-center gap-1.5 font-bold text-white text-[10px] uppercase font-mono tracking-wider">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Core Guardrails</span>
            </div>
            <div className="space-y-1.5 font-mono text-[10px]">
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Truth:</span>
                <span className="text-emerald-400 font-bold">DETERMINISTIC</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">AI Role:</span>
                <span className="text-purple-400 font-bold">RECOMMENDER</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Gatekeeper:</span>
                <span className="text-cyan-400 font-bold">POLICY GATED</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-500">Audit Ledger:</span>
                <span className="text-indigo-400 font-bold">SHA-256 LINKED</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="text-[10px] text-slate-500 font-mono px-3 py-2 border-t border-slate-800/60 flex items-center justify-between">
        <span>METFI Console</span>
        <span className="text-emerald-500 font-bold">v1.0.0</span>
      </div>
    </aside>
  );
}
