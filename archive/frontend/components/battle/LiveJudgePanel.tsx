"use client";

import React, { useState } from "react";
import {
  Award,
  Stethoscope,
  Cpu,
  TrendingUp,
  Star,
  CheckCircle2,
  Sparkles,
  ShieldCheck,
  Building2,
  Quote,
} from "lucide-react";
import { SIMULATED_JUDGES } from "@/lib/stage-l-data";

export const LiveJudgePanel: React.FC = () => {
  const [activeJudgeId, setActiveJudgeId] = useState(SIMULATED_JUDGES[0].id);

  const activeJudge =
    SIMULATED_JUDGES.find((j) => j.id === activeJudgeId) || SIMULATED_JUDGES[0];

  const overallAggregateScore = 98.5;

  const getJudgeIcon = (role: string) => {
    switch (role) {
      case "Medical Judge":
        return <Stethoscope className="w-5 h-5 text-emerald-400" />;
      case "AI Systems Judge":
        return <Cpu className="w-5 h-5 text-cyan-400" />;
      case "Investor Judge":
        return <TrendingUp className="w-5 h-5 text-purple-400" />;
    }
  };

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <Award className="w-3.5 h-3.5 text-cyan-400" />
              LIVE SIMULATED JUDGE PANEL
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              3 EXPERT PERSPECTIVES
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Simulated Hackathon Evaluation Panel (98.5 / 100)
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Independent evaluation rubrics and qualitative feedback from simulated NHS Medical Director, AI Systems Scientist, and HealthTech General Partner.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start md:self-center">
          <div className="px-5 py-2.5 rounded-2xl bg-gradient-to-br from-amber-500/20 via-cyan-500/20 to-purple-500/20 border border-amber-500/50 text-right shadow-[0_0_20px_rgba(245,158,11,0.25)]">
            <span className="text-[10px] font-mono text-slate-400 block">AGGREGATE PANEL SCORE</span>
            <span className="text-2xl font-black text-amber-300 font-mono">
              {overallAggregateScore} / 100
            </span>
          </div>
        </div>
      </div>

      {/* 3 Judge Selector Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {SIMULATED_JUDGES.map((judge) => {
          const isActive = judge.id === activeJudgeId;
          return (
            <button
              key={judge.id}
              onClick={() => setActiveJudgeId(judge.id)}
              className={`text-left p-6 rounded-3xl border transition-all duration-300 relative space-y-3 ${
                isActive
                  ? "bg-slate-950/95 border-cyan-400 shadow-[0_0_30px_rgba(0,242,254,0.2)]"
                  : "bg-slate-950/70 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-10 h-10 rounded-2xl bg-slate-900 border border-slate-700 flex items-center justify-center">
                    {getJudgeIcon(judge.role)}
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase block">
                      {judge.role}
                    </span>
                    <h4 className="font-bold text-white text-sm">{judge.name}</h4>
                  </div>
                </div>

                <span className="text-xl font-black text-amber-400 font-mono">
                  {judge.score}
                </span>
              </div>

              <p className="text-xs text-slate-400 font-sans leading-tight">
                {judge.title}
              </p>

              <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px] font-mono">
                <span className="text-emerald-400 font-bold">{judge.verdict}</span>
                <span className="text-slate-500">View Evaluation $\rightarrow$</span>
              </div>
            </button>
          );
        })}
      </div>

      {/* Active Judge Deep Evaluation View */}
      <div className="p-6 sm:p-8 rounded-3xl bg-slate-950/90 border border-cyan-500/20 shadow-lg space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div className="space-y-1">
            <span className="text-[10px] font-mono uppercase text-cyan-400 font-bold block">
              DETAILED EVALUATION — {activeJudge.role.toUpperCase()}
            </span>
            <h3 className="text-xl sm:text-2xl font-black text-white">
              {activeJudge.name}
            </h3>
            <p className="text-xs text-slate-400 font-sans">
              Focus Area: {activeJudge.focusArea}
            </p>
          </div>

          <div className="px-4 py-2 rounded-2xl bg-slate-900 border border-slate-700 text-right font-mono">
            <span className="text-[10px] text-slate-400 block">JUDGE VERDICT</span>
            <span className="text-base font-bold text-emerald-400">
              {activeJudge.verdict}
            </span>
          </div>
        </div>

        {/* Written Critique Quote */}
        <div className="p-5 rounded-2xl bg-cyan-950/20 border border-cyan-500/30 space-y-2 relative">
          <Quote className="w-8 h-8 text-cyan-500/30 absolute right-4 top-4 pointer-events-none" />
          <span className="text-xs font-mono text-cyan-300 font-bold uppercase block">
            Qualitative Panel Remarks:
          </span>
          <p className="text-xs sm:text-sm text-slate-200 font-sans leading-relaxed italic">
            &ldquo;{activeJudge.critiqueQuote}&rdquo;
          </p>
          <div className="pt-2 border-t border-cyan-900/40 text-xs font-sans text-emerald-300 flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            <span><strong>Standout Praise:</strong> {activeJudge.standoutPraise}</span>
          </div>
        </div>

        {/* Category Scoring Breakdown */}
        <div className="space-y-3">
          <h4 className="text-xs font-mono text-slate-400 uppercase tracking-wider font-bold">
            Scored Rubric Dimensions
          </h4>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {activeJudge.criteriaScores.map((crit, idx) => (
              <div
                key={idx}
                className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1.5"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white font-mono">
                    {crit.category}
                  </span>
                  <span className="text-sm font-black text-amber-400 font-mono">
                    {crit.score} / 100
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 font-sans leading-relaxed">
                  {crit.feedback}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
