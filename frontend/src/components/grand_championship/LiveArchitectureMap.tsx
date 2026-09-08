"use client";

import React, { useState } from "react";
import {
  Layers,
  Sparkles,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Terminal,
  ArrowRight,
  ChevronDown,
  Info,
  Database,
  Cpu,
} from "lucide-react";
import { ARCHITECTURE_STAGES, ArchitectureStage } from "@/lib/grand-stage-data";

export const LiveArchitectureMap: React.FC = () => {
  const [selectedStageId, setSelectedStageId] = useState<string>("stage-b");

  const activeStage =
    ARCHITECTURE_STAGES.find((s) => s.id === selectedStageId) || ARCHITECTURE_STAGES[1];

  return (
    <div className="space-y-6">
      {/* Top Header Banner */}
      <div className="p-4 rounded-xl border border-cyan-500/30 bg-cyan-950/20 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
              TECHNICAL JUDGE DEEP DIVE
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              Sub-50ms Frozen Python Core
            </span>
          </div>
          <h2 className="text-xl font-black text-white mt-1.5 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-cyan-400" />
            <span>End-to-End Live Architecture Data Flow</span>
          </h2>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span>235 Tests Passing in 0.06s</span>
        </div>
      </div>

      {/* Interactive Horizontal Pipeline Visualizer */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-950/90 relative overflow-hidden">
        <div className="text-xs font-mono font-bold text-slate-400 uppercase tracking-wider mb-4 flex items-center justify-between">
          <span>Clinical Question Pipeline Execution Graph</span>
          <span className="text-cyan-400">Deterministic Flow: USER $\rightarrow$ R $\rightarrow$ B $\rightarrow$ C $\rightarrow$ D $\rightarrow$ E $\rightarrow$ F $\rightarrow$ VERIFIED ANSWER</span>
        </div>

        {/* The Pipeline Strip */}
        <div className="flex items-center justify-between gap-2 overflow-x-auto pb-4 pt-2">
          {/* Step 0: User Query */}
          <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-900 text-center shrink-0 w-32">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Trigger</span>
            <span className="text-xs font-bold text-white mt-1 block">Clinical Query</span>
            <span className="text-[9px] font-mono text-cyan-400 mt-1 block">Candidate Input</span>
          </div>

          <ArrowRight className="w-4 h-4 text-cyan-400 shrink-0 animate-pulse" />

          {/* 6 Frozen Core Stages */}
          {ARCHITECTURE_STAGES.map((stage) => {
            const isSelected = selectedStageId === stage.id;
            return (
              <React.Fragment key={stage.id}>
                <div
                  onClick={() => setSelectedStageId(stage.id)}
                  className={`p-3.5 rounded-xl border cursor-pointer text-center shrink-0 w-36 transition-all ${
                    isSelected
                      ? "bg-cyan-950/40 border-cyan-400 shadow-[0_0_20px_rgba(0,242,254,0.3)] ring-1 ring-cyan-400/80 scale-105"
                      : "bg-slate-950/80 border-slate-800 hover:border-slate-700 hover:bg-slate-900"
                  }`}
                >
                  <div className="flex items-center justify-between text-[10px] font-mono mb-1">
                    <span className="text-cyan-400 font-bold">{stage.code}</span>
                    <span className="text-emerald-400">{stage.latency}</span>
                  </div>
                  <span className="text-xs font-bold text-white block truncate">{stage.name.replace(" Engine", "").replace(" Intelligence", "")}</span>
                  <span className="text-[9px] font-mono text-slate-400 mt-1 block truncate">
                    {stage.verifiedMetric.split(" ")[0]} {stage.verifiedMetric.split(" ")[1]}
                  </span>
                </div>

                <ArrowRight className="w-3.5 h-3.5 text-slate-600 shrink-0" />
              </React.Fragment>
            );
          })}

          {/* Final Step: Verified Safe Response */}
          <div className="p-3.5 rounded-xl border border-emerald-500/40 bg-emerald-950/30 text-center shrink-0 w-36">
            <span className="text-[10px] font-mono text-emerald-400 uppercase block font-bold">Output</span>
            <span className="text-xs font-bold text-emerald-200 mt-1 block">Verified Answer</span>
            <span className="text-[9px] font-mono text-emerald-400 mt-1 block">100% Grounded</span>
          </div>
        </div>
      </div>

      {/* Stage Detail Card for Selected Stage */}
      <div className="p-6 rounded-2xl border border-cyan-500/40 bg-slate-950/80 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold px-2.5 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                {activeStage.code}
              </span>
              <span className="text-xs font-mono text-emerald-400 font-bold">
                {activeStage.status} IN TEST SUITE
              </span>
            </div>
            <h3 className="text-xl font-black text-white mt-1.5">{activeStage.name}</h3>
            <p className="text-xs text-slate-400 mt-0.5">{activeStage.role}</p>
          </div>

          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-center">
              <span className="text-[10px] font-mono text-slate-400 block uppercase">Runtime Latency</span>
              <span className="text-base font-bold font-mono text-cyan-400">{activeStage.latency}</span>
            </div>
            <div className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-center">
              <span className="text-[10px] font-mono text-slate-400 block uppercase">Audited Metric</span>
              <span className="text-base font-bold font-mono text-emerald-400">{activeStage.verifiedMetric}</span>
            </div>
          </div>
        </div>

        {/* 4 Dimension Specs */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs font-mono">
          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
            <span className="text-slate-500 uppercase block font-bold">Underlying Algorithm:</span>
            <p className="text-slate-200">{activeStage.algorithm}</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
            <span className="text-slate-500 uppercase block font-bold">Pipeline Inputs:</span>
            <p className="text-cyan-300">{activeStage.inputs}</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
            <span className="text-slate-500 uppercase block font-bold">Pipeline Outputs:</span>
            <p className="text-emerald-300">{activeStage.outputs}</p>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-900/70 border border-slate-800 space-y-1">
            <span className="text-slate-500 uppercase block font-bold">Source Code Contract:</span>
            <p className="text-amber-300 truncate">{activeStage.codeContract}</p>
          </div>
        </div>
      </div>
    </div>
  );
};
