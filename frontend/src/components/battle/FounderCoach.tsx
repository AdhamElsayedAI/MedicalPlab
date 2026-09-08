"use client";

import React, { useState } from "react";
import {
  BrainCircuit,
  CheckCircle2,
  AlertCircle,
  Clock,
  DollarSign,
  Cpu,
  Sparkles,
  Lightbulb,
} from "lucide-react";
import { FOUNDER_COACH_AUDITS } from "@/lib/stage-l-data";

export const FounderCoach: React.FC = () => {
  const [audits, setAudits] = useState(FOUNDER_COACH_AUDITS);

  const getAreaIcon = (area: string) => {
    switch (area) {
      case "Pitch Weakness":
        return <AlertCircle className="w-4 h-4 text-rose-400" />;
      case "Timing Bottleneck":
        return <Clock className="w-4 h-4 text-amber-400" />;
      case "Business Proof":
        return <DollarSign className="w-4 h-4 text-emerald-400" />;
      case "Technical Balance":
        return <Cpu className="w-4 h-4 text-cyan-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <BrainCircuit className="w-3.5 h-3.5 text-cyan-400" />
              FOUNDER STRATEGY & PITCH COACH
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              4 CORE STRATEGIC AUDITS
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Automated Pitch Weakness & Timing Analysis
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Pre-empting presentation pitfalls: identifying timing bottlenecks, balancing technical jargon, and anchoring business proof points.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-center">
          <div className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs font-mono text-emerald-400 font-bold flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4" />
            <span>All 4 Weaknesses Addressed</span>
          </div>
        </div>
      </div>

      {/* 4 Audit Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {audits.map((item, idx) => (
          <div
            key={idx}
            className="p-6 rounded-3xl bg-slate-950/85 border border-slate-800 space-y-4 hover:border-cyan-500/40 transition-colors shadow-lg"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 font-mono text-xs font-bold text-white">
                {getAreaIcon(item.area)}
                <span>{item.area.toUpperCase()}</span>
              </div>

              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40">
                ✓ {item.status}
              </span>
            </div>

            {/* Observation */}
            <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
              <span className="text-[10px] font-mono text-slate-400 uppercase font-bold block">
                Common Founder Pitfall
              </span>
              <p className="text-xs text-slate-300 font-sans leading-relaxed">
                {item.observation}
              </p>
            </div>

            {/* Strategic Coaching Advice */}
            <div className="p-3.5 rounded-2xl bg-cyan-950/20 border border-cyan-500/30 space-y-1">
              <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold block flex items-center gap-1">
                <Lightbulb className="w-3.5 h-3.5 text-cyan-300" /> Tactical Counter-Measure
              </span>
              <p className="text-xs sm:text-sm text-cyan-100 font-sans leading-relaxed font-medium">
                {item.coachingAdvice}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
