"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  CheckCircle2,
  Lock,
  Layers,
  Sparkles,
  Zap,
  Info,
  Terminal,
} from "lucide-react";
import { TRUST_LAYERS, TrustLayer } from "@/lib/grand-stage-data";

export const AITrustVisualizer: React.FC = () => {
  const [selectedLayerId, setSelectedLayerId] = useState<string>("trust-verification");

  const activeLayer =
    TRUST_LAYERS.find((l) => l.id === selectedLayerId) || TRUST_LAYERS[1];

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              ZERO-HALLUCINATION ARCHITECTURE
            </span>
            <span className="text-xs font-mono text-slate-400">
              Mathematical Verification &amp; Deterministic Safety
            </span>
          </div>
          <h2 className="text-xl font-black text-white mt-1.5 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span>Why MedicalPlab is Trustworthy</span>
          </h2>
        </div>

        <span className="text-xs font-mono text-emerald-400 font-bold">
          ✓ 100% Guideline Provenance
        </span>
      </div>

      {/* The 4 Immutable Trust Pillars Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {TRUST_LAYERS.map((layer) => {
          const isSelected = selectedLayerId === layer.id;
          return (
            <div
              key={layer.id}
              onClick={() => setSelectedLayerId(layer.id)}
              className={`p-5 rounded-2xl border cursor-pointer transition-all ${
                isSelected
                  ? "bg-slate-900 border-emerald-400 shadow-[0_0_20px_rgba(16,185,129,0.2)] ring-1 ring-emerald-400/50"
                  : "bg-slate-950/70 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-mono font-bold text-emerald-400">
                  {layer.name}
                </span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>

              <h4 className="text-sm font-bold text-white mb-2">{layer.checkmark}</h4>
              <p className="text-xs text-slate-400 leading-relaxed line-clamp-3">
                {layer.mechanism}
              </p>

              <div className="mt-4 pt-2 border-t border-slate-800 text-[11px] font-mono text-slate-500 flex justify-between">
                <span>Verified Metric:</span>
                <span className="text-emerald-300 font-bold">{layer.verifiedBenchmark.split(" ")[0]}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Trust Layer Detailed Technical Proof */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-950/80 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-widest block">
              DEEP MATHEMATICAL PROOF
            </span>
            <h3 className="text-xl font-black text-white mt-0.5">{activeLayer.name}: {activeLayer.checkmark}</h3>
          </div>
          <span className="text-xs font-mono px-3 py-1 rounded-xl bg-slate-900 border border-slate-800 text-cyan-300 font-bold">
            {activeLayer.verifiedBenchmark}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">
          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-slate-400 font-mono font-bold uppercase block">
              Architectural Mechanism:
            </span>
            <p className="text-slate-200 leading-relaxed">{activeLayer.mechanism}</p>
          </div>

          <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 space-y-2">
            <span className="text-slate-400 font-mono font-bold uppercase block">
              Mathematical / Logic Formula:
            </span>
            <p className="text-cyan-300 font-mono leading-relaxed bg-slate-950 p-2.5 rounded border border-slate-800">
              {activeLayer.mathematicalProof}
            </p>
          </div>
        </div>

        <div className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-500/30 flex items-center gap-2 text-xs font-mono text-rose-300">
          <Lock className="w-4 h-4 shrink-0 text-rose-400" />
          <span>Failure Boundary Enforcement: {activeLayer.failureBoundary}</span>
        </div>
      </div>
    </div>
  );
};
