"use client";

import React, { useState } from "react";
import {
  BookOpen,
  UserCheck,
  ShieldCheck,
  Building2,
  Quote,
  ArrowRight,
  CheckCircle2,
  HeartPulse,
} from "lucide-react";
import { IMPACT_STORIES } from "@/lib/stage-m-data";

export const ImpactStoryMode: React.FC = () => {
  const [selectedStoryIdx, setSelectedStoryIdx] = useState(0);
  const currentStory = IMPACT_STORIES[selectedStoryIdx];

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="p-4 rounded-xl border border-cyan-500/30 bg-cyan-950/20 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
              CLINICAL IMPACT STORIES
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
              {currentStory.complianceBadge}
            </span>
          </div>
          <h2 className="text-xl font-black text-white mt-1.5 flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-cyan-400" />
            <span>Human &amp; Institutional Transformation Chronicles</span>
          </h2>
        </div>

        {/* Story Selector Pills */}
        <div className="flex items-center gap-2 bg-slate-900/90 p-1.5 rounded-xl border border-slate-800">
          {IMPACT_STORIES.map((s, idx) => (
            <button
              key={s.id}
              onClick={() => setSelectedStoryIdx(idx)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                selectedStoryIdx === idx
                  ? "bg-cyan-500 text-black shadow-[0_0_12px_rgba(0,242,254,0.4)]"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              {s.dimension}
            </button>
          ))}
        </div>
      </div>

      {/* Main Cinematic Story View */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-950/80 relative overflow-hidden">
        {/* Dimension & Protagonist Header */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
          <div>
            <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-widest block">
              {currentStory.dimension}
            </span>
            <h3 className="text-2xl font-black text-white mt-1">
              {currentStory.title}
            </h3>
            <p className="text-xs text-slate-400 mt-1 font-mono">
              Protagonist: <strong className="text-slate-200">{currentStory.protagonist}</strong>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-900 text-slate-300 border border-slate-800">
              {currentStory.clinicalContext}
            </span>
          </div>
        </div>

        {/* Hero Spoken Quote */}
        <div className="my-6 p-5 rounded-2xl bg-cyan-950/20 border border-cyan-500/20 relative">
          <Quote className="w-8 h-8 text-cyan-500/20 absolute top-3 right-4" />
          <p className="text-base sm:text-lg text-cyan-200 italic font-serif leading-relaxed">
            "{currentStory.heroQuote}"
          </p>
        </div>

        {/* 3-Column Narrative: Problem -> Intervention -> Outcome */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* 1. The Crisis Problem */}
          <div className="p-5 rounded-xl border border-rose-500/20 bg-rose-950/10 space-y-2">
            <span className="text-xs font-mono font-bold text-rose-400 uppercase tracking-wider block">
              1. The Clinical / Career Crisis
            </span>
            <p className="text-xs text-slate-300 leading-relaxed">
              {currentStory.crisisProblem}
            </p>
          </div>

          {/* 2. MedicalPlab Intervention */}
          <div className="p-5 rounded-xl border border-cyan-500/20 bg-cyan-950/10 space-y-2">
            <span className="text-xs font-mono font-bold text-cyan-400 uppercase tracking-wider block">
              2. MedicalPlab AI Intervention
            </span>
            <p className="text-xs text-slate-300 leading-relaxed">
              {currentStory.medicalPlabIntervention}
            </p>
          </div>

          {/* 3. Expected Outcome */}
          <div className="p-5 rounded-xl border border-emerald-500/20 bg-emerald-950/10 space-y-2">
            <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider block">
              3. Measurable Outcome Achieved
            </span>
            <p className="text-xs text-slate-300 leading-relaxed">
              {currentStory.expectedOutcome}
            </p>
          </div>
        </div>

        {/* Outcome Stats Footer */}
        <div className="mt-6 pt-4 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4">
            {currentStory.outcomeStats.map((stat, idx) => (
              <div key={idx} className="p-3 rounded-xl bg-slate-900 border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-400 uppercase block">{stat.label}</span>
                <span className="text-sm font-bold font-mono text-emerald-400 mt-0.5 block">{stat.value}</span>
              </div>
            ))}
          </div>

          {/* Story Navigation Controls */}
          <div className="flex items-center gap-2">
            <button
              disabled={selectedStoryIdx === 0}
              onClick={() => setSelectedStoryIdx((prev) => Math.max(0, prev - 1))}
              className="px-3 py-1.5 rounded-lg text-xs font-mono font-bold border border-slate-700 bg-slate-900 text-slate-300 disabled:opacity-30 transition-all"
            >
              Previous Story
            </button>
            <button
              disabled={selectedStoryIdx === IMPACT_STORIES.length - 1}
              onClick={() => setSelectedStoryIdx((prev) => Math.min(IMPACT_STORIES.length - 1, prev + 1))}
              className="px-4 py-1.5 rounded-lg text-xs font-mono font-bold bg-cyan-500 text-black shadow-[0_0_12px_rgba(0,242,254,0.3)] disabled:opacity-30 transition-all"
            >
              Next Story
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
