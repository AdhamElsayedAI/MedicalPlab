"use client";

import React from "react";
import {
  Users,
  Activity,
  AlertTriangle,
  ShieldCheck,
  TrendingUp,
  FileCheck,
  Building2,
  BookOpen,
} from "lucide-react";

export const InstitutionAdminView: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 med-fade-in" aria-label="Clinical Faculty Analytics">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <div className="flex items-center gap-2.5 mb-1.5">
            <div
              className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0"
              style={{ background: "rgba(14,165,233,0.15)", border: "1px solid rgba(14,165,233,0.25)" }}
            >
              <Users className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-white tracking-tight" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}>
                Clinical Faculty &amp; Cohort Analytics
              </h1>
              <p className="text-xs text-slate-400 mt-0.5">
                Cohort diagnostic telemetry, curriculum compliance audit, and weak-topic heatmaps.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-semibold text-sky-300 flex items-center gap-1.5">
            <Building2 className="w-3.5 h-3.5" />
            NHS Imperial College Healthcare Trust
          </span>
        </div>
      </div>

      {/* 4 KPI Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="med-card p-5 space-y-1.5">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Trainees</div>
          <div className="text-2xl font-black font-mono text-white">48 Doctors</div>
          <span className="text-[11px] text-emerald-400 font-medium">42 Active in current revision diet</span>
        </div>

        <div className="med-card p-5 space-y-1.5">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Cohort Mean Accuracy</div>
          <div className="text-2xl font-black font-mono text-sky-300">76.8%</div>
          <span className="text-[11px] text-sky-400 font-medium">+4.2% Above UK National Benchmark</span>
        </div>

        <div className="med-card p-5 space-y-1.5">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Clinical Decision Speed</div>
          <div className="text-2xl font-black font-mono text-emerald-400">&lt;80ms</div>
          <span className="text-[11px] text-slate-400 font-medium">Real-time Socratic preceptor latency</span>
        </div>

        <div className="med-card p-5 space-y-1.5">
          <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Patient Safety Violations</div>
          <div className="text-2xl font-black font-mono text-purple-400">0 Reported</div>
          <span className="text-[11px] text-purple-300 font-medium">All contraindications caught in simulation</span>
        </div>
      </div>

      {/* Cohort Difficult Topics & Guideline Compliance Status */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Difficult Topics (Left 6 Cols) */}
        <div className="lg:col-span-6 med-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-xs font-bold text-amber-400 flex items-center gap-1.5 uppercase tracking-wider">
              <AlertTriangle className="w-4 h-4" />
              Cohort High-Difficulty Topics (&lt;60% Accuracy)
            </span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-white block text-[13px]">Cardiac Tamponade vs Tension Pneumothorax</span>
                <span className="text-[11px] text-slate-400">Confusion regarding JVP elevation with muffled heart sounds</span>
              </div>
              <span className="text-xs font-bold text-amber-400 px-2.5 py-1 rounded bg-amber-950/80 border border-amber-500/30">
                51.2% Acc
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-white block text-[13px]">Thrombolysis Absolute Contraindications</span>
                <span className="text-[11px] text-slate-400">Differentiation between ischemic and hemorrhagic intracranial events</span>
              </div>
              <span className="text-xs font-bold text-amber-400 px-2.5 py-1 rounded bg-amber-950/80 border border-amber-500/30">
                54.8% Acc
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="font-bold text-white block text-[13px]">Subarachnoid Haemorrhage LP Timing</span>
                <span className="text-[11px] text-slate-400">Xanthochromia window (&gt;12 hours post-headache) frequently misidentified</span>
              </div>
              <span className="text-xs font-bold text-amber-400 px-2.5 py-1 rounded bg-amber-950/80 border border-amber-500/30">
                58.0% Acc
              </span>
            </div>
          </div>
        </div>

        {/* Guideline Compliance Status (Right 6 Cols) */}
        <div className="lg:col-span-6 med-card p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <span className="text-xs font-bold text-sky-400 flex items-center gap-1.5 uppercase tracking-wider">
              <FileCheck className="w-4 h-4" />
              Verified Clinical Guidelines Ingested
            </span>
            <span className="text-[11px] font-bold text-emerald-400">100% AUDITED</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-white font-bold block text-[13px]">NICE Guideline NG185 (Acute Coronary Syndromes)</span>
                <span className="text-[11px] text-slate-400">Extractive Reperfusion Protocols &amp; PPCI Delivery Targets</span>
              </div>
              <span className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold">
                COMPLIANT
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-white font-bold block text-[13px]">NICE Guideline NG128 (Stroke &amp; TIA)</span>
                <span className="text-[11px] text-slate-400">Thrombolysis Windows &amp; Mechanical Thrombectomy Criteria</span>
              </div>
              <span className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold">
                COMPLIANT
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-white font-bold block text-[13px]">British National Formulary (BNF 85)</span>
                <span className="text-[11px] text-slate-400">Prescribing Dosages, Renal Adjustments &amp; Lethal Interactions</span>
              </div>
              <span className="px-2.5 py-1 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold">
                COMPLIANT
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
