"use client";

import React, { useState } from "react";
import {
  BookOpen,
  Quote,
  TrendingUp,
  CheckCircle2,
  HeartPulse,
  Building2,
  Users,
  Award,
  ArrowRight,
} from "lucide-react";
import { IMPACT_TIMELINE, ImpactStory } from "@/lib/grand-stage-data";

export const MedicalImpactTimeline: React.FC = () => {
  const [selectedIdx, setSelectedIdx] = useState<number>(0);
  const currentItem: ImpactStory = IMPACT_TIMELINE[selectedIdx];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-4 rounded-xl border border-cyan-500/30 bg-cyan-950/20 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
              CLINICAL IMPACT CHRONICLES
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              Human &amp; Economic Storytelling
            </span>
          </div>
          <h2 className="text-xl font-black text-white mt-1.5 flex items-center gap-2">
            <HeartPulse className="w-5 h-5 text-rose-400" />
            <span>The Transformation of a Junior Doctor &amp; NHS Hospital Trust</span>
          </h2>
        </div>

        <span className="text-xs font-mono text-slate-400">
          4-Stage Longitudinal Impact Arc
        </span>
      </div>

      {/* 4-Step Timeline Progression Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {IMPACT_TIMELINE.map((item, idx) => {
          const isSelected = selectedIdx === idx;
          return (
            <div
              key={item.id}
              onClick={() => setSelectedIdx(idx)}
              className={`p-4 rounded-xl border cursor-pointer transition-all ${
                isSelected
                  ? "bg-slate-900 border-cyan-400 shadow-[0_0_20px_rgba(0,242,254,0.2)] ring-1 ring-cyan-400/50"
                  : "bg-slate-950/60 border-slate-800 hover:border-slate-700 opacity-80 hover:opacity-100"
              }`}
            >
              <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 mb-1">
                <span>PHASE 0{idx + 1}</span>
                <span className="text-cyan-400 font-bold">{item.phase.split(" ")[0]}</span>
              </div>
              <h4 className="text-xs font-bold text-white truncate">{item.phase}</h4>
              <p className="text-[11px] text-slate-400 mt-1 truncate">{item.title}</p>
            </div>
          );
        })}
      </div>

      {/* Main Narrative Focus Canvas */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-950/90 relative overflow-hidden space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-widest block">
              {currentItem.phase}
            </span>
            <h3 className="text-2xl font-black text-white mt-1">{currentItem.title}</h3>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Subject: <strong className="text-slate-200">{currentItem.protagonist}</strong>
            </p>
          </div>

          <div className="p-2.5 px-3.5 rounded-xl bg-slate-900 border border-slate-800 text-center">
            <span className="text-[10px] font-mono text-slate-500 uppercase block">Audited Metric</span>
            <span className="text-sm font-bold font-mono text-emerald-400 mt-0.5 block">
              {currentItem.clinicalMetric}
            </span>
          </div>
        </div>

        {/* Cinematic Spoken Quote */}
        <div className="p-5 rounded-2xl bg-cyan-950/20 border border-cyan-500/20 relative">
          <Quote className="w-8 h-8 text-cyan-500/20 absolute top-3 right-4" />
          <p className="text-base sm:text-lg text-cyan-200 italic font-serif leading-relaxed">
            "{currentItem.quote}"
          </p>
        </div>

        {/* Narrative Paragraph */}
        <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800">
          <span className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider block mb-2">
            Clinical Longitudinal Analysis:
          </span>
          <p className="text-sm text-slate-300 leading-relaxed">
            {currentItem.narrative}
          </p>
        </div>

        {/* Timeline Stepper Controls */}
        <div className="pt-2 flex items-center justify-between">
          <button
            disabled={selectedIdx === 0}
            onClick={() => setSelectedIdx((prev) => Math.max(0, prev - 1))}
            className="px-4 py-2 rounded-xl text-xs font-mono font-bold border border-slate-800 bg-slate-900 text-slate-300 disabled:opacity-30 transition-all"
          >
            Previous Phase
          </button>

          <button
            disabled={selectedIdx === IMPACT_TIMELINE.length - 1}
            onClick={() => setSelectedIdx((prev) => Math.min(IMPACT_TIMELINE.length - 1, prev + 1))}
            className="flex items-center gap-2 px-5 py-2 rounded-xl text-xs font-mono font-bold bg-cyan-500 text-black shadow-[0_0_15px_rgba(0,242,254,0.35)] disabled:opacity-30 transition-all"
          >
            <span>Next Phase</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
};
