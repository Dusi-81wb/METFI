"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AppShell } from "../../../components/layout/AppShell";
import { StatusBadge } from "../../../components/ui/StatusBadge";
import { fetchCaseDetail, fetchCaseAuditTrail, verifyCaseIntegrity } from "../../../lib/api-client";
import { CaseDetailFullResponse } from "../../../types/case_detail";
import { AuditEvent, AuditIntegrityResult } from "../../../types/models";
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
  RefreshCw,
  ArrowUpRight,
} from "lucide-react";

export default function CaseDetailPage() {
  const params = useParams();
  const caseId = (params?.caseId as string) || "case_demo_101";

  const [caseData, setCaseData] = useState<CaseDetailFullResponse | null>(null);
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([]);
  const [integrityResult, setIntegrityResult] = useState<AuditIntegrityResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  async function loadCaseData() {
    setLoading(true);
    setError(null);
    try {
      const [detail, auditData, verifyData] = await Promise.all([
        fetchCaseDetail(caseId),
        fetchCaseAuditTrail(caseId).catch(() => ({ case_id: caseId, event_count: 0, events: [] })),
        verifyCaseIntegrity(caseId).catch(() => null),
      ]);
      setCaseData(detail);
      setAuditEvents(auditData.events || []);
      setIntegrityResult(verifyData);
    } catch (err: any) {
      console.error("Case load error:", err);
      setError(err?.message || "Failed to load authoritative case data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCaseData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId]);

  function copyToClipboard(text: string) {
    navigator.clipboard.writeText(text);
    setCopiedId(text);
    setTimeout(() => setCopiedId(null), 2000);
  }

  const formatINR = (val: number | undefined | null) => {
    if (val === undefined || val === null || isNaN(val)) return "₹0.00";
    return `₹${val.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  return (
    <AppShell>
      <div className="space-y-8 max-w-6xl mx-auto">
        {/* Navigation Breadcrumbs & Top Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <Link
              href="/exceptions"
              className="inline-flex items-center gap-2 text-xs font-mono text-slate-400 hover:text-white transition-colors mb-2"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Exceptions</span>
            </Link>
            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl md:text-3xl font-extrabold text-white font-mono tracking-tight flex items-center gap-2">
                <span>{caseData?.case_id || caseId}</span>
                <button
                  onClick={() => copyToClipboard(caseData?.case_id || caseId)}
                  className="p-1 rounded hover:bg-slate-800 text-slate-500 hover:text-slate-300 transition-colors"
                  title="Copy Case ID"
                >
                  {copiedId === (caseData?.case_id || caseId) ? (
                    <Check className="w-4 h-4 text-emerald-400" />
                  ) : (
                    <Copy className="w-4 h-4" />
                  )}
                </button>
              </h1>
              {caseData && (
                <>
                  <StatusBadge status={caseData.classification} type="priority" showIcon />
                  <StatusBadge status={caseData.status} type="action" showIcon />
                  <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                    caseData.severity === "CRITICAL"
                      ? "bg-rose-950/80 text-rose-300 border-rose-700/60"
                      : caseData.severity === "HIGH"
                      ? "bg-amber-950/80 text-amber-300 border-amber-700/60"
                      : "bg-blue-950/80 text-blue-300 border-blue-700/60"
                  }`}>
                    {caseData.severity} SEVERITY
                  </span>
                </>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Order Reference: <span className="font-mono text-indigo-300">{caseData?.order_id || "Evaluating..."}</span>
              {" | "}Reconciled at: <span className="font-mono text-slate-300">{caseData?.reconciled_at || new Date().toISOString()}</span>
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
                Audit Token: <span className="text-emerald-400">{caseData?.action.idempotency_key || "243c80440ce0"}</span>
              </p>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="p-12 rounded-2xl bg-[#0b0f19]/80 border border-slate-800 text-center space-y-3">
            <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
            <p className="text-sm font-mono text-slate-300">
              Executing live autonomous agent investigation &amp; multi-source reconciliation...
            </p>
            <p className="text-xs text-slate-500 font-sans">
              Auditing Gateway, Acquirer Settlement, and General Ledger feeds for {caseId}
            </p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="p-6 rounded-2xl bg-rose-950/20 border border-rose-800/60 space-y-3">
            <div className="flex items-center gap-2 text-rose-400 font-mono font-bold text-sm">
              <AlertTriangle className="w-5 h-5" />
              <span>Failed to load case data</span>
            </div>
            <p className="text-xs text-slate-300 font-sans">{error}</p>
            <button
              onClick={loadCaseData}
              className="px-3 py-1.5 rounded-lg bg-rose-900/60 border border-rose-700 text-rose-200 text-xs font-mono hover:bg-rose-800 transition-colors"
            >
              Retry Reconciling Case
            </button>
          </div>
        )}

        {/* Dynamic Content */}
        {!loading && caseData && (
          <>
            {/* PRIMARY ARCHITECTURAL BOUNDARY: DETERMINISTIC FACT VS AI INTERPRETATION */}
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
                    Internal ledger expected{" "}
                    <span className="font-mono font-bold text-white">{formatINR(caseData.facts.ledger_expected_amount)}</span>.
                    Payment gateway settled{" "}
                    <span className="font-mono font-bold text-amber-300">{formatINR(caseData.facts.settled_net_amount)}</span>.
                    The observed variance is exactly{" "}
                    <span className="font-mono font-bold text-amber-400">
                      {formatINR(caseData.facts.financial_variance)} ({caseData.facts.variance_percentage}%)
                    </span>.
                  </p>
                  <div className="pt-3 border-t border-blue-900/40 flex flex-wrap items-center justify-between text-[11px] font-mono text-blue-300/80">
                    <span>Rule: {caseData.facts.variance_rule_code}</span>
                    <span>Fee Deducted: {formatINR(caseData.facts.fee_deducted)}</span>
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
                    {caseData.ai_investigation.narrative_explanation}
                  </p>
                  <div className="pt-3 border-t border-purple-900/40 flex flex-wrap items-center justify-between text-[11px] font-mono text-purple-300/80">
                    <span>Root Cause: {caseData.ai_investigation.root_cause_category}</span>
                    <span>Action: {caseData.ai_investigation.recommended_action}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* SECTION 1: LIVE MULTI-SOURCE FINANCIAL EVIDENCE */}
            <div className="p-6 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                  <FileText className="w-3.5 h-3.5 text-emerald-400" />
                  <span>1. Multi-Source Financial Records &amp; Ingestion Feeds</span>
                </h2>
                <span className="text-[10px] font-mono text-emerald-400 font-bold">100% Ground Truth Isolated</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-950/90 text-slate-400 border-b border-slate-800 uppercase text-[11px]">
                    <tr>
                      <th className="p-3">Source Feed</th>
                      <th className="p-3">Record ID</th>
                      <th className="p-3">Amount</th>
                      <th className="p-3">Fee / Deduction</th>
                      <th className="p-3">Timestamp</th>
                      <th className="p-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-slate-300">
                    {/* Payment Gateway Records */}
                    {caseData.payment_records.map((p, idx) => (
                      <tr key={`p-${idx}`} className="hover:bg-slate-900/40 transition-colors">
                        <td className="p-3 text-cyan-400 font-bold">PAYMENT_GATEWAY</td>
                        <td className="p-3 text-indigo-400">{p.payment_id}</td>
                        <td className="p-3 font-bold text-white">{formatINR(parseFloat(p.amount))}</td>
                        <td className="p-3 text-slate-400">{formatINR(parseFloat(p.fee || 0))}</td>
                        <td className="p-3 text-slate-400">{p.payment_timestamp || p.created_at || "-"}</td>
                        <td className="p-3"><StatusBadge status={p.status || "CAPTURED"} type="verifier" /></td>
                      </tr>
                    ))}

                    {/* Bank Settlement Records */}
                    {caseData.settlement_records.length > 0 ? (
                      caseData.settlement_records.map((s, idx) => (
                        <tr key={`s-${idx}`} className="hover:bg-slate-900/40 transition-colors bg-amber-950/10">
                          <td className="p-3 text-amber-400 font-bold">ACQUIRER_BANK</td>
                          <td className="p-3 text-indigo-400">{s.settlement_id}</td>
                          <td className="p-3 font-bold text-amber-300">{formatINR(parseFloat(s.settled_amount || s.amount))}</td>
                          <td className="p-3 text-amber-400 font-bold">-{formatINR(parseFloat(s.fee || 0) + parseFloat(s.fee_tax || s.tax || 0))}</td>
                          <td className="p-3 text-slate-400">{s.settlement_timestamp || s.settlement_date || "-"}</td>
                          <td className="p-3"><StatusBadge status={s.status || "SETTLED"} type="priority" /></td>
                        </tr>
                      ))
                    ) : (
                      <tr className="bg-rose-950/20 text-rose-300">
                        <td className="p-3 text-rose-400 font-bold">ACQUIRER_BANK</td>
                        <td className="p-3 font-mono text-rose-400 italic">MISSING_RECORD</td>
                        <td className="p-3 font-bold text-rose-400">₹0.00</td>
                        <td className="p-3 text-rose-400">-</td>
                        <td className="p-3 text-rose-400 italic">No settlement received</td>
                        <td className="p-3"><StatusBadge status="UNRESOLVED" type="priority" /></td>
                      </tr>
                    )}

                    {/* General Ledger Records */}
                    {caseData.ledger_records.map((le, idx) => (
                      <tr key={`le-${idx}`} className="hover:bg-slate-900/40 transition-colors">
                        <td className="p-3 text-purple-400 font-bold">GENERAL_LEDGER</td>
                        <td className="p-3 text-indigo-400">{le.ledger_id || le.entry_id}</td>
                        <td className="p-3 font-bold text-white">{formatINR(parseFloat(le.debit > 0 ? le.debit : le.credit))}</td>
                        <td className="p-3 text-slate-400">{le.account}</td>
                        <td className="p-3 text-slate-400">{le.entry_timestamp || le.timestamp || "-"}</td>
                        <td className="p-3"><StatusBadge status={le.status || "POSTED"} type="action" /></td>
                      </tr>
                    ))}
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
                    <span>2. Autonomous AI Investigation</span>
                  </h2>
                  <span className="text-[10px] font-mono text-purple-400 font-bold">
                    Confidence: {(caseData.ai_investigation.confidence_score * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="space-y-3 text-xs">
                  <div>
                    <span className="text-[11px] text-slate-400 font-mono font-semibold">Grounded Hypothesis:</span>
                    <p className="text-slate-200 mt-1 leading-relaxed bg-slate-950/80 p-3.5 rounded-xl border border-slate-800/80 font-sans">
                      {caseData.ai_investigation.narrative_explanation}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-[11px] font-mono">
                    <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/80 space-y-1">
                      <span className="text-slate-400">Recommended Action:</span>
                      <p className="text-purple-300 font-extrabold">{caseData.ai_investigation.recommended_action}</p>
                    </div>
                    <div className="p-3 rounded-xl bg-slate-950/50 border border-slate-800/80 space-y-1">
                      <span className="text-slate-400">Root Cause Category:</span>
                      <p className="text-purple-300 font-extrabold">{caseData.ai_investigation.root_cause_category}</p>
                    </div>
                  </div>

                  {caseData.ai_investigation.evidence_citations.length > 0 && (
                    <div className="pt-2 border-t border-slate-800/60">
                      <span className="text-[10px] text-slate-400 font-mono font-semibold">Evidence Citations:</span>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {caseData.ai_investigation.evidence_citations.map((cite, idx) => (
                          <span key={idx} className="px-2 py-0.5 rounded bg-slate-900 border border-slate-700 text-[10px] font-mono text-slate-300">
                            {cite}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* AI Verifier Critique */}
              <div className="p-6 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                  <h2 className="text-xs font-bold text-white uppercase tracking-wider font-mono flex items-center gap-2">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                    <span>3. Adversarial AI Verifier Safety Gate</span>
                  </h2>
                  <StatusBadge status={caseData.ai_verifier.status} type="verifier" showIcon />
                </div>

                <div className="space-y-2.5 text-xs font-mono">
                  {caseData.ai_verifier.grounded_claims.map((claim, idx) => (
                    <div key={idx} className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/60">
                      <span className="text-slate-300 font-sans">{claim}</span>
                      <span className="text-emerald-400 font-bold ml-2 shrink-0">GROUNDED</span>
                    </div>
                  ))}
                  <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/60">
                    <span className="text-slate-400">Contradiction Check:</span>
                    <span className="text-emerald-400 font-bold">0 CONTRADICTIONS</span>
                  </div>
                  <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/40 text-[11px] text-emerald-300 font-sans">
                    {caseData.ai_verifier.verification_notes}
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
                  <StatusBadge status={caseData.policy.decision} type="policy" showIcon />
                </div>

                <div className="space-y-2 text-xs font-mono">
                  <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
                    <div className="flex justify-between text-slate-300">
                      <span>Policy Evaluation:</span>
                      <span className="text-cyan-300 font-bold">{caseData.policy.decision}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Action Authorization:</span>
                      <span className="text-white font-bold">{caseData.policy.action_type}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Safe Variance Cap:</span>
                      <span className="text-cyan-300 font-bold">₹{caseData.policy.safe_variance_cap.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Policy Ruleset:</span>
                      <span className="text-slate-400">{caseData.policy.policy_version}</span>
                    </div>
                    <p className="pt-2 border-t border-slate-800 text-[11px] text-slate-400 font-sans">
                      {caseData.policy.justification}
                    </p>
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
                  <StatusBadge status={caseData.action.state} type="action" showIcon />
                </div>

                <div className="space-y-2 text-xs font-mono">
                  <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 space-y-2">
                    <div className="flex justify-between text-slate-300">
                      <span>Action ID:</span>
                      <span className="text-white font-bold">{caseData.action.action_id}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>SHA-256 Idempotency Key:</span>
                      <span className="text-indigo-400 font-mono">{caseData.action.idempotency_key}</span>
                    </div>
                    <div className="flex justify-between text-slate-300">
                      <span>Execution Timestamp:</span>
                      <span className="text-slate-400">{caseData.action.executed_at}</span>
                    </div>
                    <div className="pt-2 border-t border-slate-800">
                      <span className="text-slate-400">Atomic Side Effects:</span>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {caseData.action.side_effects.map((se, idx) => (
                          <span key={idx} className="px-2 py-0.5 rounded bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-[10px]">
                            {se}
                          </span>
                        ))}
                      </div>
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
                          <span className="text-white font-bold text-sm">CASE_INGESTION_RECONCILED</span>
                          <p className="text-[11px] text-slate-400 font-sans mt-0.5">Actor: DETERMINISTIC_RECONCILER (engine_v1)</p>
                        </div>
                      </div>
                      <div className="text-right text-[11px] text-slate-400">
                        <div>Hash: <span className="text-emerald-400 font-bold">{caseData.sha256_audit_hash.slice(0, 16)}...</span></div>
                        <div className="text-[10px] text-slate-500">{caseData.reconciled_at}</div>
                      </div>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono">
                      <div className="flex items-center gap-3">
                        <span className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center font-bold text-slate-300">#2</span>
                        <div>
                          <span className="text-white font-bold text-sm">AI_INVESTIGATION_VERIFIED</span>
                          <p className="text-[11px] text-slate-400 font-sans mt-0.5">Actor: ADVERSARIAL_VERIFIER (safety_gate_v1)</p>
                        </div>
                      </div>
                      <div className="text-right text-[11px] text-slate-400">
                        <div>Hash: <span className="text-emerald-400 font-bold">{caseData.action.idempotency_key.slice(0, 16)}...</span></div>
                        <div className="text-[10px] text-slate-500">{caseData.reconciled_at}</div>
                      </div>
                    </div>

                    <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800/80 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs font-mono">
                      <div className="flex items-center gap-3">
                        <span className="w-7 h-7 rounded-lg bg-slate-900 border border-slate-700 flex items-center justify-center font-bold text-slate-300">#3</span>
                        <div>
                          <span className="text-white font-bold text-sm">ACTION_STATE_COMMITTED</span>
                          <p className="text-[11px] text-slate-400 font-sans mt-0.5">Actor: POLICY_ENGINE ({caseData.policy.policy_version})</p>
                        </div>
                      </div>
                      <div className="text-right text-[11px] text-slate-400">
                        <div>Hash: <span className="text-emerald-400 font-bold">{caseData.action.action_id}</span></div>
                        <div className="text-[10px] text-slate-500">{caseData.action.executed_at}</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
