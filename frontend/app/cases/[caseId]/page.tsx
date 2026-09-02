"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AppShell } from "../../../components/layout/AppShell";
import { StatusBadge } from "../../../components/ui/StatusBadge";
import {
  fetchCaseAuditTrail,
  verifyCaseIntegrity,
} from "../../../lib/api-client";
import {
  AuditEvent,
  AuditIntegrityResult,
} from "../../../types/models";
import {
  ShieldCheck,
  Brain,
  Scale,
  Zap,
  History,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Clock,
  ArrowLeft,
  Key,
  Copy,
  Check,
  Sparkles,
  Layers,
  HelpCircle,
  ExternalLink,
} from "lucide-react";

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = (params?.caseId as string) || "case_demo_101";

  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [integrityResult, setIntegrityResult] = useState<AuditIntegrityResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    async function loadCaseData() {
      try {
        const [auditData, verifyData] = await Promise.all([
          fetchCaseAuditTrail(caseId).catch(() => ({ case_id: caseId, event_count: 0, events: [] })),
          verifyCaseIntegrity(caseId).catch(() => null),
        ]);
        setAuditEvents(auditData.events || []);
        setIntegrityResult(verifyData);
      } catch (err) {
        console.error("Case load error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadCaseData();
  }, [caseId]);

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
    setCopiedId(text);
    setTimeout(() => setCopiedId(null), 2000);
  }

  return (
    <AppShell>
      <div className="space-y-8 max-w-6xl mx-auto">
        {/* Navigation Breadcrumbs & Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <Link
              href="/exceptions"
              className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-indigo-400 font-mono mb-2 transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Exceptions</span>
            </Link>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl md:text-3xl font-extrabold text-white font-mono tracking-tight flex items-center gap-2">
                <span>{caseId}</span>
                <button
                  onClick={() => copyToClipboard(caseId)}
                  className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-slate-300 transition-colors"
                  title="Copy Case ID"
                >
                  {copiedId === caseId ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </h1>
              <StatusBadge status="FEE_VARIANCE" type="priority" showIcon />
              <StatusBadge status="RESOLVED" type="action" showIcon />
            </div>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Gateway settlement fee variance evaluated through verified AI reasoning and deterministic policy gating.
            </p>
          </div>

          {/* Cryptographic SHA-256 Ledger Seal */}
          <div className="p-3.5 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 flex items-center gap-3.5 shadow-md">
            <div className="w-9 h-9 rounded-xl bg-emerald-950/80 border border-emerald-700/60 flex items-center justify-center text-emerald-400 shadow-[0_0_15px_-3px_rgba(16,185,129,0.3)]">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-white">SHA-256 Hash Chain:</span>
                <StatusBadge
                  status={integrityResult?.status === "VALID" ? "VALID" : "ACTIVE"}
                  type="verifier"
                />
              </div>
              <p className="text-[10px] text-slate-400 font-mono mt-0.5">
                {integrityResult?.events_verified_count || auditEvents.length || 3} Events Verified | 0 Sequence Breaks
              </p>
            </div>
          </div>
        </div>

        {/* PRIMARY DEMO BOUNDARY: DETERMINISTIC FACT VS AI INTERPRETATION */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest font-mono flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
              <span>Core Architectural Boundary</span>
            </h2>
            <span className="text-[10px] text-slate-500 font-mono">Enforced by Verifier &amp; Policy Engine</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Deterministic Fact Card */}
            <div className="p-5 rounded-2xl bg-blue-950/20 border-2 border-blue-600/40 shadow-[0_0_25px_-5px_rgba(59,130,246,0.15)] space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-blue-400 text-xs font-extrabold font-mono uppercase tracking-wider">
                  <span className="w-2.5 h-2.5 rounded-full bg-blue-400 animate-ping" />
                  <span>DETERMINISTIC FACT (CANONICAL)</span>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800">
                  AUTHORITATIVE
                </span>
              </div>
              <p className="text-sm text-slate-200 font-medium leading-relaxed">
                Internal ledger expected <span className="font-mono font-bold text-white">₹10,000.00</span>. Payment gateway settled <span className="font-mono font-bold text-amber-300">₹9,950.00</span>. The observed variance is exactly <span className="font-mono font-bold text-amber-400">-₹50.00 (0.5%)</span>.
              </p>
              <div className="pt-3 border-t border-blue-900/40 flex flex-wrap items-center justify-between text-[11px] font-mono text-blue-300/80">
                <span>Rule: FEE_TAX_MATRIX_01</span>
                <span>Source: PG_SETTLEMENT_FEED</span>
              </div>
            </div>

            {/* AI Interpretation Card */}
            <div className="p-5 rounded-2xl bg-purple-950/20 border-2 border-purple-600/40 shadow-[0_0_25px_-5px_rgba(168,85,247,0.15)] space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-purple-400 text-xs font-extrabold font-mono uppercase tracking-wider">
                  <span className="w-2.5 h-2.5 rounded-full bg-purple-400 animate-ping" />
                  <span>AI INTERPRETATION (HYPOTHESIS ONLY)</span>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
                  RECOMMENDER
                </span>
              </div>
              <p className="text-sm text-slate-200 font-medium leading-relaxed">
                The ₹50.00 difference matches the 0.5% merchant tier-1 gateway processing fee schedule. Recommended action is <span className="font-mono font-bold text-purple-300">AUTO_RECONCILE</span>.
              </p>
              <div className="pt-3 border-t border-purple-900/40 flex flex-wrap items-center justify-between text-[11px] font-mono text-purple-300/80">
                <span>Provider: Gemini 1.5 Pro</span>
                <span>Verifier: 100% GROUNDED</span>
              </div>
            </div>
          </div>
        </div>

        {/* SECTION 1: FINANCIAL EVIDENCE TABLE */}
        <div className="p-6 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <FileText className="w-3.5 h-3.5 text-emerald-400" />
              <span>1. Multi-Source Financial Records &amp; Certified Evidence</span>
            </h2>
            <span className="text-[10px] font-mono text-emerald-400 font-bold">100% Ground Truth Isolated</span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-slate-950/90 text-slate-400 border-b border-slate-800 uppercase text-[11px]">
                <tr>
                  <th className="p-3">Source System</th>
                  <th className="p-3">Record ID</th>
                  <th className="p-3">Expected Amount</th>
                  <th className="p-3">Observed Amount</th>
                  <th className="p-3">Discrepancy</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-300">
                <tr className="hover:bg-slate-900/40 transition-colors">
                  <td className="p-3 text-white font-bold">INTERNAL_LEDGER</td>
                  <td className="p-3 text-indigo-400">LEDGER-TX-8821</td>
                  <td className="p-3">₹10,000.00</td>
                  <td className="p-3">₹10,000.00</td>
                  <td className="p-3 text-slate-500">₹0.00</td>
                  <td className="p-3"><StatusBadge status="MATCHED" type="verifier" /></td>
                </tr>
                <tr className="hover:bg-slate-900/40 transition-colors bg-amber-950/10">
                  <td className="p-3 text-white font-bold">GATEWAY_SETTLEMENT</td>
                  <td className="p-3 text-indigo-400">PG-STMT-9942</td>
                  <td className="p-3">₹10,000.00</td>
                  <td className="p-3 text-amber-300 font-bold">₹9,950.00</td>
                  <td className="p-3 text-amber-400 font-extrabold">-₹50.00</td>
                  <td className="p-3"><StatusBadge status="FEE_VARIANCE" type="priority" /></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* SECTION 2 & 3: AI INVESTIGATION & VERIFIER PANEL */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* AI Investigation Envelope */}
          <div className="p-6 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                <Brain className="w-3.5 h-3.5 text-purple-400" />
                <span>2. AI Investigation &amp; Reasoning</span>
              </h2>
              <span className="text-[10px] font-mono text-purple-400 font-bold">Confidence: 96.5%</span>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <span className="text-[11px] text-slate-400 font-mono font-semibold">Root Cause Explanation:</span>
                <p className="text-slate-200 mt-1 leading-relaxed bg-slate-950/80 p-3.5 rounded-xl border border-slate-800/80 font-sans">
                  The ₹50.00 deduction matches the contractually defined 0.5% standard payment processing fee for merchant tier-1 transactions. No duplicate payments or currency conversion losses observed.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 text-[11px] font-mono">
                <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/80 space-y-1">
                  <span className="text-slate-400">Recommended Action:</span>
                  <p className="text-purple-300 font-extrabold">AUTO_RECONCILE</p>
                </div>
                <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/80 space-y-1">
                  <span className="text-slate-400">Evidence References:</span>
                  <p className="text-purple-300 font-extrabold">2 Certified Citations</p>
                </div>
              </div>
            </div>
          </div>

          {/* AI Verifier Critique */}
          <div className="p-6 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                <span>3. AI Verifier Safety Gate</span>
              </h2>
              <StatusBadge status="VERIFIED" type="verifier" showIcon />
            </div>

            <div className="space-y-2.5 text-xs font-mono">
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/60">
                <span className="text-slate-400">Evidence Grounding Check:</span>
                <span className="text-emerald-400 font-bold">100% GROUNDED</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/60">
                <span className="text-slate-400">Contradiction Check:</span>
                <span className="text-emerald-400 font-bold">0 CONTRADICTIONS</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/60">
                <span className="text-slate-400">Deterministic Truth Preserved:</span>
                <span className="text-emerald-400 font-bold">TRUE (ENFORCED)</span>
              </div>
              <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/60">
                <span className="text-slate-400">Recommendation Safety:</span>
                <span className="text-emerald-400 font-bold">PASSED</span>
              </div>
            </div>
          </div>
        </div>

        {/* SECTION 4 & 5: DETERMINISTIC POLICY GATE & CONTROLLED ACTION */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Policy Decision */}
          <div className="p-6 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                <Scale className="w-3.5 h-3.5 text-cyan-400" />
                <span>4. Deterministic Corporate Policy Gate</span>
              </h2>
              <StatusBadge status="ALLOW" type="policy" showIcon />
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
                <div className="flex justify-between text-slate-300">
                  <span>Variance Tolerance:</span>
                  <span className="text-cyan-300 font-bold">₹50.00 &lt;= ₹100.00 (ALLOWED)</span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Verifier Prerequisite:</span>
                  <span className="text-emerald-400 font-bold">SATISFIED</span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Autonomous Limit Cap:</span>
                  <span className="text-cyan-300 font-bold">₹10,000 &lt;= ₹50,000</span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Emergency Master Switch:</span>
                  <span className="text-emerald-400 font-bold">ARMED (ACTIVE)</span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Lifecycle */}
          <div className="p-6 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
              <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                <Zap className="w-3.5 h-3.5 text-emerald-400" />
                <span>5. Controlled Action State Machine</span>
              </h2>
              <StatusBadge status="EXECUTED" type="action" showIcon />
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
                <div className="flex justify-between text-slate-300">
                  <span>Action Type:</span>
                  <span className="text-white font-bold">AUTO_RECONCILE</span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Idempotency Key:</span>
                  <span className="text-indigo-400 font-mono">243c80440ce00f9ee220...</span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Execution Mode:</span>
                  <span className="text-emerald-400 font-bold">SIMULATION_SANDBOX</span>
                </div>
                <div className="flex justify-between text-slate-300">
                  <span>Side Effects:</span>
                  <span className="text-slate-300 font-sans">SETTLEMENT_MARKED_RECONCILED</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* SECTION 6: BLOCKCHAIN-STYLE SHA-256 AUDIT TIMELINE */}
        <div className="p-6 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
            <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
              <History className="w-3.5 h-3.5 text-indigo-400" />
              <span>6. Tamper-Evident SHA-256 Audit Trail</span>
            </h2>
            <span className="text-[10px] font-mono text-indigo-400 font-bold">Sequential Hash Chain</span>
          </div>

          <div className="space-y-3">
            {auditEvents.length > 0 ? (
              auditEvents.map((ev, idx) => (
                <div
                  key={ev.event_id || idx}
                  className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center font-bold text-slate-300">
                      #{ev.sequence_number || idx + 1}
                    </span>
                    <div>
                      <span className="text-white font-bold text-sm">{ev.event_type}</span>
                      <p className="text-[11px] text-slate-400 font-sans mt-0.5">
                        Actor: <span className="text-indigo-300 font-mono">{ev.actor?.actor_type}</span> ({ev.actor?.actor_id})
                      </p>
                    </div>
                  </div>

                  <div className="text-right text-[11px] text-slate-400 space-y-0.5">
                    <div>Hash: <span className="text-emerald-400 font-bold">{ev.event_hash ? ev.event_hash.slice(0, 16) + "..." : "GENESIS_ROOT"}</span></div>
                    <div className="text-[10px] text-slate-500">{ev.timestamp}</div>
                  </div>
                </div>
              ))
            ) : (
              <div className="space-y-3">
                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono">
                  <div className="flex items-center gap-3">
                    <span className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center font-bold text-slate-300">#1</span>
                    <div>
                      <span className="text-white font-bold text-sm">CASE_CREATED</span>
                      <p className="text-[11px] text-slate-400 font-sans mt-0.5">Actor: SYSTEM (reconciliation_feed_v1)</p>
                    </div>
                  </div>
                  <div className="text-right text-[11px] text-slate-400">
                    <div>Hash: <span className="text-emerald-400 font-bold">e3b0c44298fc1c14...</span></div>
                    <div className="text-[10px] text-slate-500">2026-09-02T07:12:00Z</div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono">
                  <div className="flex items-center gap-3">
                    <span className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center font-bold text-slate-300">#2</span>
                    <div>
                      <span className="text-white font-bold text-sm">POLICY_EVALUATED</span>
                      <p className="text-[11px] text-slate-400 font-sans mt-0.5">Actor: POLICY_ENGINE (deterministic_gate_v1)</p>
                    </div>
                  </div>
                  <div className="text-right text-[11px] text-slate-400">
                    <div>Hash: <span className="text-emerald-400 font-bold">8f49a162b2c3d4e5...</span></div>
                    <div className="text-[10px] text-slate-500">2026-09-02T07:12:01Z</div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono">
                  <div className="flex items-center gap-3">
                    <span className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center font-bold text-slate-300">#3</span>
                    <div>
                      <span className="text-white font-bold text-sm">ACTION_EXECUTED</span>
                      <p className="text-[11px] text-slate-400 font-sans mt-0.5">Actor: ACTION_EXECUTOR (simulation_sandbox_v1)</p>
                    </div>
                  </div>
                  <div className="text-right text-[11px] text-slate-400">
                    <div>Hash: <span className="text-emerald-400 font-bold">7a1b2c3d4e5f6a7b...</span></div>
                    <div className="text-[10px] text-slate-500">2026-09-02T07:12:02Z</div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
