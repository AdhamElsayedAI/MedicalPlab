"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  HelpCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Terminal,
  Sparkles,
  Zap,
  Filter,
} from "lucide-react";
import { JUDGE_FINAL_DEFENSES, JudgeScenario } from "@/lib/grand-stage-data";

export const JudgeFinalDefense: React.FC = () => {
  const [selectedLevel, setSelectedLevel] = useState<string>("ALL");
  const [expandedId, setExpandedId] = useState<string>("defense-ai-wrapper");

  const levels = [
    "ALL",
    "LEVEL 2: AI Engineer",
    "LEVEL 3: Medical Expert",
    "LEVEL 4: Investor",
  ];

  const filteredScenarios =
    selectedLevel === "ALL"
      ? JUDGE_FINAL_DEFENSES
      : JUDGE_FINAL_DEFENSES.filter((s) => s.difficultyLevel === selectedLevel);

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-4 rounded-xl border border-red-500/30 bg-red-950/20 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/40">
              ADVERSARIAL DEFENSE ENGINE
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
              4 Difficulty Levels
            </span>
          </div>
          <h2 className="text-xl font-black text-white mt-1.5 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span>Judge Q&amp;A Counter-Attack &amp; Technical Proof System</span>
          </h2>
        </div>

        <span className="text-xs font-mono text-slate-400">
          Founder-Ready 30-Second Defenses
        </span>
      </div>

      {/* Level Filter Tabs */}
      <div className="flex flex-wrap items-center gap-2">
        {levels.map((lvl) => (
          <button
            key={lvl}
            onClick={() => setSelectedLevel(lvl)}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-mono font-bold transition-all border ${
              selectedLevel === lvl
                ? "bg-cyan-500 text-black border-cyan-400 shadow-[0_0_12px_rgba(0,242,254,0.35)]"
                : "bg-slate-900 text-slate-400 border-slate-800 hover:text-white hover:bg-slate-850"
            }`}
          >
            {lvl}
          </button>
        ))}
      </div>

      {/* Accordion Defense Scenarios */}
      <div className="space-y-4">
        {filteredScenarios.map((item, idx) => {
          const isExpanded = expandedId === item.id;
          return (
            <div
              key={item.id}
              className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
                isExpanded
                  ? "border-cyan-500/50 bg-slate-950 shadow-[0_0_25px_rgba(0,242,254,0.12)]"
                  : "border-slate-800 bg-slate-950/60 hover:border-slate-700"
              }`}
            >
              {/* Header Bar */}
              <div
                onClick={() => setExpandedId(isExpanded ? "" : item.id)}
                className="p-5 flex items-center justify-between cursor-pointer select-none"
              >
                <div className="flex flex-wrap items-center gap-3">
                  <span className="text-xs font-mono font-bold text-slate-500">
                    0{idx + 1}
                  </span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700 font-bold">
                    {item.difficultyLevel}
                  </span>
                  <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                    {item.category}
                  </span>
                  <h3 className="text-sm font-bold text-white font-mono ml-1">
                    "{item.question}"
                  </h3>
                </div>

                <button className="text-slate-400 hover:text-white transition-colors shrink-0 ml-2">
                  {isExpanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                </button>
              </div>

              {/* Expanded Body */}
              {isExpanded && (
                <div className="px-5 pb-6 space-y-4 border-t border-slate-800/80 pt-4">
                  {/* Hidden Judge Concern */}
                  <div className="p-3.5 rounded-xl bg-amber-950/20 border border-amber-500/30">
                    <span className="text-[10px] font-mono font-bold text-amber-400 uppercase tracking-widest block">
                      HIDDEN JUDGE CONCERN (WHAT THEY ARE REALLY SKEPTICAL ABOUT):
                    </span>
                    <p className="text-xs text-amber-200 mt-1 italic leading-relaxed">
                      "{item.hiddenConcern}"
                    </p>
                  </div>

                  {/* Founder 30-Second Answer */}
                  <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/30 space-y-1">
                    <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-cyan-300">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>FOUNDER SPOKEN DEFENSE (30 SECONDS):</span>
                    </div>
                    <p className="text-sm text-slate-200 leading-relaxed font-serif italic">
                      "{item.founderAnswer}"
                    </p>
                  </div>

                  {/* Technical Proof & Code Contract */}
                  <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 space-y-1">
                    <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-slate-300">
                      <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                      <span>TECHNICAL PROOF &amp; BENCHMARK CONTRACT:</span>
                    </div>
                    <p className="text-xs text-slate-300 font-mono leading-relaxed">
                      {item.technicalProof}
                    </p>
                  </div>

                  {/* Follow-up Defense */}
                  <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 space-y-1">
                    <div className="flex items-center gap-1.5 text-xs font-mono font-bold text-emerald-400">
                      <Zap className="w-3.5 h-3.5" />
                      <span>COUNTER-PUNCH (PRE-EMPTING THE HARD FOLLOW-UP ATTACK):</span>
                    </div>
                    <p className="text-xs text-emerald-200 leading-relaxed">
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
