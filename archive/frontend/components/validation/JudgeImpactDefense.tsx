"use client";

import React, { useState } from "react";
import {
  ShieldAlert,
  HelpCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  Calendar,
  Sparkles,
  Terminal,
} from "lucide-react";
import { JUDGE_IMPACT_DEFENSES } from "@/lib/stage-m-data";

export const JudgeImpactDefense: React.FC = () => {
  const [expandedId, setExpandedId] = useState<string>("defense-validation");

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? "" : id));
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-4 rounded-xl border border-red-500/30 bg-red-950/20 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-red-500/20 text-red-300 border border-red-500/40">
              ADVERSARIAL DEFENSE
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
              Honest Limitations &amp; Clinical Roadmap
            </span>
          </div>
          <h2 className="text-xl font-black text-white mt-1.5 flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-rose-400" />
            <span>Judge Impact &amp; Clinical Skepticism Defense</span>
          </h2>
        </div>

        <span className="text-xs font-mono text-slate-400">
          4 Core Adversarial Impact Inquiries
        </span>
      </div>

      {/* Accordion List of 4 Judge Defense Scenarios */}
      <div className="space-y-4">
        {JUDGE_IMPACT_DEFENSES.map((item, idx) => {
          const isExpanded = expandedId === item.id;
          return (
            <div
              key={item.id}
              className={`rounded-2xl border transition-all duration-200 overflow-hidden ${
                isExpanded
                  ? "border-cyan-500/50 bg-slate-950 shadow-[0_0_20px_rgba(0,242,254,0.1)]"
                  : "border-slate-800 bg-slate-950/60 hover:border-slate-700"
              }`}
            >
              {/* Header Accordion Bar */}
              <div
                onClick={() => toggleExpand(item.id)}
                className="p-5 flex items-center justify-between cursor-pointer select-none"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono font-bold text-slate-500">
                    0{idx + 1}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-mono font-bold text-white">
                      {item.question}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
                      {item.complianceBadge}
                    </span>
                  </div>
                </div>

                <button className="text-slate-400 hover:text-white transition-colors">
                  {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                </button>
              </div>

              {/* Expanded Defense Details */}
              {isExpanded && (
                <div className="px-5 pb-6 space-y-4 border-t border-slate-800/80 pt-4">
                  {/* 1. Founder Spoken Response */}
                  <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/20">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-cyan-300 mb-1.5">
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>FOUNDER DIRECT SPOKEN ANSWER:</span>
                    </div>
                    <p className="text-sm text-slate-200 leading-relaxed italic">
                      "{item.founderResponse}"
                    </p>
                  </div>

                  {/* 2. Technical Explanation & Code Verification */}
                  <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                    <div className="flex items-center gap-2 text-xs font-mono font-bold text-slate-300 mb-1.5">
                      <Terminal className="w-3.5 h-3.5 text-cyan-400" />
                      <span>TECHNICAL MECHANISM &amp; FORMULA:</span>
                    </div>
                    <p className="text-xs text-slate-300 font-mono leading-relaxed">
                      {item.technicalExplanation}
                    </p>
                  </div>

                  {/* Two Columns: Honest Limitation & Future Roadmap */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Honest Limitation */}
                    <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30">
                      <div className="flex items-center gap-2 text-xs font-mono font-bold text-rose-400 mb-1.5">
                        <AlertCircle className="w-3.5 h-3.5" />
                        <span>HONEST LIMITATION (ZERO PROTOTYPE HYPE):</span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        {item.honestLimitation}
                      </p>
                    </div>

                    {/* Future Validation Roadmap */}
                    <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30">
                      <div className="flex items-center gap-2 text-xs font-mono font-bold text-emerald-400 mb-1.5">
                        <Calendar className="w-3.5 h-3.5" />
                        <span>PROSPECTIVE VALIDATION ROADMAP:</span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed">
                        {item.futureValidationRoadmap}
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
