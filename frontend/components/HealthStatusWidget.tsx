"use client";

import React, { useEffect, useState } from "react";
import { 
  CheckCircle2, 
  XCircle, 
  RefreshCw, 
  Server, 
  ShieldCheck, 
  Cpu, 
  Lock, 
  FileText, 
  BarChart3,
  Clock,
  Sparkles
} from "lucide-react";
import { HealthResponse } from "../types";
import { fetchHealthStatus } from "../lib/api-client";

export function HealthStatusWidget() {
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);
  const [latencyMs, setLatencyMs] = useState<number | null>(null);

  const checkHealth = async () => {
    setLoading(true);
    setError(null);
    const start = performance.now();
    try {
      const response = await fetchHealthStatus();
      const end = performance.now();
      setData(response);
      setLatencyMs(Math.round(end - start));
      setLastChecked(new Date());
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to connect to backend server";
      setError(message);
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const subsystems = [
    {
      name: "Data Plane (Layer A)",
      description: "Synthetic generation & ground-truth isolation",
      status: data?.subsystems?.data_plane || "pending",
      icon: DatabaseIcon,
    },
    {
      name: "Deterministic Matcher (Layer D)",
      description: "Mathematical matching & rule evaluation",
      status: data?.subsystems?.deterministic_engine || "pending",
      icon: Cpu,
    },
    {
      name: "AI Intelligence (Layer E)",
      description: "Bounded anomaly investigation & reasoning",
      status: data?.subsystems?.intelligence_layer || "pending",
      icon: Sparkles,
    },
    {
      name: "Policy Engine (Layer F)",
      description: "Deterministic gatekeeper & action authorization",
      status: data?.subsystems?.policy_engine || "pending",
      icon: Lock,
    },
    {
      name: "Audit Trail (Layer G)",
      description: "Append-only immutable decision lineage",
      status: data?.subsystems?.audit_layer || "pending",
      icon: FileText,
    },
    {
      name: "Evaluation Harness (Layer H)",
      description: "Ground-truth benchmark validation & metrics",
      status: data?.subsystems?.evaluation_engine || "pending",
      icon: BarChart3,
    },
  ];

  return (
    <div className="w-full space-y-6">
      {/* Top Banner Status */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 shadow-xl backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-4">
            <div className={`flex h-12 w-12 items-center justify-center rounded-xl border ${
              data?.status === "healthy"
                ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
                : error
                ? "border-rose-500/30 bg-rose-500/10 text-rose-400"
                : "border-blue-500/30 bg-blue-500/10 text-blue-400"
            }`}>
              {loading ? (
                <RefreshCw className="h-6 w-6 animate-spin" />
              ) : data?.status === "healthy" ? (
                <CheckCircle2 className="h-6 w-6" />
              ) : (
                <XCircle className="h-6 w-6" />
              )}
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-semibold text-white">Backend Controller State</h2>
                <span className={`inline-flex items-center rounded-md px-2 py-0.5 text-xs font-semibold ${
                  data?.status === "healthy"
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-rose-500/10 text-rose-400 border border-rose-500/20"
                }`}>
                  {data?.status === "healthy" ? "OPERATIONAL" : "DISCONNECTED"}
                </span>
              </div>
              <p className="text-sm text-slate-400">
                {data ? `${data.service} • Environment: ${data.environment}` : "Checking connectivity to FastAPI runtime..."}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {latencyMs !== null && (
              <div className="flex items-center gap-1.5 rounded-lg border border-slate-800 bg-slate-950 px-3 py-1.5 text-xs text-slate-300">
                <Clock className="h-3.5 w-3.5 text-blue-400" />
                <span>Latency: {latencyMs}ms</span>
              </div>
            )}
            <button
              onClick={checkHealth}
              disabled={loading}
              className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-1.5 text-sm font-medium text-slate-200 hover:bg-slate-700 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 rounded-lg border border-rose-500/30 bg-rose-950/20 p-3 text-xs text-rose-300">
            <p className="font-semibold">Connection Error:</p>
            <p className="font-mono text-rose-400 mt-0.5">{error}</p>
          </div>
        )}
      </div>

      {/* Subsystem Layer Grid */}
      <div>
        <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-3">
          Architecture Layer Status
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {subsystems.map((sub, idx) => {
            const Icon = sub.icon;
            const isReady = sub.status === "ready";
            return (
              <div
                key={idx}
                className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 transition-all hover:border-slate-700"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-800 text-slate-300 border border-slate-700">
                      <Icon className="h-5 w-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-semibold text-white">{sub.name}</h4>
                      <p className="text-xs text-slate-400">{sub.description}</p>
                    </div>
                  </div>
                  <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                    isReady
                      ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                      : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                  }`}>
                    {sub.status}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function DatabaseIcon(props: React.SVGProps<SVGSVGElement>) {
  return <Server {...props} />;
}
