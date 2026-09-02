"use client";

import React from "react";
import Link from "next/link";
import { AppShell } from "../../components/layout/AppShell";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { Zap, ShieldCheck, ArrowUpRight, CheckCircle2, ChevronRight } from "lucide-react";

export default function ActionsPage() {
  const sampleActions = [
    {
      actionId: "act_0f3a4edf4e1b",
      caseId: "case_demo_101",
      actionType: "AUTO_RECONCILE",
      state: "EXECUTED",
      idempotencyKey: "243c80440ce00f9ee2203dda",
      policyVersion: "1.0.0",
      executedAt: "2026-09-02T07:15:30Z",
      sideEffects: ["MARKED_RECONCILED", "FEE_GL_ACCOUNTED"],
    },
    {
      actionId: "act_8a2b3c4d5e6f",
      caseId: "case_demo_102",
      actionType: "MARK_FOR_REVIEW",
      state: "AUTHORIZED",
      idempotencyKey: "1a2b3c4d5e6f7a8b9c0d1e2f",
      policyVersion: "1.0.0",
      executedAt: "2026-09-02T07:10:00Z",
      sideEffects: ["ENQUEUED_HUMAN_REVIEW"],
    },
    {
      actionId: "act_9b3c4d5e6f7a",
      caseId: "case_demo_103",
      actionType: "REJECT_AND_ESCALATE",
      state: "EXECUTED",
      idempotencyKey: "3b4c5d6e7f8a9b0c1d2e3f4a",
      policyVersion: "1.0.0",
      executedAt: "2026-09-02T06:55:00Z",
      sideEffects: ["AUDIT_ALERT_FIRED", "ESCALATED_TO_CONTROLLER"],
    },
  ];

  return (
    <AppShell>
      <div className="space-y-8 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-cyan-950/80 border border-cyan-700/60 text-cyan-300 text-[11px] font-mono font-semibold mb-2">
              <Zap className="w-3.5 h-3.5" />
              <span>CONTROLLED ACTIONS LIFECYCLE</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Action State Machine Tracker
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Policy-authorized bounded execution tracker enforcing strict states and SHA-256 idempotency.
            </p>
          </div>
        </div>

        {/* Actions Table */}
        <div className="p-6 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 space-y-4">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950/90 text-slate-400 border-b border-slate-800 uppercase text-[11px]">
                <tr>
                  <th className="p-3">Action ID</th>
                  <th className="p-3">Case ID</th>
                  <th className="p-3">Action Type</th>
                  <th className="p-3">State</th>
                  <th className="p-3">Idempotency Key</th>
                  <th className="p-3">Side Effects</th>
                  <th className="p-3">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                {sampleActions.map((act) => (
                  <tr key={act.actionId} className="hover:bg-slate-900/40 transition-colors">
                    <td className="p-3 text-cyan-300 font-bold">{act.actionId}</td>
                    <td className="p-3">
                      <Link href={`/cases/${act.caseId}`} className="text-indigo-400 hover:text-indigo-300 hover:underline">
                        {act.caseId}
                      </Link>
                    </td>
                    <td className="p-3 text-white font-semibold">{act.actionType}</td>
                    <td className="p-3"><StatusBadge status={act.state} type="action" showIcon /></td>
                    <td className="p-3 text-slate-400 font-mono text-[11px]">{act.idempotencyKey.slice(0, 14)}...</td>
                    <td className="p-3 text-slate-300 text-[11px] font-sans">{act.sideEffects.join(", ")}</td>
                    <td className="p-3 text-slate-500 text-[11px]">{act.executedAt}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </AppShell>
  );
}
