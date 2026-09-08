"use client";

import React from "react";
import {
  TrendingUp,
  XCircle,
  CheckCircle2,
  ArrowRight,
  Sparkles,
  Zap,
  Activity,
  ShieldCheck,
  Building2,
  Award,
} from "lucide-react";
import { IMPACT_STORY_DIMENSIONS } from "@/lib/championship-data";

export const ImpactStoryView: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-cyan-400" />
              THE IMPACT STORY: BEFORE VS AFTER TRANSFORMATION
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              PROVEN RESULTS
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Transforming Medical Education from Guesswork to Precision
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            A direct contrast between outdated static learning and MedicalPlab's evidence-grounded clinical intelligence operating system.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start md:self-center">
          <div className="px-4 py-2 rounded-xl bg-slate-900 border border-emerald-500/30 text-right">
            <span className="text-[10px] font-mono text-slate-400 block">PASS RATE DELTA</span>
            <span className="text-sm font-mono font-bold text-emerald-400">+34.2% Examination Lift</span>
          </div>
        </div>
      </div>

      {/* 5 Transformation Cards */}
      <div className="space-y-6">
        {IMPACT_STORY_DIMENSIONS.map((dim, idx) => (
          <div
            key={idx}
            className="rounded-3xl border border-slate-800 bg-slate-950/80 p-6 sm:p-7 space-y-5 hover:border-cyan-500/40 transition-colors shadow-lg"
          >
            {/* Dimension Title & Delta Impact Badge */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-lg bg-cyan-950 border border-cyan-400/40 text-cyan-300 text-xs font-mono font-bold flex items-center justify-center">
                  {idx + 1}
                </span>
                <h4 className="text-base font-bold text-white tracking-wide">
                  {dim.dimension}
                </h4>
              </div>

              <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40 self-start sm:self-center shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                ⚡ {dim.deltaImpact}
              </span>
            </div>

            {/* Before vs After Side-by-Side Comparison */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-center">
              {/* Left: Traditional Way (Red/Dark) */}
              <div className="lg:col-span-5 p-5 rounded-2xl bg-rose-950/15 border border-rose-500/25 space-y-2">
                <div className="flex items-center gap-2 text-rose-400 font-mono text-xs font-bold">
                  <XCircle className="w-4 h-4" />
                  <span>TRADITIONAL METHOD (STATUS QUO)</span>
                </div>
                <h5 className="font-bold text-slate-200 text-sm">
                  {dim.traditionalWay.title}
                </h5>
                <p className="text-xs text-slate-400 font-sans leading-relaxed">
                  {dim.traditionalWay.description}
                </p>
                <div className="pt-2 border-t border-rose-900/40 text-[11px] font-sans text-rose-300/80">
                  <span className="font-bold text-rose-300">Failure Mode:</span> {dim.traditionalWay.painPoint}
                </div>
              </div>

              {/* Middle Arrow */}
              <div className="lg:col-span-2 flex justify-center py-2 lg:py-0">
                <div className="w-10 h-10 rounded-full bg-slate-900 border border-cyan-500/40 flex items-center justify-center text-cyan-400 shadow-[0_0_15px_rgba(0,242,254,0.3)]">
                  <ArrowRight className="w-5 h-5" />
                </div>
              </div>

              {/* Right: MedicalPlab Way (Cyan/Emerald) */}
              <div className="lg:col-span-5 p-5 rounded-2xl bg-cyan-950/25 border border-cyan-500/40 space-y-2 shadow-[0_0_20px_rgba(0,242,254,0.08)]">
                <div className="flex items-center gap-2 text-cyan-400 font-mono text-xs font-bold">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>MEDICALPLAB INTELLIGENT SYSTEM</span>
                </div>
                <h5 className="font-bold text-white text-sm">
                  {dim.medicalPlabWay.title}
                </h5>
                <p className="text-xs text-slate-200 font-sans leading-relaxed">
                  {dim.medicalPlabWay.description}
                </p>
                <div className="pt-2 border-t border-cyan-900/40 text-[11px] font-sans text-emerald-300">
                  <span className="font-bold text-white">Clinical Advantage:</span> {dim.medicalPlabWay.clinicalAdvantage}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
