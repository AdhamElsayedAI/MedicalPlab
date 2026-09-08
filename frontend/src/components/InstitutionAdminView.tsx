"use client";

import React from "react";
import {
  Users,
  Activity,
  AlertTriangle,
  Cpu,
  ShieldCheck,
  DollarSign,
  TrendingUp,
  FileCheck,
} from "lucide-react";

export const InstitutionAdminView: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg bg-indigo-950 text-indigo-400 border border-indigo-500/40">
              <Users className="w-4 h-4" />
            </span>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-wide">
              INSTITUTIONAL COHORT & TELEMETRY DASHBOARD
            </h2>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            STAGE-G PRODUCT PLATFORM // MULTI-TENANT ISOLATION // AI USAGE & COST AUDIT
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs font-mono text-cyan-300">
            TENANT: NHS Imperial College Trust
          </span>
        </div>
      </div>

      {/* 4 KPI Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="cyber-card rounded-2xl p-4 border border-cyan-500/20 bg-slate-950/85">
          <div className="text-[11px] font-mono text-slate-400 mb-1">TOTAL TRAINEES</div>
          <div className="text-2xl font-black font-mono text-white">48 Students</div>
          <span className="text-[10px] font-mono text-emerald-400">42 Active this week</span>
        </div>

        <div className="cyber-card rounded-2xl p-4 border border-cyan-500/20 bg-slate-950/85">
          <div className="text-[11px] font-mono text-slate-400 mb-1">COHORT MEAN ACCURACY</div>
          <div className="text-2xl font-black font-mono text-cyan-300">76.8%</div>
          <span className="text-[10px] font-mono text-cyan-400">Above UK National Benchmark</span>
        </div>

        <div className="cyber-card rounded-2xl p-4 border border-cyan-500/20 bg-slate-950/85">
          <div className="text-[11px] font-mono text-slate-400 mb-1">AI INFERENCE LATENCY</div>
          <div className="text-2xl font-black font-mono text-emerald-400">62.4ms</div>
          <span className="text-[10px] font-mono text-slate-400">Stage-F Orchestrated</span>
        </div>

        <div className="cyber-card rounded-2xl p-4 border border-cyan-500/20 bg-slate-950/85">
          <div className="text-[11px] font-mono text-slate-400 mb-1">AI CLOUD COST (MTD)</div>
          <div className="text-2xl font-black font-mono text-purple-400">$0.048 USD</div>
          <span className="text-[10px] font-mono text-purple-300">12,400 Tokens Processed</span>
        </div>
      </div>

      {/* Cohort Difficult Topics & Guideline Ingestion Status */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Difficult Topics (Left 6 Cols) */}
        <div className="lg:col-span-6 cyber-card rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/85 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <span className="text-xs font-mono text-amber-400 font-bold flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4" />
              COHORT HIGH-DIFFICULTY TOPICS (&lt;60% ACCURACY)
            </span>
          </div>

          <div className="space-y-3">
            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-white block">Cardiac Tamponade vs Tension Pneumothorax</span>
                <span className="text-[11px] font-mono text-slate-400">Missed in 42% of mock simulation attempts</span>
              </div>
              <span className="text-xs font-mono font-bold text-amber-400 px-2.5 py-1 rounded bg-amber-950/80 border border-amber-500/30">
                51.2% Acc
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-white block">Thrombolysis Absolute Contraindications</span>
                <span className="text-[11px] font-mono text-slate-400">Confusion regarding ischemic vs hemorrhagic stroke</span>
              </div>
              <span className="text-xs font-mono font-bold text-amber-400 px-2.5 py-1 rounded bg-amber-950/80 border border-amber-500/30">
                54.8% Acc
              </span>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-bold text-white block">Subarachnoid Haemorrhage LP Timing</span>
                <span className="text-[11px] font-mono text-slate-400">Xanthochromia window (&gt;12h) often neglected</span>
              </div>
              <span className="text-xs font-mono font-bold text-amber-400 px-2.5 py-1 rounded bg-amber-950/80 border border-amber-500/30">
                58.0% Acc
              </span>
            </div>
          </div>
        </div>

        {/* Ingestion & Compliance Audit (Right 6 Cols) */}
        <div className="lg:col-span-6 cyber-card rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/85 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <span className="text-xs font-mono text-cyan-400 font-bold flex items-center gap-1.5">
              <FileCheck className="w-4 h-4" />
              KNOWLEDGE INGESTION PIPELINE (STAGE-G)
            </span>
            <span className="text-[10px] font-mono text-emerald-400">100% ONLINE</span>
          </div>

          <div className="space-y-3 text-xs font-mono">
            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-white font-bold block">NICE Guideline NG185 (ACS)</span>
                <span className="text-[11px] text-slate-400">2,450 KB // 142 Extracted Evidence Blocks</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold">
                AVAILABLE
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-white font-bold block">NICE Guideline NG128 (Stroke)</span>
                <span className="text-[11px] text-slate-400">1,820 KB // 98 Extracted Evidence Blocks</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold">
                AVAILABLE
              </span>
            </div>

            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-white font-bold block">British National Formulary (BNF 85)</span>
                <span className="text-[11px] text-slate-400">4,100 KB // Drug Dosages & Contraindications</span>
              </div>
              <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/40 text-[10px] font-bold">
                AVAILABLE
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
