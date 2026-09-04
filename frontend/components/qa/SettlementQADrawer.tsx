"use client";

import React, { useState } from "react";
import { X, Sparkles, Send, ShieldCheck, HelpCircle, Bot, User as UserIcon } from "lucide-react";
import { askSettlementQA } from "../../lib/api-client";
import { SettlementQAResponse } from "../../types/controller";

interface SettlementQADrawerProps {
  isOpen: boolean;
  onClose: () => void;
  datasetId?: string;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  citedRecords?: string[];
}

export const SettlementQADrawer: React.FC<SettlementQADrawerProps> = ({
  isOpen,
  onClose,
  datasetId = "dev_500",
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content:
        "Hello Controller. I am your grounded settlement & cash position assistant. Ask me anything about bank liquidity, general ledger invariants, unresolvable exceptions, or match rates.",
    },
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const quickPrompts = [
    "What is our verified bank cash position?",
    "Are the books balanced and what is the debit credit status?",
    "What exceptions could not be resolved and why?",
    "What is our reconciliation throughput and accuracy?",
  ];

  const handleSend = async (queryText?: string) => {
    const text = queryText || inputQuery;
    if (!text.trim()) return;

    const userMsg: ChatMessage = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInputQuery("");
    setLoading(true);

    try {
      const res: SettlementQAResponse = await askSettlementQA({
        question: text,
        dataset_id: datasetId,
      });

      const botMsg: ChatMessage = {
        role: "assistant",
        content: res.answer,
        citedRecords: res.cited_records,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Unable to process financial query: ${err.message || "Network error"}`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs transition-opacity">
      <div className="w-full max-w-lg bg-[#111217] h-full shadow-2xl flex flex-col overflow-hidden border-l border-zinc-800 animate-in slide-in-from-right duration-200 text-zinc-100">
        {/* Header Bar */}
        <div className="h-16 px-6 border-b border-zinc-800 flex items-center justify-between shrink-0 bg-[#111217]">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-indigo-950 text-indigo-400 flex items-center justify-center font-bold border border-indigo-800/50">
              <Sparkles className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-zinc-100">Settlement Q&amp;A Agent</h2>
              <p className="text-[11px] text-zinc-400 font-mono">Grounded Financial Intelligence</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 rounded-full transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Suggested Quick Prompts */}
        <div className="p-3 border-b border-zinc-800 bg-zinc-900/60">
          <div className="flex items-center space-x-1 text-[11px] font-semibold text-zinc-400 mb-1.5">
            <HelpCircle className="w-3 h-3" />
            <span>Suggested Questions:</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {quickPrompts.map((prompt) => (
              <button
                key={prompt}
                type="button"
                onClick={() => handleSend(prompt)}
                className="text-[11px] px-2.5 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-300 hover:border-indigo-500 hover:text-indigo-400 transition-colors truncate max-w-xs text-left"
              >
                {prompt}
              </button>
            ))}
          </div>
        </div>

        {/* Chat Messages Container */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#09090b]">
          {messages.map((m, idx) => (
            <div
              key={idx}
              className={`flex items-start space-x-2.5 ${
                m.role === "user" ? "flex-row-reverse space-x-reverse" : ""
              }`}
            >
              <div
                className={`w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs ${
                  m.role === "user"
                    ? "bg-indigo-600 text-white"
                    : "bg-emerald-950 text-emerald-400 border border-emerald-800/50"
                }`}
              >
                {m.role === "user" ? <UserIcon className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>

              <div
                className={`p-3.5 rounded-2xl text-xs max-w-[85%] leading-relaxed ${
                  m.role === "user"
                    ? "bg-indigo-600 text-white rounded-tr-xs shadow-xs"
                    : "bg-[#14151b] text-zinc-200 border border-zinc-800 shadow-xs rounded-tl-xs"
                }`}
              >
                <div className="whitespace-pre-line font-sans">{m.content}</div>

                {m.citedRecords && m.citedRecords.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-zinc-800 text-[10px] text-zinc-400 font-mono">
                    <span className="font-semibold text-zinc-300">Authoritative Citations: </span>
                    {m.citedRecords.join(", ")}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex items-center space-x-2 text-xs text-zinc-400 p-2 font-mono">
              <div className="w-4 h-4 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
              <span>Querying verified books &amp; cash positions...</span>
            </div>
          )}
        </div>

        {/* Chat Input Box */}
        <div className="p-3 border-t border-zinc-800 bg-[#111217] flex items-center space-x-2">
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleSend();
            }}
            placeholder="Ask about cash positions, unresolvable exceptions, or books..."
            className="flex-1 px-4 py-2 bg-zinc-900 text-xs text-zinc-200 rounded-full border border-zinc-800 focus:bg-zinc-850 focus:border-indigo-500 focus:outline-none transition-all"
          />
          <button
            type="button"
            onClick={() => handleSend()}
            disabled={!inputQuery.trim() || loading}
            className="p-2 rounded-full bg-indigo-600 text-white hover:bg-indigo-500 disabled:opacity-40 transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
