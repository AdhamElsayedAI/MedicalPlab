"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  Search,
  ChevronDown,
  ChevronUp,
  HelpCircle,
  Volume2,
  Code2,
  CheckCircle2,
  XCircle,
  BrainCircuit,
  Sparkles,
  Award,
} from "lucide-react";
import { JUDGE_ARENA_SCENARIOS } from "@/lib/stage-l-data";
import { JudgeMemoryItem } from "@/lib/types";

export const JudgeArena: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState<
    "All" | "Basic" | "Technical" | "Business" | "Clinical Safety"
  >("All");
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string>("tech_chatgpt_wrapper");
  const [showMemoryEngine, setShowMemoryEngine] = useState(true);

  const filtered = JUDGE_ARENA_SCENARIOS.filter((item) => {
    const matchCat = activeCategory === "All" || item.category === activeCategory;
    const matchSearch =
      search.trim() === "" ||
      item.question.toLowerCase().includes(search.toLowerCase()) ||
      item.hiddenJudgeConcern.toLowerCase().includes(search.toLowerCase()) ||
      item.winningFounderAnswer.toLowerCase().includes(search.toLowerCase());
    return matchCat && matchSearch;
  });

  const toggle = (id: string) => {
    setExpandedId((prev) => (prev === id ? "" : id));
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <ShieldAlert className="w-3.5 h-3.5 text-cyan-400" />
              JUDGE ARENA SIMULATOR
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              12 BATTLE SCENARIOS + JUDGE MEMORY ENGINE
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Adversarial Pitch Defense & Evaluation Intelligence
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Simulate hardball judge pressure testing with hidden concerns, winning founder answers, common traps to avoid, and technical proofs.
          </p>
        </div>

        {/* Memory Engine Toggle */}
        <div className="flex items-center gap-2 self-start md:self-center">
          <button
            onClick={() => setShowMemoryEngine(!showMemoryEngine)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono border transition-all ${
              showMemoryEngine
                ? "bg-purple-950 text-purple-300 border-purple-500/50 shadow-[0_0_12px_rgba(168,85,247,0.3)]"
                : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
            }`}
          >
            <BrainCircuit className="w-3.5 h-3.5 text-purple-400" />
            <span>Judge Memory Engine: {showMemoryEngine ? "ON" : "OFF"}</span>
          </button>
        </div>
      </div>

      {/* Category Pills & Search */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 overflow-x-auto bg-slate-900/90 p-1.5 rounded-xl border border-slate-800">
          {(["All", "Basic", "Technical", "Business", "Clinical Safety"] as const).map(
            (cat) => (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold whitespace-nowrap transition-all ${
                  activeCategory === cat
                    ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(0,242,254,0.25)]"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {cat}
              </button>
            )
          )}
        </div>

        <div className="relative flex-1 sm:max-w-xs">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter attacks..."
            className="w-full bg-slate-950 text-slate-100 placeholder-slate-500 text-xs rounded-xl pl-9 pr-3 py-2 border border-slate-800 focus:border-cyan-400 focus:outline-none"
          />
        </div>
      </div>

      {/* Accordion Questions */}
      <div className="space-y-4">
        {filtered.map((item) => {
          const isExp = expandedId === item.id;
          return (
            <div
              key={item.id}
              className={`rounded-2xl border transition-all ${
                isExp
                  ? "bg-slate-950/95 border-cyan-500/40 shadow-[0_0_30px_rgba(0,242,254,0.12)]"
                  : "bg-slate-950/60 border-slate-800/80 hover:border-slate-700"
              }`}
            >
              <button
                onClick={() => toggle(item.id)}
                className="w-full p-5 text-left flex items-start sm:items-center justify-between gap-4 focus:outline-none"
              >
                <div className="space-y-1.5">
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 text-[10px] font-mono font-bold rounded uppercase ${
                        item.category === "Basic"
                          ? "bg-slate-800 text-slate-300 border border-slate-700"
                          : item.category === "Technical"
                          ? "bg-blue-950 text-blue-300 border border-blue-500/40"
                          : item.category === "Business"
                          ? "bg-emerald-950 text-emerald-300 border border-emerald-500/40"
                          : "bg-rose-950 text-rose-300 border border-rose-500/40"
                      }`}
                    >
                      {item.category}
                    </span>
                    <span className="text-xs font-mono text-slate-500">ID: {item.id}</span>
                  </div>
                  <h4 className="text-base sm:text-lg font-bold text-white tracking-wide">
                    {item.question}
                  </h4>
                </div>

                <div className="flex-shrink-0 p-1.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-400">
                  {isExp ? <ChevronUp className="w-5 h-5 text-cyan-400" /> : <ChevronDown className="w-5 h-5" />}
                </div>
              </button>

              {isExp && (
                <div className="px-5 pb-6 pt-2 border-t border-slate-800/80 space-y-4 animate-in fade-in duration-200">
                  {/* Hidden Judge Concern */}
                  <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/30 space-y-1">
                    <div className="flex items-center gap-1.5 text-xs font-mono text-amber-400 font-bold">
                      <HelpCircle className="w-4 h-4" />
                      <span>HIDDEN JUDGE SKEPTICISM (WHAT THEY REALLY CARE ABOUT)</span>
                    </div>
                    <p className="text-xs sm:text-sm text-amber-200/90 font-sans leading-relaxed">
                      {item.hiddenJudgeConcern}
                    </p>
                  </div>

                  {/* Winning Founder Answer */}
                  <div className="p-4 rounded-2xl bg-cyan-950/25 border border-cyan-500/40 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono text-cyan-400">
                      <span className="font-bold uppercase tracking-wider flex items-center gap-1.5">
                        <Volume2 className="w-3.5 h-3.5" /> Winning Founder Answer (20–30s)
                      </span>
                      <span>Decisive & Evidence-Backed</span>
                    </div>
                    <p className="text-xs sm:text-sm text-slate-100 font-sans leading-relaxed font-medium">
                      &ldquo;{item.winningFounderAnswer}&rdquo;
                    </p>
                  </div>

                  {/* Judge Memory Engine Intelligence Block */}
                  {showMemoryEngine && (
                    <div className="p-5 rounded-2xl bg-purple-950/15 border border-purple-500/30 space-y-3">
                      <div className="flex items-center gap-1.5 text-xs font-mono text-purple-300 font-bold border-b border-purple-500/20 pb-2">
                        <BrainCircuit className="w-4 h-4 text-purple-400" />
                        <span>JUDGE MEMORY ENGINE: EVALUATION MATRIX & ANSWER BLUEPRINT</span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-sans">
                        {/* Evaluation Criteria & Winning Structure */}
                        <div className="space-y-2">
                          <span className="font-mono text-[11px] text-purple-300 block font-bold">
                            Evaluation Criteria:
                          </span>
                          <ul className="space-y-1 text-slate-300">
                            {item.evaluationCriteria.map((c, i) => (
                              <li key={i} className="flex items-center gap-1.5">
                                <CheckCircle2 className="w-3 h-3 text-emerald-400 flex-shrink-0" />
                                <span>{c}</span>
                              </li>
                            ))}
                          </ul>

                          <span className="font-mono text-[11px] text-cyan-300 block font-bold pt-2">
                            Winning Answer Structure:
                          </span>
                          <ol className="space-y-1 text-slate-300 list-decimal pl-4">
                            {item.winningAnswerStructure.map((s, i) => (
                              <li key={i}>{s}</li>
                            ))}
                          </ol>
                        </div>

                        {/* Weak Answers & Mistakes to Avoid */}
                        <div className="space-y-2">
                          <span className="font-mono text-[11px] text-rose-300 block font-bold">
                            Common Weak Answers (What Loses Hackathons):
                          </span>
                          <ul className="space-y-1 text-slate-400">
                            {item.commonWeakAnswers.map((w, i) => (
                              <li key={i} className="flex items-center gap-1.5 text-rose-200/80">
                                <XCircle className="w-3 h-3 text-rose-400 flex-shrink-0" />
                                <span>&ldquo;{w}&rdquo;</span>
                              </li>
                            ))}
                          </ul>

                          <span className="font-mono text-[11px] text-amber-300 block font-bold pt-2">
                            Critical Mistakes to Avoid:
                          </span>
                          <ul className="space-y-1 text-slate-300">
                            {item.mistakesToAvoid.map((m, i) => (
                              <li key={i} className="flex items-center gap-1.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-400 inline-block flex-shrink-0" />
                                <span>{m}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Technical Proof */}
                  <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2">
                    <span className="text-[11px] font-mono text-cyan-400 font-bold block">
                      TECHNICAL CONTRACT PROOF
                    </span>
                    <div className="p-2.5 rounded-xl bg-black/70 border border-slate-800 font-mono text-xs text-emerald-400 overflow-x-auto">
                      <code>{item.technicalProof.codeContract}</code>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 font-sans pt-1">
                      <span><strong>Metric:</strong> {item.technicalProof.metric}</span>
                      <span><strong>Mechanism:</strong> {item.technicalProof.mechanism}</span>
                    </div>
                  </div>

                  {/* Follow-Up Defense */}
                  <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-1">
                    <span className="text-[11px] font-mono text-slate-400 font-bold uppercase block">
                      Pre-Empting Hard Follow-Up Attack
                    </span>
                    <p className="text-xs text-slate-200 font-sans leading-relaxed">
                      {item.followUpDefense}
                    </p>
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
