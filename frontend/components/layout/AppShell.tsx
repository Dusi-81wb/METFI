"use client";

import React, { useEffect, useState } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { fetchHealth } from "../../lib/api-client";
import { HealthResponse } from "../../types/models";

interface AppShellProps {
  children: React.ReactNode;
  searchQuery?: string;
  onSearchChange?: (q: string) => void;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  onOpenQA?: () => void;
  onTriggerReconcile?: () => void;
  isReconciling?: boolean;
  exceptionCount?: number;
  isBalanced?: boolean;
}

export function AppShell({
  children,
  searchQuery = "",
  onSearchChange,
  onRefresh,
  isRefreshing = false,
  onOpenQA,
  onTriggerReconcile,
  isReconciling = false,
  exceptionCount = 200,
  isBalanced = true,
}: AppShellProps) {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    fetchHealth()
      .then((data) => setHealth(data))
      .catch((err) => console.warn("AppShell health probe error:", err));
  }, []);

  return (
    <div className="flex h-screen bg-[#09090b] font-sans antialiased overflow-hidden text-zinc-100 selection:bg-indigo-500 selection:text-white">
      {/* Sleek Sidebar matching email_scheduler */}
      <Sidebar
        onTriggerReconcile={onTriggerReconcile}
        isReconciling={isReconciling}
        exceptionCount={exceptionCount}
      />

      {/* Main Column */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* TopBar with Search and Status */}
        <TopBar
          searchQuery={searchQuery}
          onSearchChange={onSearchChange || (() => {})}
          onRefresh={onRefresh || (() => {})}
          isRefreshing={isRefreshing}
          onOpenQA={onOpenQA}
          health={health}
          isBalanced={isBalanced}
        />

        {/* Scrollable Content View */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-7xl mx-auto w-full">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
