"use client";

import React, { useState } from "react";
import { X, ShieldCheck, Cpu, ArrowRight, Layers, CheckCircle2, Zap } from "lucide-react";
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-xl animate-in fade-in duration-200">
      <div className="cyber-card w-full max-w-5xl rounded-3xl p-6 border border-cyan-400/40 bg-slate-950/95 shadow-[0_0_60px_rgba(0,242,254,0.3)] flex flex-col max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-cyan-500/20">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-cyan-950 text-cyan-400 border border-cyan-500/40">
              <Cpu className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-black text-white">
                  MEDICALPLAB FULL ARCHITECTURE PIPELINE
                </h3>
                <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950 text-emerald-400 border border-emerald-500/40 font-bold">
                  HACKATHON DEEP DIVE
                </span>
              </div>
              <p className="text-xs font-mono text-slate-400">
                FROZEN DETERMINISTIC LAYERS // ZERO-HALLUCINATION EVIDENCE POLICY
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
                  ? "bg-cyan-500/20 border-cyan-400 text-white shadow-[0_0_15px_rgba(0,242,254,0.3)]"
                  : "bg-slate-900/80 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200"
              }`}
            >
              <span className="text-[10px] font-mono text-cyan-400 font-bold block">
                {stg.name}
              </span>
              <span className="text-xs font-bold truncate block">{stg.code}</span>
              <span className="text-[9px] font-mono text-emerald-400 mt-1 block">
                {stg.latencyMs}ms
              </span>
            </button>
          ))}
        </div>

        {/* Selected Stage Detail Panel */}
        <div className="flex-1 overflow-y-auto p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-2xl font-black text-cyan-300 font-mono">
                {selectedStage.name}: {selectedStage.code}
              </span>
              <span className="px-2 py-0.5 rounded text-xs font-mono bg-emerald-950 text-emerald-300 border border-emerald-500/40">
                STATUS: {selectedStage.status}
              </span>
            </div>

            <span className="text-xs font-mono text-slate-400">
              INFERENCE LATENCY: <strong className="text-white">{selectedStage.latencyMs} ms</strong>
            </span>
          </div>

          <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-1">
            <span className="text-xs font-mono text-cyan-400 font-bold">CORE OBJECTIVE & CONTRACT:</span>
            <p className="text-xs text-slate-200 leading-relaxed font-sans">
              {selectedStage.purpose}
            </p>
          </div>

          {/* Contracts I/O Diagram */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
            <div className="p-3.5 rounded-xl bg-slate-950/90 border border-slate-800">
              <span className="text-slate-400 block mb-1">INPUT CONTRACT SPEC:</span>
              <span className="text-white font-bold">{selectedStage.inputContract}</span>
              <p className="text-[11px] text-slate-400 mt-1">
                Validated deterministically via Stage-B schema contracts before execution.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950/90 border border-slate-800">
              <span className="text-slate-400 block mb-1">OUTPUT CONTRACT SPEC:</span>
              <span className="text-emerald-400 font-bold">{selectedStage.outputContract}</span>
              <p className="text-[11px] text-slate-400 mt-1">
                Strict immutable frozen dataclass passed across module boundaries.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-4 border-t border-slate-800 flex items-center justify-between text-xs font-mono text-slate-400">
          <span>7 INDEPENDENT FROZEN LAYERS // OVER 219 UNIT TESTS PASSING</span>
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold hover:shadow-[0_0_15px_rgba(0,242,254,0.4)] transition-all"
          >
            Return to Interactive Lab
          </button>
        </div>
      </div>
    </div>
  );
};
