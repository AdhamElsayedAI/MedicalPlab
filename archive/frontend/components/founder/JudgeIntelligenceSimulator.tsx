"use client";

import React, { useState } from "react";
import {
  Scale,
  Cpu,
  Search,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Volume2,
  Code2,
  ShieldAlert,
  Sparkles,
  ArrowRight,
  HelpCircle,
} from "lucide-react";
import { JUDGE_QA_ITEMS } from "@/lib/founder-data";
import { JudgeQAItem } from "@/lib/types";

export const JudgeIntelligenceSimulator: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<"All" | "Technical" | "Business">("All");
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedId, setExpandedId] = useState<string>("tech_why_not_chatgpt");
  const [viewModeMap, setViewModeMap] = useState<Record<string, "executive" | "deep_dive">>({
    tech_why_not_chatgpt: "executive",
  });

  const filteredItems = JUDGE_QA_ITEMS.filter((item) => {
    const matchesCategory =
      selectedCategory === "All" || item.category === selectedCategory;
    const matchesSearch =
      searchQuery.trim() === "" ||
      item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      item.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase())) ||
      item.executiveSummary.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? "" : id));
  };

  const toggleViewMode = (id: string, mode: "executive" | "deep_dive") => {
    setViewModeMap((prev) => ({ ...prev, [id]: mode }));
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <Scale className="w-3.5 h-3.5 text-cyan-400" />
              JUDGE Q&A INTELLIGENCE SIMULATOR
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              11 DEFENSE SCENARIOS
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Hackathon & Investor Hardball Defense Simulator
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Rapid-fire 20–40 second answers with executive spoken scripts, technical architecture proof points, and follow-up defenses.
          </p>
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-1.5 bg-slate-900/90 p-1.5 rounded-xl border border-slate-800 self-start md:self-center">
          {(["All", "Technical", "Business"] as const).map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                selectedCategory === cat
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(0,242,254,0.25)]"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {cat} {cat === "Technical" ? "(6)" : cat === "Business" ? "(5)" : "(11)"}
            </button>
          ))}
        </div>
      </div>

      {/* Search Filter Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search judge questions, tags, or concepts (e.g., 'ChatGPT', 'RAG', 'Unit Economics', 'Hallucinations')..."
          className="w-full bg-slate-950/80 text-slate-100 placeholder-slate-500 text-xs sm:text-sm font-sans rounded-2xl pl-11 pr-4 py-3 border border-slate-800 focus:border-cyan-400 focus:outline-none transition-colors"
        />
      </div>

      {/* Q&A Accordion List */}
      <div className="space-y-4">
        {filteredItems.map((item) => {
          const isExpanded = expandedId === item.id;
          const currentMode = viewModeMap[item.id] || "executive";

          return (
            <div
              key={item.id}
              className={`rounded-2xl border transition-all ${
                isExpanded
                  ? "bg-slate-950/95 border-cyan-500/40 shadow-[0_0_30px_rgba(0,242,254,0.12)]"
                  : "bg-slate-950/60 border-slate-800/80 hover:border-slate-700"
              }`}
            >
              {/* Question Clickable Header */}
              <button
                onClick={() => toggleExpand(item.id)}
                className="w-full p-5 text-left flex items-start sm:items-center justify-between gap-4 focus:outline-none"
              >
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span
                      className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded uppercase ${
                        item.category === "Technical"
                          ? "bg-blue-950 text-blue-300 border border-blue-500/40"
                          : "bg-emerald-950 text-emerald-300 border border-emerald-500/40"
                      }`}
                    >
                      {item.category}
                    </span>
                    {item.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                  <h4 className="text-base sm:text-lg font-bold text-white tracking-wide">
                    {item.question}
                  </h4>
                </div>

                <div className="flex-shrink-0 p-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400">
                  {isExpanded ? (
                    <ChevronUp className="w-5 h-5 text-cyan-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5" />
                  )}
                </div>
              </button>

              {/* Expanded Answer Content */}
              {isExpanded && (
                <div className="px-5 pb-6 pt-2 border-t border-slate-800/80 space-y-5 animate-in fade-in duration-200">
                  {/* Mode Switcher Tabs */}
                  <div className="flex items-center gap-2 border-b border-slate-800 pb-3">
                    <button
                      onClick={() => toggleViewMode(item.id, "executive")}
                      className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold transition-all ${
                        currentMode === "executive"
                          ? "bg-cyan-950 text-cyan-300 border border-cyan-400/50 shadow-[0_0_10px_rgba(0,242,254,0.25)]"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      <Volume2 className="w-4 h-4 text-cyan-400" />
                      <span>Executive Spoken Answer (20–40s)</span>
                    </button>

                    <button
                      onClick={() => toggleViewMode(item.id, "deep_dive")}
                      className={`flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold transition-all ${
                        currentMode === "deep_dive"
                          ? "bg-purple-950 text-purple-300 border border-purple-400/50 shadow-[0_0_10px_rgba(168,85,247,0.25)]"
                          : "text-slate-400 hover:text-white"
                      }`}
                    >
                      <Code2 className="w-4 h-4 text-purple-400" />
                      <span>Technical Architecture Proof</span>
                    </button>
                  </div>

                  {/* Mode 1: Executive Spoken Answer */}
                  {currentMode === "executive" && (
                    <div className="p-4 rounded-2xl bg-cyan-950/20 border border-cyan-500/30 space-y-2">
                      <div className="flex items-center justify-between text-[11px] font-mono text-cyan-400">
                        <span className="font-bold uppercase tracking-wider flex items-center gap-1.5">
                          <Sparkles className="w-3.5 h-3.5" />
                          Founder Voice Delivery
                        </span>
                        <span>Estimated delivery: ~30 seconds</span>
                      </div>
                      <p className="text-sm sm:text-base text-slate-100 font-sans leading-relaxed">
                        &ldquo;{item.executiveSummary}&rdquo;
                      </p>
                    </div>
                  )}

                  {/* Mode 2: Technical Architecture Proof */}
                  {currentMode === "deep_dive" && (
                    <div className="space-y-3">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                          <span className="text-[11px] font-mono text-purple-400 block font-bold">
                            ACTIVE PIPELINE STAGES
                          </span>
                          <div className="flex flex-wrap gap-1.5 mt-1">
                            {item.technicalDeepDive.activeStages.map((st) => (
                              <span
                                key={st}
                                className="px-2 py-0.5 rounded text-[10px] font-mono bg-purple-950 text-purple-300 border border-purple-500/40 font-bold"
                              >
                                {st}
                              </span>
                            ))}
                          </div>
                        </div>

                        <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                          <span className="text-[11px] font-mono text-emerald-400 block font-bold">
                            DETERMINISTIC PROOF METRIC
                          </span>
                          <p className="text-xs text-slate-200 font-mono">
                            {item.technicalDeepDive.proofMetric}
                          </p>
                        </div>
                      </div>

                      <div className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-1.5">
                        <span className="text-[11px] font-mono text-cyan-400 block font-bold">
                          INTERNAL ARCHITECTURE MECHANISM
                        </span>
                        <p className="text-xs sm:text-sm text-slate-300 font-sans leading-relaxed">
                          {item.technicalDeepDive.architecture}
                        </p>
                      </div>

                      <div className="p-3 rounded-xl bg-black/80 border border-slate-800 font-mono text-xs text-emerald-400 overflow-x-auto">
                        <span className="text-[10px] text-slate-500 block mb-1">
                          // Verified Deterministic Contract Logic:
                        </span>
                        <code>{item.technicalDeepDive.codeContractOrLogic}</code>
                      </div>
                    </div>
                  )}

                  {/* Anticipated Judge Follow-up & Tactical Defense */}
                  <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-2">
                    <div className="flex items-center gap-2 text-xs font-mono text-amber-400 font-bold">
                      <HelpCircle className="w-4 h-4" />
                      <span>ANTICIPATED JUDGE FOLLOW-UP QUESTION</span>
                    </div>
                    <p className="text-xs sm:text-sm text-amber-200/90 font-sans italic">
                      &ldquo;{item.sampleJudgeFollowUp}&rdquo;
                    </p>
                    <div className="pt-2 border-t border-slate-800 flex items-start gap-2">
                      <span className="text-[11px] font-mono text-cyan-400 font-bold uppercase flex-shrink-0 mt-0.5">
                        Tactical Defense:
                      </span>
                      <p className="text-xs text-slate-300 font-sans leading-relaxed">
                        {item.followUpDefense}
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
