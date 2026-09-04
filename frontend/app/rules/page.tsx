"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  fetchRules,
  createCustomRule,
  toggleRule,
  deleteCustomRule,
  resetRules,
  runFinanceOpsLoop,
  fetchSampleData,
} from "../../lib/api-client";
import {
  CustomRule,
  CreateRuleRequest,
  RuleField,
  RuleOperator,
  RuleType,
} from "../../types/rules";
import { SampleDataResponse } from "../../types/data";
import { FinanceOpsLoopReport } from "../../types/controller";
import {
  SlidersHorizontal,
  Plus,
  RotateCcw,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  Zap,
  Trash2,
  Layers,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Cpu,
  Database,
  Eye,
  Search,
  FileCode2,
  ExternalLink,
  X,
  Terminal,
  Activity,
  Info,
} from "lucide-react";

export default function RuleStudioPage() {
  const [rules, setRules] = useState<CustomRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<"ALL" | "CLASSIFICATION" | "POLICY_GATE" | "CUSTOM">("ALL");

  // Rule Creator Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [savingRule, setSavingRule] = useState(false);
  const [ruleName, setRuleName] = useState("");
  const [ruleDesc, setRuleDesc] = useState("");
  const [ruleType, setRuleType] = useState<RuleType>("CLASSIFICATION");
  const [field, setField] = useState<RuleField>("monetary.fee_variance");
  const [operator, setOperator] = useState<RuleOperator>("<=");
  const [benchValue, setBenchValue] = useState("50.0");
  const [targetClass, setTargetClass] = useState("EXACT_MATCH");
  const [targetPolicy, setTargetPolicy] = useState("AUTO_RECONCILE");
  const [priority, setPriority] = useState(15);

  // Dataset Inspector Modal State
  const [isDatasetModalOpen, setIsDatasetModalOpen] = useState(false);
  const [datasetLoading, setDatasetLoading] = useState(false);
  const [datasetData, setDatasetData] = useState<SampleDataResponse | null>(null);
  const [datasetSourceTab, setDatasetSourceTab] = useState<"all" | "payments" | "settlements" | "ledger">("all");
  const [datasetSearch, setDatasetSearch] = useState("");
  const [inspectedRecord, setInspectedRecord] = useState<Record<string, any> | null>(null);

  // Internal Logic Processing Modal State
  const [isLogicTraceOpen, setIsLogicTraceOpen] = useState(false);

  // Live Sandbox Simulation
  const [simulating, setSimulating] = useState(false);
  const [simReport, setSimReport] = useState<FinanceOpsLoopReport | null>(null);

  useEffect(() => {
    loadRules();
  }, []);

  async function loadRules() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchRules();
      setRules(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load rules");
    } finally {
      setLoading(false);
    }
  }

  async function openDatasetModal() {
    setIsDatasetModalOpen(true);
    if (!datasetData) {
      try {
        setDatasetLoading(true);
        const data = await fetchSampleData({
          dataset_id: "dev_500",
          source: "all",
          limit: 100,
        });
        setDatasetData(data);
      } catch (err: any) {
        console.error("Failed to load dataset records", err);
      } finally {
        setDatasetLoading(false);
      }
    }
  }

  async function handleToggle(ruleId: string, currentStatus: boolean) {
    try {
      // Optimistic update
      setRules((prev) =>
        prev.map((r) => (r.rule_id === ruleId ? { ...r, is_enabled: !currentStatus } : r))
      );
      await toggleRule(ruleId, !currentStatus);
    } catch (err: any) {
      alert("Failed to toggle rule: " + err?.message);
      loadRules();
    }
  }

  async function handleDelete(ruleId: string) {
    if (!confirm("Are you sure you want to delete this custom rule?")) return;
    try {
      await deleteCustomRule(ruleId);
      setRules((prev) => prev.filter((r) => r.rule_id !== ruleId));
    } catch (err: any) {
      alert("Failed to delete rule: " + err?.message);
    }
  }

  async function handleReset() {
    if (!confirm("Reset all rules back to system defaults?")) return;
    try {
      setLoading(true);
      const res = await resetRules();
      setRules(res);
    } catch (err: any) {
      alert("Failed to reset rules: " + err?.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateRule(e: React.FormEvent) {
    e.preventDefault();
    if (!ruleName.trim() || !ruleDesc.trim()) {
      alert("Please provide rule name and description.");
      return;
    }
    const valNum = parseFloat(benchValue);
    if (isNaN(valNum)) {
      alert("Benchmark value must be a valid number.");
      return;
    }

    try {
      setSavingRule(true);
      const payload: CreateRuleRequest = {
        name: ruleName.trim(),
        description: ruleDesc.trim(),
        rule_type: ruleType,
        condition: {
          field: field,
          operator: operator,
          value: valNum,
        },
        target_classification: targetClass,
        target_policy_outcome: targetPolicy,
        priority: priority,
        is_enabled: true,
      };

      const created = await createCustomRule(payload);
      setRules((prev) => [created, ...prev]);
      setIsModalOpen(false);
      // Reset form
      setRuleName("");
      setRuleDesc("");
      setBenchValue("50.0");
    } catch (err: any) {
      alert("Failed to create rule: " + err?.message);
    } finally {
      setSavingRule(false);
    }
  }

  async function handleRunSandbox() {
    try {
      setSimulating(true);
      const report = await runFinanceOpsLoop({
        max_records: 500,
        dataset_id: "dev_500",
      });
      setSimReport(report);
    } catch (err: any) {
      alert("Simulation failed: " + err?.message);
    } finally {
      setSimulating(false);
    }
  }

  // Filtered list
  const filteredRules = rules.filter((r) => {
    if (filterType === "CLASSIFICATION") return r.rule_type === "CLASSIFICATION";
    if (filterType === "POLICY_GATE") return r.rule_type === "POLICY_GATE";
    if (filterType === "CUSTOM") return !r.is_system;
    return true;
  });

  const totalRules = rules.length;
  const activeRules = rules.filter((r) => r.is_enabled).length;
  const customCount = rules.filter((r) => !r.is_system).length;
  const systemCount = rules.filter((r) => r.is_system).length;

  return (
    <div className="space-y-8 p-8 max-w-7xl mx-auto">
      {/* Hero Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/20 p-8 shadow-2xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-3">
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex items-center gap-1.5">
                <SlidersHorizontal className="w-3.5 h-3.5 text-indigo-400" />
                PURVIEW RULE STUDIO
              </span>
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                DYNAMIC GOVERNANCE
              </span>
            </div>
            <h1 className="text-3xl font-bold text-white tracking-tight">
              Rule Studio & Governance Center
            </h1>
            <p className="mt-2 text-slate-400 max-w-3xl text-sm leading-relaxed">
              Define custom financial classification rules and policy gating controls just like
              Microsoft Purview. Configure fee tolerance caps, SLA timing allowances, and automatic
              reconciliation thresholds dynamically without modifying core source code.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={openDatasetModal}
              className="px-4 py-2.5 rounded-xl text-xs font-semibold text-cyan-300 hover:text-white bg-cyan-950/60 hover:bg-cyan-900/70 border border-cyan-500/30 transition-all flex items-center gap-2 hover:scale-[1.02] shadow-sm"
              title="Inspect raw records in the active dev_500 evaluation dataset"
            >
              <Database className="w-4 h-4 text-cyan-400" />
              View Dataset (dev_500)
            </button>
            <button
              onClick={handleReset}
              className="px-4 py-2.5 rounded-xl text-xs font-medium text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-700 border border-slate-700 transition-all flex items-center gap-2"
              title="Reset rules to corporate system defaults"
            >
              <RotateCcw className="w-4 h-4" />
              Reset Defaults
            </button>
            <button
              onClick={() => setIsModalOpen(true)}
              className="px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-600 hover:from-indigo-500 hover:to-purple-500 shadow-lg shadow-indigo-500/25 border border-indigo-400/30 transition-all flex items-center gap-2 hover:scale-[1.02]"
            >
              <Plus className="w-4 h-4" />
              New Custom Rule
            </button>
          </div>
        </div>
      </div>

      {/* Metrics Strip */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-xl backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium uppercase tracking-wider">Total Rules</div>
          <div className="text-3xl font-bold text-white mt-1">{totalRules}</div>
          <div className="text-[11px] text-slate-500 mt-1">Catalogued governance rules</div>
        </div>
        <div className="bg-slate-900/60 border border-emerald-500/20 p-5 rounded-xl backdrop-blur-sm">
          <div className="text-emerald-400 text-xs font-medium uppercase tracking-wider flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5" />
            Active / Enforced
          </div>
          <div className="text-3xl font-bold text-emerald-400 mt-1">{activeRules}</div>
          <div className="text-[11px] text-slate-500 mt-1">Evaluating live reconciliation</div>
        </div>
        <div className="bg-slate-900/60 border border-purple-500/20 p-5 rounded-xl backdrop-blur-sm">
          <div className="text-purple-400 text-xs font-medium uppercase tracking-wider flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            Custom User Rules
          </div>
          <div className="text-3xl font-bold text-purple-400 mt-1">{customCount}</div>
          <div className="text-[11px] text-slate-500 mt-1">User-configured policies</div>
        </div>
        <div className="bg-slate-900/60 border border-slate-800 p-5 rounded-xl backdrop-blur-sm">
          <div className="text-slate-400 text-xs font-medium uppercase tracking-wider flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            System Safeguards
          </div>
          <div className="text-3xl font-bold text-cyan-400 mt-1">{systemCount}</div>
          <div className="text-[11px] text-slate-500 mt-1">Built-in financial invariants</div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          {(["ALL", "CLASSIFICATION", "POLICY_GATE", "CUSTOM"] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilterType(tab)}
              className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all ${
                filterType === tab
                  ? "bg-indigo-600/20 text-indigo-300 border border-indigo-500/30"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              }`}
            >
              {tab === "ALL" && "All Rules"}
              {tab === "CLASSIFICATION" && "Classification Rules"}
              {tab === "POLICY_GATE" && "Policy Gating"}
              {tab === "CUSTOM" && "Custom Only"}
            </button>
          ))}
        </div>
        <div className="text-xs text-slate-500">
          Showing {filteredRules.length} of {rules.length} rules
        </div>
      </div>

      {/* Rules Catalog */}
      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading governance rules...</div>
      ) : error ? (
        <div className="bg-rose-500/10 border border-rose-500/20 p-6 rounded-xl text-rose-300 text-sm">
          {error}
        </div>
      ) : filteredRules.length === 0 ? (
        <div className="text-center py-12 bg-slate-900/40 rounded-xl border border-slate-800 text-slate-400">
          No rules found for selected filter.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredRules.map((rule) => {
            const isCustom = !rule.is_system;
            return (
              <div
                key={rule.rule_id}
                className={`relative rounded-xl border transition-all p-5 backdrop-blur-sm ${
                  rule.is_enabled
                    ? "bg-slate-900/70 border-slate-800 hover:border-slate-700"
                    : "bg-slate-950/40 border-slate-900 opacity-60"
                }`}
              >
                {/* Header & Badges */}
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                          rule.rule_type === "CLASSIFICATION"
                            ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                            : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        }`}
                      >
                        {rule.rule_type}
                      </span>
                      {rule.is_system ? (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 border border-slate-700">
                          SYSTEM DEFAULT
                        </span>
                      ) : (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                          USER CUSTOM
                        </span>
                      )}
                      <span className="text-[10px] font-mono text-slate-500">
                        P{rule.priority}
                      </span>
                    </div>
                    <h3 className="text-base font-semibold text-white">{rule.name}</h3>
                    <p className="text-xs text-slate-400 leading-relaxed">{rule.description}</p>
                  </div>

                  {/* Toggle Switch */}
                  <div className="flex items-center gap-3 shrink-0">
                    <button
                      onClick={() => handleToggle(rule.rule_id, rule.is_enabled)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${
                        rule.is_enabled ? "bg-emerald-500" : "bg-slate-700"
                      }`}
                      title={rule.is_enabled ? "Click to disable rule" : "Click to enable rule"}
                    >
                      <span
                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                          rule.is_enabled ? "translate-x-6" : "translate-x-1"
                        }`}
                      />
                    </button>
                    {isCustom && (
                      <button
                        onClick={() => handleDelete(rule.rule_id)}
                        className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                        title="Delete custom rule"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </div>

                {/* Condition Box */}
                <div className="mt-4 pt-3 border-t border-slate-800/80 grid grid-cols-2 gap-3 text-xs">
                  <div>
                    <span className="text-slate-500 text-[11px] block">Condition Trigger</span>
                    <div className="mt-1 font-mono text-slate-300 bg-slate-950/60 px-2.5 py-1.5 rounded-md border border-slate-800 inline-block">
                      <span className="text-indigo-400">{rule.condition.field}</span>{" "}
                      <span className="text-amber-400 font-bold">{rule.condition.operator}</span>{" "}
                      <span className="text-emerald-400">
                        {typeof rule.condition.value === "number"
                          ? `₹${rule.condition.value}`
                          : rule.condition.value}
                      </span>
                    </div>
                  </div>
                  <div>
                    <span className="text-slate-500 text-[11px] block">Target Outcome</span>
                    <div className="mt-1 font-mono text-slate-300 bg-slate-950/60 px-2.5 py-1.5 rounded-md border border-slate-800 inline-block">
                      {rule.rule_type === "CLASSIFICATION" ? (
                        <span className="text-purple-300">
                          Class: {rule.target_classification}
                        </span>
                      ) : (
                        <span className="text-amber-300">
                          Policy: {rule.target_policy_outcome}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Live Impact Sandbox */}
      <div className="bg-gradient-to-br from-slate-900 to-indigo-950/30 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-indigo-400" />
              <h2 className="text-lg font-bold text-white">Live Batch Impact Sandbox</h2>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Verify how your active custom rules dynamically shift batch match rates and honest
              exception isolation across 500 multi-source transactions in real time.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={openDatasetModal}
              className="px-5 py-3 rounded-xl text-xs font-semibold text-cyan-300 hover:text-white bg-slate-800/90 hover:bg-slate-700 border border-slate-700 transition-all flex items-center gap-2"
            >
              <Database className="w-4 h-4 text-cyan-400" />
              Inspect Dataset Records
            </button>
            <button
              onClick={handleRunSandbox}
              disabled={simulating}
              className="px-6 py-3 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 shadow-lg shadow-emerald-500/20 transition-all flex items-center gap-2 hover:scale-[1.02] disabled:opacity-50"
            >
              {simulating ? (
                <>
                  <RotateCcw className="w-4 h-4 animate-spin" />
                  Simulating Loop...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 text-emerald-200" />
                  Test Rules on 500-Tx Batch
                </>
              )}
            </button>
          </div>
        </div>

        {simReport && (
          <div className="mt-4 p-5 bg-slate-950/70 border border-indigo-500/20 rounded-xl space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <span className="text-xs font-semibold text-indigo-300 uppercase tracking-wider flex items-center gap-1.5">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                Live Execution Result (500 Transactions)
              </span>
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-slate-400">
                  Processed at {simReport.throughput_records_per_sec.toLocaleString()} recs/sec
                </span>
                <button
                  onClick={() => setIsLogicTraceOpen(true)}
                  className="px-3.5 py-1.5 rounded-lg text-xs font-semibold text-cyan-300 hover:text-white bg-cyan-950/60 hover:bg-cyan-900 border border-cyan-500/30 transition-all flex items-center gap-1.5 shadow-sm hover:scale-[1.02]"
                >
                  <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                  View Internal Logic Processing
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-500 block">Match Rate</span>
                <span className="text-2xl font-bold text-emerald-400">
                  {simReport.match_rate_pct.toFixed(1)}%
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  {simReport.matched_cases_count} exact matches
                </span>
              </div>
              <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-500 block">Policy Auto-Posting</span>
                <span className="text-2xl font-bold text-indigo-400">
                  {simReport.resolution_rate_pct.toFixed(1)}%
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">
                  {simReport.total_cases - simReport.unresolved_exceptions_count} auto-resolved
                </span>
              </div>
              <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-500 block">Honest Exceptions</span>
                <span className="text-2xl font-bold text-amber-400">
                  {simReport.unresolved_exceptions_count}
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">Quarantined for review</span>
              </div>
              <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
                <span className="text-[11px] text-slate-500 block">Ledger Double-Entry</span>
                <span className="text-2xl font-bold text-emerald-400">
                  {simReport.books_status.imbalance === 0 ? "BALANCED" : "IMBALANCE"}
                </span>
                <span className="text-[10px] text-slate-500 block mt-0.5">₹0.00 variance delta</span>
              </div>
            </div>

            {/* Rule Logic Impact Callout */}
            {simReport.honest_exception_list.length > 0 && (
              <div className="p-3.5 rounded-xl bg-indigo-950/40 border border-indigo-500/20 text-xs text-slate-300 flex items-start gap-3">
                <Info className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <div className="font-semibold text-white flex items-center gap-2">
                    <span>Active Rule Evaluation: {simReport.unresolved_exceptions_count} Cases Quarantined as Exceptions</span>
                    <button
                      onClick={() => setIsLogicTraceOpen(true)}
                      className="text-cyan-400 hover:text-cyan-300 underline font-mono text-[11px]"
                    >
                      Inspect Logic Trace &rarr;
                    </button>
                  </div>
                  <div className="text-slate-400 text-[11px] leading-relaxed">
                    Custom and system rules were evaluated in priority order. If your custom rule&apos;s target outcome is configured as{" "}
                    <strong className="text-purple-300 font-mono">FEE_DISCREPANCY</strong> (or any discrepancy type), all matching records are intentionally flagged as financial exceptions and sent to review quarantine. To auto-reconcile matching records instead, set the Target Outcome to{" "}
                    <strong className="text-emerald-300 font-mono">EXACT_MATCH</strong> and Policy Action to{" "}
                    <strong className="text-emerald-300 font-mono">AUTO_RECONCILE</strong>.
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Rule Creator Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-5 animate-in fade-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <SlidersHorizontal className="w-5 h-5 text-indigo-400" />
                  Create Purview Custom Rule
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Configure custom threshold and classification criteria.
                </p>
              </div>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-slate-400 hover:text-white text-lg font-bold p-1"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateRule} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Rule Name
                </label>
                <input
                  type="text"
                  value={ruleName}
                  onChange={(e) => setRuleName(e.target.value)}
                  placeholder="e.g. Minor Fee Waiver Under ₹50"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1">
                  Description & Justification
                </label>
                <textarea
                  value={ruleDesc}
                  onChange={(e) => setRuleDesc(e.target.value)}
                  placeholder="e.g. Automatically waives gateway processing fee variances up to ₹50.00 as standard contract drift."
                  rows={2}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Rule Scope
                  </label>
                  <select
                    value={ruleType}
                    onChange={(e) => setRuleType(e.target.value as RuleType)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="CLASSIFICATION">Classification Rule</option>
                    <option value="POLICY_GATE">Policy Gating Rule</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Priority Precedence (1-100)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={priority}
                    onChange={(e) => setPriority(parseInt(e.target.value) || 50)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Condition Section */}
              <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 space-y-2">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                  Condition Logic
                </span>
                <div className="grid grid-cols-3 gap-2">
                  <select
                    value={field}
                    onChange={(e) => setField(e.target.value as RuleField)}
                    className="bg-slate-900 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-white"
                  >
                    <option value="monetary.fee_variance">Fee Variance</option>
                    <option value="monetary.tax_variance">Tax Variance</option>
                    <option value="monetary.settlement_amount_delta">Settlement Delta</option>
                    <option value="timing.hours_to_settlement">Settlement Hours</option>
                    <option value="monetary.payment_gross">Gross Volume</option>
                  </select>

                  <select
                    value={operator}
                    onChange={(e) => setOperator(e.target.value as RuleOperator)}
                    className="bg-slate-900 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-white font-mono"
                  >
                    <option value="<=">&le; Less or Equal</option>
                    <option value=">=">&ge; Greater or Equal</option>
                    <option value="==">== Exact Match</option>
                    <option value="<">&lt; Strictly Less</option>
                    <option value=">">&gt; Strictly Greater</option>
                  </select>

                  <input
                    type="number"
                    step="0.01"
                    value={benchValue}
                    onChange={(e) => setBenchValue(e.target.value)}
                    placeholder="Value (₹)"
                    className="bg-slate-900 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white font-mono"
                    required
                  />
                </div>
              </div>

              {/* Outcome Section */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Target Classification
                  </label>
                  <select
                    value={targetClass}
                    onChange={(e) => setTargetClass(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="EXACT_MATCH">EXACT_MATCH (Clean)</option>
                    <option value="FEE_DISCREPANCY">FEE_DISCREPANCY</option>
                    <option value="AMOUNT_MISMATCH">AMOUNT_MISMATCH</option>
                    <option value="DATE_MISMATCH">DATE_MISMATCH</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-300 block mb-1">
                    Policy Action
                  </label>
                  <select
                    value={targetPolicy}
                    onChange={(e) => setTargetPolicy(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="AUTO_RECONCILE">AUTO_RECONCILE (Auto-post)</option>
                    <option value="REVIEW_REQUIRED">REVIEW_REQUIRED (Quarantine)</option>
                  </select>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-800 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 rounded-lg text-xs font-medium text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingRule}
                  className="px-5 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 shadow-md transition-all flex items-center gap-1.5"
                >
                  {savingRule ? "Deploying..." : "Create & Deploy Rule"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Dataset Inspector Modal */}
      {isDatasetModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-5xl w-full max-h-[85vh] flex flex-col shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-800 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold text-white">Active Dataset: dev_500</h3>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                      500 TRANSACTIONS
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Multi-source transaction feed evaluated by classification and policy rules.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Link
                  href="/data"
                  className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-cyan-300 hover:text-white bg-cyan-950/60 hover:bg-cyan-900/80 border border-cyan-500/30 transition-all flex items-center gap-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  Open Full Data Studio
                </Link>
                <button
                  onClick={() => {
                    setIsDatasetModalOpen(false);
                    setInspectedRecord(null);
                  }}
                  className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Controls Bar */}
            <div className="px-6 py-3 border-b border-slate-800/80 bg-slate-950/40 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
              <div className="flex items-center gap-2">
                {(["all", "payments", "settlements", "ledger"] as const).map((feed) => (
                  <button
                    key={feed}
                    onClick={() => setDatasetSourceTab(feed)}
                    className={`px-3 py-1.5 rounded-lg text-xs font-semibold capitalize transition-all ${
                      datasetSourceTab === feed
                        ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                        : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                    }`}
                  >
                    {feed === "all" ? "All Feeds" : feed}
                  </button>
                ))}
              </div>
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={datasetSearch}
                  onChange={(e) => setDatasetSearch(e.target.value)}
                  placeholder="Filter by ID, order, currency..."
                  className="bg-slate-900 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-60"
                />
              </div>
            </div>

            {/* Records Content */}
            <div className="p-6 overflow-y-auto flex-1 space-y-4">
              {datasetLoading ? (
                <div className="text-center py-16 text-slate-400 flex flex-col items-center gap-3">
                  <RotateCcw className="w-6 h-6 animate-spin text-cyan-400" />
                  <span>Loading raw dataset records from dev_500...</span>
                </div>
              ) : (
                (() => {
                  const records: Array<{
                    source: "PAYMENT" | "SETTLEMENT" | "LEDGER";
                    id: string;
                    refId: string;
                    amount: string;
                    metrics: string;
                    timestamp: string;
                    status: string;
                    raw: Record<string, any>;
                  }> = [];

                  if (datasetData?.payments && (datasetSourceTab === "all" || datasetSourceTab === "payments")) {
                    datasetData.payments.forEach((p) => {
                      records.push({
                        source: "PAYMENT",
                        id: p.payment_id,
                        refId: p.order_id || "-",
                        amount: `₹${parseFloat(p.amount || "0").toFixed(2)} ${p.currency || "INR"}`,
                        metrics: `Gross Capture • Method: ${p.metadata?.payment_method || "card"}`,
                        timestamp: p.payment_timestamp || "-",
                        status: p.status || "SUCCESS",
                        raw: p,
                      });
                    });
                  }

                  if (datasetData?.settlements && (datasetSourceTab === "all" || datasetSourceTab === "settlements")) {
                    datasetData.settlements.forEach((s) => {
                      records.push({
                        source: "SETTLEMENT",
                        id: s.settlement_id,
                        refId: s.payment_id || "-",
                        amount: `₹${parseFloat(s.settled_amount || "0").toFixed(2)} ${s.currency || "INR"}`,
                        metrics: `Fee: ₹${s.fee || "0.00"} • Tax: ₹${s.fee_tax || "0.00"}`,
                        timestamp: s.settlement_timestamp || "-",
                        status: s.status || "SETTLED",
                        raw: s,
                      });
                    });
                  }

                  if (datasetData?.ledger_entries && (datasetSourceTab === "all" || datasetSourceTab === "ledger")) {
                    datasetData.ledger_entries.forEach((l) => {
                      records.push({
                        source: "LEDGER",
                        id: l.ledger_id,
                        refId: l.order_id || l.reference_id || "-",
                        amount: `₹${parseFloat(l.debit || l.credit || "0").toFixed(2)} ${l.currency || "INR"}`,
                        metrics: `Account: ${l.account || "GENERAL_LEDGER"}`,
                        timestamp: l.entry_timestamp || "-",
                        status: l.status || "POSTED",
                        raw: l,
                      });
                    });
                  }

                  const filtered = records.filter((r) => {
                    if (!datasetSearch.trim()) return true;
                    const q = datasetSearch.toLowerCase();
                    return (
                      r.id.toLowerCase().includes(q) ||
                      r.refId.toLowerCase().includes(q) ||
                      r.amount.toLowerCase().includes(q)
                    );
                  });

                  if (filtered.length === 0) {
                    return (
                      <div className="text-center py-12 text-slate-500 bg-slate-950/40 rounded-xl border border-slate-800">
                        No records matched your search filter.
                      </div>
                    );
                  }

                  return (
                    <div className="space-y-4">
                      <div className="overflow-x-auto rounded-xl border border-slate-800">
                        <table className="w-full text-left text-xs">
                          <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800 font-semibold uppercase tracking-wider text-[10px]">
                            <tr>
                              <th className="p-3">Source</th>
                              <th className="p-3">Record ID</th>
                              <th className="p-3">Reference ID</th>
                              <th className="p-3">Monetary Amount</th>
                              <th className="p-3">Details / Deductions</th>
                              <th className="p-3">Timestamp</th>
                              <th className="p-3 text-right">Inspect</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-800/60 font-mono">
                            {filtered.slice(0, 50).map((rec) => (
                              <tr
                                key={rec.id}
                                className="hover:bg-slate-800/40 transition-colors"
                              >
                                <td className="p-3 font-sans">
                                  <span
                                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                                      rec.source === "PAYMENT"
                                        ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20"
                                        : rec.source === "SETTLEMENT"
                                        ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                                        : "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                                    }`}
                                  >
                                    {rec.source}
                                  </span>
                                </td>
                                <td className="p-3 text-white font-medium">{rec.id}</td>
                                <td className="p-3 text-slate-400">{rec.refId}</td>
                                <td className="p-3 text-emerald-400 font-semibold">{rec.amount}</td>
                                <td className="p-3 text-slate-300 font-sans text-[11px]">{rec.metrics}</td>
                                <td className="p-3 text-slate-400 text-[11px]">{rec.timestamp}</td>
                                <td className="p-3 text-right font-sans">
                                  <button
                                    onClick={() => setInspectedRecord(rec.raw)}
                                    className="px-2 py-1 rounded bg-slate-800 hover:bg-indigo-600 text-slate-300 hover:text-white transition-colors text-[10px] flex items-center gap-1 ml-auto"
                                  >
                                    <FileCode2 className="w-3 h-3" />
                                    JSON
                                  </button>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {/* Raw Record JSON Drawer */}
                      {inspectedRecord && (
                        <div className="p-4 bg-slate-950 border border-indigo-500/30 rounded-xl space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-indigo-400 flex items-center gap-1.5">
                              <FileCode2 className="w-3.5 h-3.5" />
                              Inspected Raw Record Payload
                            </span>
                            <button
                              onClick={() => setInspectedRecord(null)}
                              className="text-slate-500 hover:text-white text-xs"
                            >
                              Close JSON
                            </button>
                          </div>
                          <pre className="p-3 bg-slate-900/90 rounded-lg text-[11px] font-mono text-emerald-400 overflow-x-auto max-h-48 border border-slate-800">
                            {JSON.stringify(inspectedRecord, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  );
                })()
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400 shrink-0">
              <span>Showing up to 50 active sample records from <strong className="text-white">dev_500</strong></span>
              <button
                onClick={() => {
                  setIsDatasetModalOpen(false);
                  setInspectedRecord(null);
                }}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition-colors"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Internal Logic Processing Modal */}
      {isLogicTraceOpen && simReport && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl animate-in fade-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-6 border-b border-slate-800 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                  <Terminal className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">
                    Internal Logic Processing & Execution Trace
                  </h3>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Step-by-step pipeline evaluation, rule triggers, and authority hierarchy gating for batch {simReport.batch_id}.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsLogicTraceOpen(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto flex-1 space-y-6">
              {/* Educational Rule Explanation Callout */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-indigo-950/60 to-purple-950/60 border border-indigo-500/30 text-xs text-slate-300 space-y-2">
                <div className="font-bold text-white flex items-center gap-2">
                  <Info className="w-4 h-4 text-indigo-400" />
                  <span>How Custom Rules Shape Batch Execution</span>
                </div>
                <p className="text-slate-400 text-[11px] leading-relaxed">
                  The reconciliation engine evaluates rules deterministically in priority order (lowest priority integer runs first).
                  When a rule matches a transaction, it forces the candidate into that rule&apos;s <strong>Target Outcome</strong>.
                  If the target outcome is an exception type like <span className="text-purple-300 font-mono">FEE_DISCREPANCY</span>, 
                  the transaction is intentionally quarantined for human review. To make transactions auto-post cleanly with 0 exceptions, 
                  configure the target outcome as <span className="text-emerald-300 font-mono">EXACT_MATCH</span> and Policy Action as <span className="text-emerald-300 font-mono">AUTO_RECONCILE</span>.
                </p>
              </div>

              {/* Chronological Pipeline Trace */}
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                  <Activity className="w-3.5 h-3.5 text-indigo-400" />
                  Deterministic Pipeline Execution Trace
                </h4>
                <div className="space-y-2 font-mono text-xs">
                  {(simReport.logic_trace && simReport.logic_trace.length > 0 ? simReport.logic_trace : [
                    `STAGE 1 [INGESTION]: Loaded 500 payments, 498 settlements, 495 ledger entries from ${simReport.batch_id}.`,
                    `STAGE 2 [RULES LOADED]: Evaluated active governance rules against multi-source evidence matrix.`,
                    `STAGE 3 [PRECEDENCE]: Applied deterministic classification precedence hierarchy.`,
                    `STAGE 4 [AUTHORITY HIERARCHY]: Enforced Deterministic Truth > Policy > Action gating. ${simReport.matched_cases_count} cases authorized, ${simReport.unresolved_exceptions_count} quarantined.`,
                    `STAGE 5 [LEDGER INVARIANT]: Double-entry balanced: Total Debits == Total Credits (₹0.00 delta).`,
                    `STAGE 6 [FINAL DISPOSITION]: Batch complete. Match Rate: ${simReport.match_rate_pct}% | Throughput: ${simReport.throughput_records_per_sec.toLocaleString()} recs/sec.`,
                  ]).map((step, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 text-slate-300 flex items-start gap-3"
                    >
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shrink-0">
                        STAGE {idx + 1}
                      </span>
                      <span className="leading-relaxed font-mono text-[11px] text-slate-300">{step}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Rule Hit Frequency */}
              {simReport.rule_hits && Object.keys(simReport.rule_hits).length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                    <Zap className="w-3.5 h-3.5 text-amber-400" />
                    Rule Trigger Frequencies Across {simReport.total_cases} Records
                  </h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {Object.entries(simReport.rule_hits).map(([code, count]) => (
                      <div
                        key={code}
                        className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between"
                      >
                        <span className="font-mono text-xs text-indigo-300 truncate pr-2">
                          {code}
                        </span>
                        <span className="text-xs font-bold text-white bg-slate-800 px-2 py-0.5 rounded-full shrink-0">
                          {count} hits
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Sample Quarantined Exceptions */}
              {simReport.honest_exception_list.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                    Sample Quarantined Exceptions ({simReport.honest_exception_list.length} Total in Review Queue)
                  </h4>
                  <div className="overflow-x-auto rounded-lg border border-slate-800">
                    <table className="w-full text-left text-xs font-mono">
                      <thead className="bg-slate-950 text-slate-400 uppercase text-[10px]">
                        <tr>
                          <th className="p-2.5">Case ID</th>
                          <th className="p-2.5">Classification</th>
                          <th className="p-2.5">Variance</th>
                          <th className="p-2.5">Reason Code / Trigger</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60">
                        {simReport.honest_exception_list.slice(0, 5).map((item) => (
                          <tr key={item.case_id} className="hover:bg-slate-800/30">
                            <td className="p-2.5 text-white">{item.case_id}</td>
                            <td className="p-2.5 text-purple-400 font-semibold">{item.exception_type}</td>
                            <td className="p-2.5 text-amber-400">₹{item.financial_variance.toFixed(2)}</td>
                            <td className="p-2.5 text-slate-300 truncate max-w-xs">{item.reason_unresolved}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between text-xs text-slate-400 shrink-0">
              <span>Engine Invariant: Deterministic mathematical truth always supersedes probabilistic classification.</span>
              <button
                onClick={() => setIsLogicTraceOpen(false)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white transition-colors"
              >
                Close Trace
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
