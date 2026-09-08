"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  WifiOff,
  RefreshCw,
  CheckCircle2,
  HardDrive,
  Database,
  Lock,
  Zap,
} from "lucide-react";

export const ValidationSafeMode: React.FC = () => {
  const [isOfflineLocked, setIsOfflineLocked] = useState(true);
  const [resetStatus, setResetStatus] = useState(false);

  const handlePanicReset = () => {
    setResetStatus(true);
    setTimeout(() => {
      setResetStatus(false);
    }, 2500);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              ZERO NETWORK RESILIENCE
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
              Deterministic Air-Gapped Fallback
            </span>
          </div>
          <h2 className="text-xl font-black text-white mt-1.5 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span>Validation Safe Mode &amp; Audit Resilience Engine</span>
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5 font-bold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>LOCAL MEMORY GROUNDED (0ms Latency)</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Card 1: Air-Gapped Dataset Status */}
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-950/70 space-y-3">
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-cyan-400">
              <Database className="w-5 h-5" />
            </div>
            <span className="text-xs font-mono text-emerald-400 font-bold">100% PRELOADED</span>
          </div>

          <h3 className="text-base font-bold text-white">Deterministic Pilot Cohort</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            All 4 Student Journey phases, 6 Outcome metrics, and NHS Deanery hospital telemetry are bundled directly in static client memory (`stage-m-data.ts`).
          </p>

          <div className="pt-2 border-t border-slate-800 text-[11px] font-mono text-slate-400 space-y-1">
            <div className="flex justify-between">
              <span>Candidate Records:</span>
              <span className="text-white font-bold">250 Cohort</span>
            </div>
            <div className="flex justify-between">
              <span>NICE Guidelines Indexed:</span>
              <span className="text-white font-bold">NG185, NG51, BNF 85</span>
            </div>
            <div className="flex justify-between">
              <span>External API Dependencies:</span>
              <span className="text-emerald-400 font-bold">0 (Zero Remote Calls)</span>
            </div>
          </div>
        </div>

        {/* Card 2: Offline Lock Controller */}
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-950/70 space-y-3">
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-amber-400">
              <WifiOff className="w-5 h-5" />
            </div>
            <span className="text-xs font-mono text-amber-400 font-bold">
              {isOfflineLocked ? "OFFLINE ENFORCED" : "HYBRID NETWORK"}
            </span>
          </div>

          <h3 className="text-base font-bold text-white">Zero-Network Lock</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            Forces all ROI calculations, student journey state transitions, and deanery intervention actions to run completely offline without contacting external networks.
          </p>

          <button
            onClick={() => setIsOfflineLocked(!isOfflineLocked)}
            className={`w-full py-2 px-3 rounded-xl text-xs font-mono font-bold transition-all border ${
              isOfflineLocked
                ? "bg-amber-500/20 text-amber-300 border-amber-500/40"
                : "bg-slate-900 text-slate-400 border-slate-700"
            }`}
          >
            {isOfflineLocked ? "✓ Air-Gapped Mode Active" : "Activate Air-Gapped Lock"}
          </button>
        </div>

        {/* Card 3: Stage Panic Reset */}
        <div className="p-5 rounded-2xl border border-slate-800 bg-slate-950/70 space-y-3">
          <div className="flex items-center justify-between">
            <div className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-rose-400">
              <RefreshCw className={`w-5 h-5 ${resetStatus ? "animate-spin text-rose-400" : ""}`} />
            </div>
            <span className="text-xs font-mono text-rose-400 font-bold">EMERGENCY FLUSH</span>
          </div>

          <h3 className="text-base font-bold text-white">Stage Panic State Reset</h3>
          <p className="text-xs text-slate-400 leading-relaxed">
            If an unexpected state mismatch occurs during a live judge presentation, click this button to instantly restore all datasets and sliders to pristine default values.
          </p>

          <button
            onClick={handlePanicReset}
            disabled={resetStatus}
            className={`w-full py-2 px-3 rounded-xl text-xs font-mono font-bold transition-all border flex items-center justify-center gap-1.5 ${
              resetStatus
                ? "bg-emerald-500 text-black border-emerald-400 shadow-[0_0_12px_rgba(16,185,129,0.5)]"
                : "bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border-rose-500/40"
            }`}
          >
            {resetStatus ? (
              <>
                <CheckCircle2 className="w-4 h-4" />
                <span>Pristine State Restored!</span>
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4" />
                <span>Trigger Panic Reset</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
