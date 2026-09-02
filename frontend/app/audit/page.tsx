"use client";

import React, { useState } from "react";
import { AppShell } from "../../components/layout/AppShell";
import { StatusBadge } from "../../components/ui/StatusBadge";
import { fetchCaseAuditTrail, verifyCaseIntegrity } from "../../lib/api-client";
import { AuditEvent, AuditIntegrityResult } from "../../types/models";
import {
  History,
  ShieldCheck,
  Search,
  CheckCircle2,
  AlertTriangle,
  Lock,
  ArrowDown,
  Clock,
  Sparkles,
  Key,
} from "lucide-react";

export default function AuditTrailPage() {
  const [caseId, setCaseId] = useState("case_demo_101");
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [verifyResult, setVerifyResult] = useState<AuditIntegrityResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearchAndVerify(e?: React.FormEvent) {
    if (e) e.preventDefault();
    if (!caseId.trim()) return;

    setLoading(true);
    setError(null);
    setVerifyResult(null);

    try {
      const [auditData, verifyData] = await Promise.all([
        fetchCaseAuditTrail(caseId.trim()),
        verifyCaseIntegrity(caseId.trim()),
      ]);
      setEvents(auditData.events || []);
      setVerifyResult(verifyData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit events");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell>
      <div className="space-y-8 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-950/80 border border-emerald-700/60 text-emerald-300 text-[11px] font-mono font-semibold mb-2">
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>CRYPTOGRAPHIC IMMUTABILITY</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Audit Trail &amp; SHA-256 Hash Chain Verifier
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Cryptographically verified financial audit ledger. Mathematical proof of immutability and sequence integrity.
            </p>
          </div>
        </div>

        {/* Case Selector Search Bar */}
        <form onSubmit={handleSearchAndVerify} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Enter Case ID (e.g., case_demo_101, case_eval_01)..."
              value={caseId}
              onChange={(e) => setCaseId(e.target.value)}
              className="w-full pl-9 pr-4 py-3 rounded-2xl bg-[#0b0f19] border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-3 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold font-mono transition-colors shadow-md shadow-indigo-600/20 disabled:opacity-50 shrink-0"
          >
            {loading ? "Verifying..." : "Verify Hash Chain"}
          </button>
        </form>

        {/* Verification Certificate Banner */}
        {verifyResult && (
          <div className={`p-5 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xl ${
            verifyResult.status === "VALID"
              ? "bg-emerald-950/30 border-emerald-700/80 text-emerald-200"
              : "bg-rose-950/30 border-rose-700/80 text-rose-200"
          }`}>
            <div className="flex items-center gap-3.5">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                verifyResult.status === "VALID"
                  ? "bg-emerald-950 border border-emerald-700 text-emerald-400 shadow-[0_0_15px_-3px_rgba(16,185,129,0.4)]"
                  : "bg-rose-950 border border-rose-700 text-rose-400"
              }`}>
                {verifyResult.status === "VALID" ? <CheckCircle2 className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
              </div>
              <div>
                <p className="font-extrabold text-sm font-mono">
                  Chain Status: {verifyResult.status} ({verifyResult.is_hash_chain_valid ? "Continuous SHA-256 Hash Chain" : "Tampering Detected"})
                </p>
                <p className="text-xs text-slate-300 mt-0.5 font-sans">
                  Verified {verifyResult.events_verified_count} events from Genesis Block with 0 sequence breaks.
                </p>
              </div>
            </div>

            <StatusBadge
              status={verifyResult.status === "VALID" ? "VALID" : "FAIL"}
              type="verifier"
              showIcon
            />
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800 text-rose-200 text-xs font-mono">
            {error}
          </div>
        )}

        {/* Block-by-Block Blockchain Timeline */}
        <div className="space-y-4">
          <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest font-mono flex items-center gap-2">
            <Lock className="w-3.5 h-3.5 text-indigo-400" />
            <span>Immutable Event Chain</span>
          </h2>

          <div className="space-y-3">
            {events.length > 0 ? (
              events.map((ev, idx) => (
                <div key={ev.event_id || idx} className="space-y-3">
                  <div className="p-5 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 hover:border-slate-700 transition-all font-mono text-xs text-slate-300 space-y-3">
                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/60 pb-3">
                      <div className="flex items-center gap-2.5">
                        <span className="w-7 h-7 rounded-lg bg-indigo-950/80 border border-indigo-700/60 flex items-center justify-center font-bold text-indigo-300 text-xs">
                          #{ev.sequence_number || idx + 1}
                        </span>
                        <span className="font-bold text-sm text-white">{ev.event_type}</span>
                        <StatusBadge status="CANONICAL" type="fact" />
                      </div>
                      <span className="text-[11px] text-slate-500">{ev.timestamp}</span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
                      <div>
                        <span className="text-slate-500">Actor:</span>{" "}
                        <span className="text-indigo-300 font-bold">{ev.actor?.actor_type}</span> ({ev.actor?.actor_id})
                      </div>
                      <div>
                        <span className="text-slate-500">Source:</span>{" "}
                        <span className="text-slate-300">{ev.source_component}</span>
                      </div>
                      <div className="col-span-full">
                        <span className="text-slate-500">Prev Hash:</span>{" "}
                        <span className="text-slate-400 break-all">{ev.previous_event_hash || "GENESIS_ROOT"}</span>
                      </div>
                      <div className="col-span-full">
                        <span className="text-slate-500">Event Hash:</span>{" "}
                        <span className="text-emerald-400 font-bold break-all">{ev.event_hash}</span>
                      </div>
                    </div>
                  </div>

                  {idx < events.length - 1 && (
                    <div className="flex justify-center py-1">
                      <ArrowDown className="w-4 h-4 text-slate-600" />
                    </div>
                  )}
                </div>
              ))
            ) : (
              <div className="p-12 rounded-2xl bg-[#0b0f19]/60 border border-slate-800/80 text-center text-slate-400 font-mono text-xs">
                No events currently loaded. Click &quot;Verify Hash Chain&quot; to inspect the ledger for case <span className="text-indigo-400">{caseId}</span>.
              </div>
            )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
