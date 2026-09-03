"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { AppShell } from "../../components/layout/AppShell";
import { StatusBadge } from "../../components/ui/StatusBadge";
import {
  fetchAvailableDatasets,
  fetchSampleData,
  generateRandomData,
  testReconcileGeneratedData,
} from "../../lib/api-client";
import {
  DatasetMetadata,
  RandomGenerationResponse,
  SampleDataResponse,
} from "../../types/data";
import {
  Database,
  Sliders,
  Sparkles,
  RefreshCw,
  Search,
  Play,
  Layers,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  FileCode2,
  Clock,
  Zap,
  Info,
  ChevronRight,
  Filter,
} from "lucide-react";

export default function SampleDataPage() {
  // Navigation tabs: 'catalog' (Explore Demo Data) vs 'randomizer' (Live Generator)
  const [activeTab, setActiveTab] = useState<"catalog" | "randomizer">("catalog");

  // Catalog state
  const [datasets, setDatasets] = useState<DatasetMetadata[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<string>("dev_500");
  const [selectedFeed, setSelectedFeed] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState<string>("");
  const [sampleData, setSampleData] = useState<SampleDataResponse | null>(null);
  const [catalogLoading, setCatalogLoading] = useState<boolean>(true);
  const [selectedJsonRecord, setSelectedJsonRecord] = useState<Record<string, any> | null>(null);

  // Randomizer state
  const [temperature, setTemperature] = useState<number>(0.35);
  const [anomalyProfile, setAnomalyProfile] = useState<string>("AUTO");
  const [recordCount, setRecordCount] = useState<number>(1);
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [generatedData, setGeneratedData] = useState<RandomGenerationResponse | null>(null);
  const [isReconciling, setIsReconciling] = useState<boolean>(false);
  const [reconciliationResult, setReconciliationResult] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Initial load
  useEffect(() => {
    fetchAvailableDatasets()
      .then((data) => {
        setDatasets(data);
        if (data.length > 0) {
          setSelectedDataset(data[0].dataset_id);
        }
      })
      .catch((err) => {
        console.error("Failed to load datasets:", err);
      });
  }, []);

  // Fetch sample data when dataset, feed, or search changes
  useEffect(() => {
    setCatalogLoading(true);
    fetchSampleData({
      dataset_id: selectedDataset,
      source: selectedFeed,
      limit: 20,
      search: searchTerm.trim() || undefined,
    })
      .then((res) => {
        setSampleData(res);
        setCatalogLoading(false);
      })
      .catch((err) => {
        setErrorMsg(err.message || "Failed to load sample feed records");
        setCatalogLoading(false);
      });
  }, [selectedDataset, selectedFeed, searchTerm]);

  // Handle random generation
  async function handleGenerate() {
    setIsGenerating(true);
    setReconciliationResult(null);
    setErrorMsg(null);
    try {
      const res = await generateRandomData({
        count: recordCount,
        temperature: temperature,
        anomaly_profile: anomalyProfile,
      });
      setGeneratedData(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to generate random transaction records");
    } finally {
      setIsGenerating(false);
    }
  }

  // Handle live reconciliation test on generated data
  async function handleTestOnPlatform() {
    if (!generatedData) return;
    setIsReconciling(true);
    setErrorMsg(null);
    try {
      const res = await testReconcileGeneratedData({
        dataset_id: generatedData.generated_dataset_id,
        payments: generatedData.payments,
        settlements: generatedData.settlements,
        ledger_entries: generatedData.ledger_entries,
      });
      setReconciliationResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Reconciliation test failed");
    } finally {
      setIsReconciling(false);
    }
  }

  // Helper to interpret entropy temperature
  function getTemperatureInfo(temp: number) {
    if (temp <= 0.15) {
      return {
        label: "Strict Canonical (Zero Entropy)",
        badgeColor: "text-emerald-400 bg-emerald-950/80 border-emerald-700/60",
        desc: "Strict deterministic match. Fees and amounts balance perfectly across all 3 feeds.",
      };
    } else if (temp <= 0.55) {
      return {
        label: "Moderate Entropy (Operational Variance)",
        badgeColor: "text-amber-400 bg-amber-950/80 border-amber-700/60",
        desc: "Injects realistic fee differences, gateway interchange changes, or date cut-off shifts.",
      };
    } else {
      return {
        label: "High Entropy (Chaotic Anomaly)",
        badgeColor: "text-rose-400 bg-rose-950/80 border-rose-700/60",
        desc: "Heavy anomalies: missing bank settlements, gross amount rounding, or unlinked records.",
      };
    }
  }

  const tempInfo = getTemperatureInfo(temperature);
  const currentDatasetMeta = datasets.find((d) => d.dataset_id === selectedDataset);

  return (
    <AppShell>
      <div className="space-y-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-indigo-950/80 border border-indigo-700/60 text-indigo-300 text-[11px] font-mono font-semibold mb-2">
              <Database className="w-3.5 h-3.5" />
              <span>TRANSPARENT FINANCIAL FEEDS</span>
            </div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight">
              Sample Data Explorer &amp; Live Randomizer
            </h1>
            <p className="text-xs text-slate-400 mt-1 font-sans">
              Inspect actual multi-source transaction feeds used in demo execution, or synthesize temperature-controlled random transactions for instant engine evaluation.
            </p>
          </div>

          {/* Top-Level Mode Selector */}
          <div className="inline-flex p-1 rounded-2xl bg-[#0b0f19] border border-slate-800 self-start sm:self-auto font-mono text-xs">
            <button
              onClick={() => setActiveTab("catalog")}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${
                activeTab === "catalog"
                  ? "bg-indigo-600 text-white font-bold shadow-sm shadow-indigo-500/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>Explore Demo Feeds</span>
            </button>
            <button
              onClick={() => {
                setActiveTab("randomizer");
                if (!generatedData) {
                  handleGenerate();
                }
              }}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-all ${
                activeTab === "randomizer"
                  ? "bg-indigo-600 text-white font-bold shadow-sm shadow-indigo-500/30"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              <Sliders className="w-3.5 h-3.5" />
              <span>Live Randomizer &amp; Test</span>
            </button>
          </div>
        </div>

        {errorMsg && (
          <div className="p-4 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs font-mono flex items-center gap-3">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* TAB 1: EXPLORE DEMO FEEDS */}
        {activeTab === "catalog" && (
          <div className="space-y-6">
            {/* Dataset Selector Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {datasets.map((d) => (
                <button
                  key={d.dataset_id}
                  onClick={() => setSelectedDataset(d.dataset_id)}
                  className={`p-4 rounded-2xl border text-left transition-all ${
                    selectedDataset === d.dataset_id
                      ? "bg-indigo-950/40 border-indigo-500/80 shadow-md shadow-indigo-950/50"
                      : "bg-[#0b0f19]/90 border-slate-800/80 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-white font-mono">{d.dataset_id}</span>
                    {d.is_live_fixture && (
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-950/80 border border-emerald-700/60 text-emerald-400 font-semibold">
                        LIVE DEMO
                      </span>
                    )}
                  </div>
                  <h3 className="text-xs font-semibold text-slate-200 line-clamp-1">{d.name}</h3>
                  <p className="text-[11px] text-slate-400 mt-1 line-clamp-2">{d.description}</p>
                  <div className="mt-3 pt-2.5 border-t border-slate-800/60 flex items-center justify-between text-[10px] font-mono text-slate-400">
                    <span>{d.total_records} Records</span>
                    <span>{d.file_size_kb} KB</span>
                  </div>
                </button>
              ))}
            </div>

            {/* Filter & Search Bar */}
            <div className="p-4 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 flex flex-col md:flex-row items-center justify-between gap-4">
              {/* Feed tabs */}
              <div className="flex flex-wrap items-center gap-1.5 self-stretch md:self-auto font-mono text-xs">
                {[
                  { id: "all", label: "Unified Multi-Source (3-Way)" },
                  { id: "payments", label: "Payment Gateway Feed" },
                  { id: "settlements", label: "Bank Settlement Feed" },
                  { id: "ledger", label: "General Ledger Feed" },
                ].map((feed) => (
                  <button
                    key={feed.id}
                    onClick={() => setSelectedFeed(feed.id)}
                    className={`px-3 py-1.5 rounded-xl transition-all text-[11px] font-semibold ${
                      selectedFeed === feed.id
                        ? "bg-slate-800 text-white border border-slate-700"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {feed.label}
                  </button>
                ))}
              </div>

              {/* Search input */}
              <div className="relative w-full md:w-72">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Filter by ID, account, amount..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-8 pr-3 py-1.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>
            </div>

            {/* Data Tables */}
            {catalogLoading ? (
              <div className="p-12 text-center text-xs font-mono text-slate-500 bg-[#0b0f19]/90 rounded-2xl border border-slate-800/80">
                <RefreshCw className="w-5 h-5 animate-spin mx-auto mb-2 text-indigo-400" />
                Loading operational records from disk...
              </div>
            ) : (
              <div className="space-y-6">
                {/* 1. Payments Feed Table */}
                {(selectedFeed === "all" || selectedFeed === "payments") && (
                  <div className="rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 overflow-hidden">
                    <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-emerald-400" />
                        <h2 className="text-xs font-bold text-white font-mono uppercase tracking-wider">
                          Payment Gateway Transactions
                        </h2>
                        <span className="text-[10px] text-slate-500 font-mono">
                          ({sampleData?.payments?.length || 0} shown)
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400">Ingest Feed: GATEWAY_API</span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-slate-950/60 text-[11px] text-slate-400 border-b border-slate-800/80">
                          <tr>
                            <th className="py-3 px-4">Payment ID</th>
                            <th className="py-3 px-4">Order Ref</th>
                            <th className="py-3 px-4">Gross Amount</th>
                            <th className="py-3 px-4">Fee / Tax</th>
                            <th className="py-3 px-4">Net</th>
                            <th className="py-3 px-4">Status</th>
                            <th className="py-3 px-4">Timestamp</th>
                            <th className="py-3 px-4 text-right">Raw</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                          {sampleData?.payments?.map((p, idx) => (
                            <tr key={p.payment_id || idx} className="hover:bg-slate-900/40 transition-colors">
                              <td className="py-3 px-4 font-bold text-indigo-300">{p.payment_id}</td>
                              <td className="py-3 px-4 text-slate-300">{p.order_id}</td>
                              <td className="py-3 px-4 font-bold text-white">₹{p.amount}</td>
                              <td className="py-3 px-4 text-slate-400">
                                ₹{p.fee || "0.00"} / ₹{p.tax || "0.00"}
                              </td>
                              <td className="py-3 px-4 text-emerald-400">
                                ₹{p.net || p.amount}
                              </td>
                              <td className="py-3 px-4">
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950/80 border border-emerald-800/60 text-emerald-300">
                                  {p.status}
                                </span>
                              </td>
                              <td className="py-3 px-4 text-slate-400 text-[11px]">
                                {p.payment_timestamp || p.created_at || "—"}
                              </td>
                              <td className="py-3 px-4 text-right">
                                <button
                                  onClick={() => setSelectedJsonRecord(p)}
                                  className="text-[10px] text-indigo-400 hover:text-indigo-300 font-bold hover:underline"
                                >
                                  JSON
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* 2. Settlements Feed Table */}
                {(selectedFeed === "all" || selectedFeed === "settlements") && (
                  <div className="rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 overflow-hidden">
                    <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-cyan-400" />
                        <h2 className="text-xs font-bold text-white font-mono uppercase tracking-wider">
                          Bank Settlement Payout Statements
                        </h2>
                        <span className="text-[10px] text-slate-500 font-mono">
                          ({sampleData?.settlements?.length || 0} shown)
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400">Ingest Feed: BANK_NEFT_CAMT</span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-slate-950/60 text-[11px] text-slate-400 border-b border-slate-800/80">
                          <tr>
                            <th className="py-3 px-4">Settlement ID</th>
                            <th className="py-3 px-4">Banking UTR</th>
                            <th className="py-3 px-4">Payout Amount</th>
                            <th className="py-3 px-4">Deducted Fee</th>
                            <th className="py-3 px-4">Status</th>
                            <th className="py-3 px-4">Settlement Date</th>
                            <th className="py-3 px-4 text-right">Raw</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                          {sampleData?.settlements?.map((s, idx) => (
                            <tr key={s.settlement_id || idx} className="hover:bg-slate-900/40 transition-colors">
                              <td className="py-3 px-4 font-bold text-cyan-300">{s.settlement_id}</td>
                              <td className="py-3 px-4 text-slate-300 font-mono text-[11px]">{s.utr || "—"}</td>
                              <td className="py-3 px-4 font-bold text-white">
                                ₹{s.settled_amount || s.amount}
                              </td>
                              <td className="py-3 px-4 text-amber-300">
                                ₹{s.fee || "0.00"}
                              </td>
                              <td className="py-3 px-4">
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-cyan-950/80 border border-cyan-800/60 text-cyan-300">
                                  {s.status}
                                </span>
                              </td>
                              <td className="py-3 px-4 text-slate-400 text-[11px]">
                                {s.settlement_date || s.settlement_timestamp || "—"}
                              </td>
                              <td className="py-3 px-4 text-right">
                                <button
                                  onClick={() => setSelectedJsonRecord(s)}
                                  className="text-[10px] text-indigo-400 hover:text-indigo-300 font-bold hover:underline"
                                >
                                  JSON
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* 3. Ledger Feed Table */}
                {(selectedFeed === "all" || selectedFeed === "ledger") && (
                  <div className="rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 overflow-hidden">
                    <div className="p-4 border-b border-slate-800/80 flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-purple-400" />
                        <h2 className="text-xs font-bold text-white font-mono uppercase tracking-wider">
                          Internal Accounting General Ledger
                        </h2>
                        <span className="text-[10px] text-slate-500 font-mono">
                          ({sampleData?.ledger_entries?.length || 0} shown)
                        </span>
                      </div>
                      <span className="text-[10px] font-mono text-slate-400">Ingest Feed: ERP_JOURNAL</span>
                    </div>

                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-xs font-mono">
                        <thead className="bg-slate-950/60 text-[11px] text-slate-400 border-b border-slate-800/80">
                          <tr>
                            <th className="py-3 px-4">Entry ID</th>
                            <th className="py-3 px-4">Chart of Account</th>
                            <th className="py-3 px-4">Debit</th>
                            <th className="py-3 px-4">Credit</th>
                            <th className="py-3 px-4">Reference ID</th>
                            <th className="py-3 px-4">Status</th>
                            <th className="py-3 px-4 text-right">Raw</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                          {sampleData?.ledger_entries?.map((le, idx) => (
                            <tr key={le.ledger_id || le.entry_id || idx} className="hover:bg-slate-900/40 transition-colors">
                              <td className="py-3 px-4 font-bold text-purple-300">{le.ledger_id || le.entry_id}</td>
                              <td className="py-3 px-4 text-slate-300 font-bold">{le.account}</td>
                              <td className="py-3 px-4 text-emerald-400 font-bold">
                                {le.debit && le.debit !== "0.00" ? `₹${le.debit}` : "—"}
                              </td>
                              <td className="py-3 px-4 text-rose-400 font-bold">
                                {le.credit && le.credit !== "0.00" ? `₹${le.credit}` : "—"}
                              </td>
                              <td className="py-3 px-4 text-slate-400 text-[11px]">
                                {le.order_id || le.reference_id || "—"}
                              </td>
                              <td className="py-3 px-4">
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-purple-950/80 border border-purple-800/60 text-purple-300">
                                  {le.status}
                                </span>
                              </td>
                              <td className="py-3 px-4 text-right">
                                <button
                                  onClick={() => setSelectedJsonRecord(le)}
                                  className="text-[10px] text-indigo-400 hover:text-indigo-300 font-bold hover:underline"
                                >
                                  JSON
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* TAB 2: LIVE RANDOMIZER & PLATFORM TEST */}
        {activeTab === "randomizer" && (
          <div className="space-y-8">
            {/* Generator Control Panel */}
            <div className="p-6 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 space-y-6">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800/80 pb-4">
                <div>
                  <h2 className="text-base font-bold text-white font-mono flex items-center gap-2">
                    <Sliders className="w-4 h-4 text-indigo-400" />
                    <span>Synthetic Multi-Source Transaction Generator</span>
                  </h2>
                  <p className="text-xs text-slate-400 font-sans mt-0.5">
                    Tune the entropy parameter to synthesize custom anomalies or exact matches, then run live deterministic reconciliation on the platform.
                  </p>
                </div>

                <button
                  onClick={handleGenerate}
                  disabled={isGenerating}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white text-xs font-bold font-mono shadow-md shadow-indigo-600/20 transition-all disabled:opacity-50 shrink-0"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${isGenerating ? "animate-spin" : ""}`} />
                  <span>{isGenerating ? "Synthesizing..." : "Randomize / Generate New Case"}</span>
                </button>
              </div>

              {/* Slider & Options Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* 1. Entropy / Temperature Slider */}
                <div className="space-y-3 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-white font-mono">
                      Entropy Temperature: <strong className="text-cyan-400">{temperature.toFixed(2)}</strong>
                    </span>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${tempInfo.badgeColor}`}>
                      {tempInfo.label}
                    </span>
                  </div>

                  <input
                    type="range"
                    min="0.0"
                    max="1.0"
                    step="0.05"
                    value={temperature}
                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                    className="w-full accent-indigo-500 cursor-pointer"
                  />

                  <p className="text-[11px] text-slate-400 font-sans">{tempInfo.desc}</p>
                </div>

                {/* 2. Anomaly Profile Scenario */}
                <div className="space-y-3 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <span className="text-xs font-bold text-white font-mono">Scenario Preset</span>
                  <select
                    value={anomalyProfile}
                    onChange={(e) => setAnomalyProfile(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-200 font-mono focus:outline-none focus:border-indigo-500"
                  >
                    <option value="AUTO">Auto (Driven by Temperature Slider)</option>
                    <option value="EXACT_MATCH">Strict Exact Match (Clean Reconciliation)</option>
                    <option value="FEE_DISCREPANCY">Fee Discrepancy (Interchange Delta)</option>
                    <option value="AMOUNT_MISMATCH">Amount Mismatch (Rounding Variance)</option>
                    <option value="MISSING_SETTLEMENT">Missing Settlement (Unsettled Capture)</option>
                    <option value="DATE_MISMATCH">Date Mismatch (Timing Cut-off Drift)</option>
                  </select>
                  <p className="text-[11px] text-slate-400 font-sans">
                    Force a specific defect class or let the entropy slider decide anomaly distribution.
                  </p>
                </div>

                {/* 3. Record Count */}
                <div className="space-y-3 p-4 rounded-xl bg-slate-950/60 border border-slate-800/80">
                  <span className="text-xs font-bold text-white font-mono">Batch Size (50+ Synthetic)</span>
                  <div className="grid grid-cols-4 gap-1.5">
                    {[1, 5, 50, 100].map((cnt) => (
                      <button
                        key={cnt}
                        type="button"
                        onClick={() => setRecordCount(cnt)}
                        className={`py-2 rounded-xl text-[11px] font-mono font-bold transition-all ${
                          recordCount === cnt
                            ? "bg-indigo-600 text-white"
                            : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
                        }`}
                      >
                        {cnt}
                      </button>
                    ))}
                  </div>
                  <p className="text-[11px] text-slate-400 font-sans">
                    Generate single cases or 50+ record synthetic batches.
                  </p>
                </div>
              </div>
            </div>

            {/* Generated Feeds Display & Reconciliation Action */}
            {generatedData && (
              <div className="space-y-6">
                {/* Summary Banner & Platform Test Trigger */}
                <div className="p-5 rounded-2xl bg-indigo-950/30 border border-indigo-500/40 flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 font-mono text-xs font-bold text-indigo-300">
                      <Sparkles className="w-4 h-4 text-cyan-400" />
                      <span>Generated Ephemeral Batch: {generatedData.generated_dataset_id}</span>
                      <span className="text-slate-500 font-normal">| Seed: {generatedData.seed}</span>
                    </div>
                    <p className="text-xs text-slate-300 font-sans">
                      {generatedData.anomaly_summary}
                    </p>
                  </div>

                  <button
                    onClick={handleTestOnPlatform}
                    disabled={isReconciling}
                    className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-extrabold font-mono shadow-lg shadow-emerald-600/20 transition-all disabled:opacity-50 shrink-0"
                  >
                    <Zap className={`w-4 h-4 ${isReconciling ? "animate-spin" : ""}`} />
                    <span>{isReconciling ? "Evaluating Rules..." : "⚡ Run Platform Reconciliation"}</span>
                  </button>
                </div>

                {/* Platform Test Results Card */}
                {reconciliationResult && (
                  <div className="p-6 rounded-2xl bg-[#0b0f19] border border-emerald-500/50 shadow-xl shadow-emerald-950/30 space-y-4 animate-in fade-in duration-300">
                    <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                      <div className="flex items-center gap-2 font-mono">
                        <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                          Platform Reconciliation Evaluation
                        </h3>
                      </div>
                      <span className="text-[11px] font-mono text-emerald-400 font-bold">
                        100% Deterministic Verification
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      {reconciliationResult.results?.map((res: any, idx: number) => (
                        <div
                          key={res.case_id || idx}
                          className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2 font-mono text-xs"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-white">{res.case_id}</span>
                            <StatusBadge status={res.classification} type="verifier" />
                          </div>
                          <p className="text-[11px] text-slate-400 font-sans line-clamp-2">{res.summary}</p>
                          <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px]">
                            <span className="text-slate-500">Policy Gate:</span>
                            <span className="text-indigo-300 font-bold">{res.policy_outcome}</span>
                          </div>
                          {res.classification !== "EXACT_MATCH" && (
                            <Link
                              href={`/cases/${res.case_id}`}
                              className="mt-2 w-full inline-flex items-center justify-center gap-1 py-1.5 rounded-lg bg-indigo-950 border border-indigo-700/60 text-indigo-300 text-[10px] font-bold hover:bg-indigo-900 transition-colors"
                            >
                              <span>Inspect in Case Detail</span>
                              <ArrowRight className="w-3 h-3" />
                            </Link>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* 3-Way Feed Cards for Generated Data */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* Feed 1: Payment */}
                  <div className="p-5 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
                      <span className="text-xs font-bold text-emerald-400 font-mono uppercase tracking-wider">
                        1. Payment Gateway Feed
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">
                        {generatedData.payments.length} record(s)
                      </span>
                    </div>

                    <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                      {generatedData.payments.map((p, i) => (
                        <div key={i} className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 font-mono text-xs space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-indigo-300">{p.payment_id}</span>
                            <span className="text-white font-extrabold">₹{p.amount}</span>
                          </div>
                          <div className="text-[11px] text-slate-400 flex items-center justify-between">
                            <span>Fee: ₹{p.fee} | Tax: ₹{p.tax}</span>
                            <span className="text-emerald-400 font-semibold">Net: ₹{p.net}</span>
                          </div>
                          <div className="text-[10px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-800/40">
                            <span>Method: {p.payment_method}</span>
                            <span>{p.created_at?.slice(0, 19)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Feed 2: Settlement */}
                  <div className="p-5 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
                      <span className="text-xs font-bold text-cyan-400 font-mono uppercase tracking-wider">
                        2. Bank Settlement Feed
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">
                        {generatedData.settlements.length} record(s)
                      </span>
                    </div>

                    <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                      {generatedData.settlements.length === 0 ? (
                        <div className="p-6 text-center text-xs font-mono text-rose-400 bg-rose-950/20 rounded-xl border border-rose-900/50">
                          <AlertTriangle className="w-4 h-4 mx-auto mb-1" />
                          Settlement absent (Missing Settlement Anomaly)
                        </div>
                      ) : (
                        generatedData.settlements.map((s, i) => (
                          <div key={i} className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 font-mono text-xs space-y-1.5">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-cyan-300">{s.settlement_id}</span>
                              <span className="text-white font-extrabold">₹{s.settled_amount || s.amount}</span>
                            </div>
                            <div className="text-[11px] text-slate-400 flex items-center justify-between">
                              <span>UTR: {s.utr}</span>
                              <span className="text-amber-300 font-semibold">Fee: ₹{s.fee}</span>
                            </div>
                            <div className="text-[10px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-800/40">
                              <span>Date: {s.settlement_date}</span>
                              <span className="text-cyan-400">{s.status}</span>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>

                  {/* Feed 3: Ledger */}
                  <div className="p-5 rounded-2xl bg-[#0b0f19]/90 border border-slate-800/80 space-y-3">
                    <div className="flex items-center justify-between border-b border-slate-800/80 pb-2.5">
                      <span className="text-xs font-bold text-purple-400 font-mono uppercase tracking-wider">
                        3. General Ledger Feed
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">
                        {generatedData.ledger_entries.length} record(s)
                      </span>
                    </div>

                    <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                      {generatedData.ledger_entries.map((le, i) => (
                        <div key={i} className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800/80 font-mono text-xs space-y-1.5">
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-purple-300">{le.account}</span>
                            <span className={le.direction === "DEBIT" ? "text-emerald-400 font-bold" : "text-rose-400 font-bold"}>
                              {le.direction}: ₹{le.amount}
                            </span>
                          </div>
                          <div className="text-[10px] text-slate-500 flex items-center justify-between pt-1 border-t border-slate-800/40">
                            <span>ID: {le.ledger_id || le.entry_id}</span>
                            <span>{le.status}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* JSON Inspector Drawer Modal */}
        {selectedJsonRecord && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="w-full max-w-2xl bg-[#0b0f19] border border-slate-800 rounded-2xl p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
                <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                  <FileCode2 className="w-4 h-4 text-indigo-400" />
                  <span>Raw Ingest Payload Inspector</span>
                </div>
                <button
                  onClick={() => setSelectedJsonRecord(null)}
                  className="text-slate-400 hover:text-white text-xs font-mono px-2 py-1 rounded-lg bg-slate-900 border border-slate-800"
                >
                  ✕ Close
                </button>
              </div>

              <pre className="p-4 rounded-xl bg-slate-950 text-emerald-300 font-mono text-xs overflow-x-auto max-h-96 border border-slate-900">
                {JSON.stringify(selectedJsonRecord, null, 2)}
              </pre>

              <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 pt-2 border-t border-slate-800/60">
                <span>Deterministic Immutability: Enforced</span>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(selectedJsonRecord, null, 2));
                    alert("JSON copied to clipboard");
                  }}
                  className="text-indigo-400 hover:text-indigo-300 font-bold"
                >
                  Copy JSON
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </AppShell>
  );
}
