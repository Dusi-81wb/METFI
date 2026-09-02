import React from "react";
import { ShieldCheck, Brain, Scale, Zap, AlertTriangle, CheckCircle2, Clock } from "lucide-react";

interface StatusBadgeProps {
  status: string;
  type?: "fact" | "interpretation" | "verifier" | "policy" | "action" | "priority" | "default";
  className?: string;
  showIcon?: boolean;
}

export function StatusBadge({ status, type = "default", className = "", showIcon = false }: StatusBadgeProps) {
  let colorClasses = "bg-slate-900/90 text-slate-300 border-slate-700/80";
  let icon: React.ReactNode = null;

  if (type === "fact") {
    colorClasses = "bg-blue-950/60 text-blue-300 border-blue-700/60 shadow-[0_0_12px_-3px_rgba(59,130,246,0.3)] font-mono tracking-wider font-semibold";
    if (showIcon) icon = <ShieldCheck className="w-3 h-3 text-blue-400 shrink-0" />;
  } else if (type === "interpretation") {
    colorClasses = "bg-purple-950/60 text-purple-300 border-purple-700/60 shadow-[0_0_12px_-3px_rgba(168,85,247,0.3)] font-mono tracking-wider font-semibold";
    if (showIcon) icon = <Brain className="w-3 h-3 text-purple-400 shrink-0" />;
  } else if (type === "verifier") {
    if (status === "VERIFIED" || status === "VALID" || status === "PASS") {
      colorClasses = "bg-emerald-950/60 text-emerald-300 border-emerald-700/60 shadow-[0_0_12px_-3px_rgba(16,185,129,0.3)] font-semibold";
      if (showIcon) icon = <CheckCircle2 className="w-3 h-3 text-emerald-400 shrink-0" />;
    } else if (status === "REJECTED" || status === "INTEGRITY_FAILURE" || status === "FAIL") {
      colorClasses = "bg-rose-950/70 text-rose-300 border-rose-700/80 shadow-[0_0_12px_-3px_rgba(244,63,94,0.3)] font-semibold animate-pulse";
      if (showIcon) icon = <AlertTriangle className="w-3 h-3 text-rose-400 shrink-0" />;
    } else {
      colorClasses = "bg-amber-950/60 text-amber-300 border-amber-700/60 font-semibold";
      if (showIcon) icon = <Clock className="w-3 h-3 text-amber-400 shrink-0" />;
    }
  } else if (type === "policy") {
    if (status === "ALLOW") {
      colorClasses = "bg-emerald-950/60 text-emerald-300 border-emerald-700/60 font-semibold";
      if (showIcon) icon = <Scale className="w-3 h-3 text-emerald-400 shrink-0" />;
    } else if (status === "DENY") {
      colorClasses = "bg-rose-950/60 text-rose-300 border-rose-700/60 font-semibold";
      if (showIcon) icon = <Scale className="w-3 h-3 text-rose-400 shrink-0" />;
    } else {
      colorClasses = "bg-amber-950/60 text-amber-300 border-amber-700/60 font-semibold";
      if (showIcon) icon = <Scale className="w-3 h-3 text-amber-400 shrink-0" />;
    }
  } else if (type === "action") {
    if (status === "EXECUTED") {
      colorClasses = "bg-emerald-950/60 text-emerald-300 border-emerald-700/60 font-semibold";
      if (showIcon) icon = <Zap className="w-3 h-3 text-emerald-400 shrink-0" />;
    } else if (status === "AUTHORIZED") {
      colorClasses = "bg-cyan-950/60 text-cyan-300 border-cyan-700/60 font-semibold";
      if (showIcon) icon = <Zap className="w-3 h-3 text-cyan-400 shrink-0" />;
    } else if (status === "REJECTED" || status === "FAILED") {
      colorClasses = "bg-rose-950/60 text-rose-300 border-rose-700/60 font-semibold";
      if (showIcon) icon = <AlertTriangle className="w-3 h-3 text-rose-400 shrink-0" />;
    } else {
      colorClasses = "bg-slate-900 text-slate-300 border-slate-700/60";
    }
  } else if (type === "priority") {
    if (status === "CRITICAL") {
      colorClasses = "bg-rose-950/80 text-rose-200 border-rose-600 font-bold shadow-[0_0_12px_-3px_rgba(244,63,94,0.4)]";
    } else if (status === "HIGH") {
      colorClasses = "bg-orange-950/70 text-orange-200 border-orange-700 font-semibold";
    } else if (status === "MEDIUM") {
      colorClasses = "bg-amber-950/60 text-amber-300 border-amber-700 font-medium";
    } else {
      colorClasses = "bg-slate-900/80 text-slate-400 border-slate-800";
    }
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] border backdrop-blur-sm transition-all duration-150 ${colorClasses} ${className}`}
    >
      {icon}
      <span>{status}</span>
    </span>
  );
}
