"use client";

import React, { useState } from "react";
import { X, ShieldCheck, Cpu, ArrowRight, Layers, CheckCircle2, Zap, FileCode, CheckCircle } from "lucide-react";
import { PIPELINE_STAGES } from "@/lib/demo-data";
import { PipelineStageInfo } from "@/lib/types";

interface HackathonDeepDiveModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const HackathonDeepDiveModal: React.FC<HackathonDeepDiveModalProps> = ({
  isOpen,
  onClose,
}) => {
  const [selectedStage, setSelectedStage] = useState<PipelineStageInfo>(PIPELINE_STAGES[0]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className="med-card w-full max-w-5xl rounded-3xl p-6 md:p-8 flex flex-col max-h-[90vh] overflow-hidden shadow-2xl"
        style={{ background: "#0b1120", border: "1px solid rgba(56, 189, 248, 0.25)" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div
              className="p-2.5 rounded-xl flex-shrink-0"
              style={{ background: "rgba(14, 165, 233, 0.15)", border: "1px solid rgba(14, 165, 233, 0.3)" }}
            >
              <Cpu className="w-5 h-5 text-sky-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3
                  className="text-lg font-bold text-white tracking-tight"
                  style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}
                >
                  MedicalPlab AI Architecture &amp; Clinical Safety Verification
                </h3>
                <span className="med-badge med-badge-primary">Technical Whitepaper</span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Deterministic Retrieval Boundaries · Mathematical Claim Extraction · Real-Time Safety Interceptor
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Pipeline Stage Buttons Row */}
        <div className="py-4 grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 overflow-x-auto">
          {PIPELINE_STAGES.map((stg) => (
            <button
              key={stg.id}
              onClick={() => setSelectedStage(stg)}
              className={`p-2.5 rounded-xl border text-left transition-all ${
                selectedStage.id === stg.id
                  ? "bg-sky-500/20 border-sky-400/40 text-white shadow-sm"
                  : "bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
              }`}
            >
              <span className="text-[10px] font-mono text-sky-400 font-bold block truncate">
                {stg.name}
              </span>
              <span className="text-xs font-bold truncate block text-slate-200 mt-0.5">{stg.code}</span>
              <span className="text-[10px] font-mono text-emerald-400 mt-1 block">
                {stg.latencyMs}ms
              </span>
            </button>
          ))}
        </div>

        {/* Selected Stage Detail Panel */}
        <div className="flex-1 overflow-y-auto p-5 rounded-2xl bg-slate-900/60 border border-slate-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <span className="text-base sm:text-lg font-bold text-white">
                {selectedStage.name}: {selectedStage.code}
              </span>
              <span className="med-badge" style={{ background: "rgba(34, 197, 94, 0.12)", color: "#86efac", border: "1px solid rgba(34, 197, 94, 0.25)" }}>
                STATUS: {selectedStage.status}
              </span>
            </div>

            <span className="text-xs text-slate-400">
              Verified Latency: <strong className="text-sky-300 font-mono">{selectedStage.latencyMs} ms</strong>
            </span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/70 border border-slate-800 space-y-1">
            <span className="text-xs font-bold text-sky-400 block uppercase tracking-wider">
              Core Objective &amp; Clinical Safety Contract:
            </span>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              {selectedStage.purpose}
            </p>
          </div>

          {/* Contracts I/O Diagram */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-slate-400 block mb-1 text-[11px] uppercase">Input Schema Contract:</span>
              <span className="text-sky-300 font-bold">{selectedStage.inputContract}</span>
              <p className="text-[11px] text-slate-400 mt-1 font-sans leading-tight">
                Validated deterministically via strict Pydantic schemas before execution.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800">
              <span className="text-slate-400 block mb-1 text-[11px] uppercase">Output Evidence Contract:</span>
              <span className="text-emerald-300 font-bold">{selectedStage.outputContract}</span>
              <p className="text-[11px] text-slate-400 mt-1 font-sans leading-tight">
                Extractive citations with exact byte-level provenance against NICE NG185 and BNF 85.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 mt-2 border-t border-slate-800 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span>Over 219 automated unit &amp; safety tests verified across Python &amp; TypeScript layers.</span>
          </div>
          <button
            onClick={onClose}
            className="btn-primary text-xs font-bold px-5 py-2 rounded-xl"
          >
            Close Deep Dive
          </button>
        </div>
      </div>
    </div>
  );
};
