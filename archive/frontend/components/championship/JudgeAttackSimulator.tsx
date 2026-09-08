"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  Search,
  ChevronDown,
  ChevronUp,
  Sparkles,
  HelpCircle,
  Code2,
  Volume2,
  ShieldCheck,
  Scale,
  Zap,
} from "lucide-react";
import { JUDGE_ATTACK_SCENARIOS } from "@/lib/championship-data";
import { JudgeAttackItem } from "@/lib/types";

export const JudgeAttackSimulator: React.FC = () => {
  const [selectedCat, setSelectedCat] = useState<"All" | "Technical" | "Clinical Safety" | "Business">("All");
  const [search, setSearch] = useState("");
  const [expandedId, setExpandedId] = useState<string>("attack_chatgpt_wrapper");

  const filtered = JUDGE_ATTACK_SCENARIOS.filter((item) => {
    const matchCat = selectedCat === "All" || item.category === selectedCat;
    const matchSearch =
      search.trim() === "" ||
      item.question.toLowerCase().includes(search.toLowerCase()) ||
      item.hiddenJudgeConcern.toLowerCase().includes(search.toLowerCase()) ||
      item.founderAnswer.toLowerCase().includes(search.toLowerCase());
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
              JUDGE ATTACK SIMULATOR
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              9 ADVERSARIAL SCENARIOS
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Anticipate Hidden Judge Concerns & Deliver Winning Defenses
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Revealing what the judges are actually skeptical about, backed by 20-second crisp founder responses and deterministic technical proofs.
          </p>
        </div>

        {/* Category Filter Pills */}
        <div className="flex items-center gap-1.5 bg-slate-900/90 p-1.5 rounded-xl border border-slate-800 self-start md:self-center">
          {(["All", "Technical", "Clinical Safety", "Business"] as const).map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCat(cat)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                selectedCat === cat
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_10px_rgba(0,242,254,0.25)]"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-slate-400 absolute left-4 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search judge attacks, hidden concerns, or keywords (e.g., 'Wrapper', 'Latency', 'NHS Procurement', 'Hallucination')..."
          className="w-full bg-slate-950/80 text-slate-100 placeholder-slate-500 text-xs sm:text-sm font-sans rounded-2xl pl-11 pr-4 py-3 border border-slate-800 focus:border-cyan-400 focus:outline-none transition-colors"
        />
      </div>

      {/* Accordion List */}
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
                        item.category === "Technical"
                          ? "bg-blue-950 text-blue-300 border border-blue-500/40"
                          : item.category === "Clinical Safety"
                          ? "bg-rose-950 text-rose-300 border border-rose-500/40"
                          : "bg-emerald-950 text-emerald-300 border border-emerald-500/40"
                      }`}
                    >
                      {item.category}
                    </span>
                    <span className="text-xs font-mono text-slate-500">
                      ID: {item.id}
                    </span>
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
                      <span>WHAT THE JUDGE IS ACTUALLY WORRIED ABOUT (HIDDEN SKEPTICISM)</span>
                    </div>
                    <p className="text-xs sm:text-sm text-amber-200/90 font-sans leading-relaxed">
                      {item.hiddenJudgeConcern}
                    </p>
                  </div>

                  {/* Crisp Founder Response */}
                  <div className="p-4 rounded-2xl bg-cyan-950/20 border border-cyan-500/30 space-y-2">
                    <div className="flex items-center justify-between text-xs font-mono text-cyan-400">
                      <span className="font-bold uppercase tracking-wider flex items-center gap-1.5">
                        <Volume2 className="w-3.5 h-3.5" />
                        Founder Spoken Defense (20–30s)
                      </span>
                      <span>Confident, Decisive Delivery</span>
                    </div>
                    <p className="text-xs sm:text-sm text-slate-100 font-sans leading-relaxed font-medium">
                      &ldquo;{item.founderAnswer}&rdquo;
                    </p>
                  </div>

                  {/* Technical Proof */}
                  <div className="space-y-3">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
                        <span className="text-[11px] font-mono text-purple-400 block font-bold">
                          ACTIVE DEFENSE STAGES
                        </span>
                        <div className="flex flex-wrap gap-1.5 mt-1">
                          {item.technicalProof.stages.map((st) => (
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
                          {item.technicalProof.metric}
                        </p>
                      </div>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 space-y-1">
                      <span className="text-[11px] font-mono text-cyan-400 block font-bold">
                        UNDERLYING ARCHITECTURAL MECHANISM
                      </span>
                      <p className="text-xs text-slate-300 font-sans leading-relaxed">
                        {item.technicalProof.mechanism}
                      </p>
                    </div>

                    <div className="p-3 rounded-xl bg-black/80 border border-slate-800 font-mono text-xs text-emerald-400 overflow-x-auto">
                      <span className="text-[10px] text-slate-500 block mb-1">
                        // Verified Code Logic & Contract:
                      </span>
                      <code>{item.technicalProof.contractOrCode}</code>
                    </div>
                  </div>

                  {/* Follow-up Counter Defense */}
                  <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-1.5">
                    <span className="text-[11px] font-mono text-slate-400 font-bold uppercase block">
                      Pre-Empting Hard Follow-Up Attack
                    </span>
                    <p className="text-xs sm:text-sm text-slate-200 font-sans leading-relaxed">
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
