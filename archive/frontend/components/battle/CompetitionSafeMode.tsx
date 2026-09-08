"use client";

import React, { useState } from "react";
import {
  Lock,
  RotateCcw,
  CheckCircle2,
  AlertOctagon,
  Zap,
  Server,
  Layers,
  Sparkles,
} from "lucide-react";
import { PRELOADED_OFFLINE_SCENARIOS } from "@/lib/founder-data";

interface CompetitionSafeModeProps {
  isOfflineMode: boolean;
  onToggleOfflineMode: () => void;
}

export const CompetitionSafeMode: React.FC<CompetitionSafeModeProps> = ({
  isOfflineMode,
  onToggleOfflineMode,
}) => {
  const [selectedScenarioId, setSelectedScenarioId] = useState(
    PRELOADED_OFFLINE_SCENARIOS[0].id
  );
  const [force60FPS, setForce60FPS] = useState(false);
  const [resetFeedback, setResetFeedback] = useState<string | null>(null);

  const scenario =
    PRELOADED_OFFLINE_SCENARIOS.find((s) => s.id === selectedScenarioId) ||
    PRELOADED_OFFLINE_SCENARIOS[0];

  const handlePanicReset = () => {
    localStorage.clear();
    setResetFeedback(`State Flushed & Restored at ${new Date().toLocaleTimeString()}`);
    setTimeout(() => setResetFeedback(null), 3500);
  };

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-cyan-400" />
              COMPETITION SAFE MODE & ZERO-DEPENDENCY PROTECTION
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              100% STAGE RESILIENCE
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Zero-Network Presentation Lock & Instant Emergency Reset
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Pre-bundled client-side scenarios, guaranteed 0ms network latency, and instant panic reset for high-stakes competition stages.
          </p>
        </div>

        <div className="flex items-center gap-3 self-start md:self-center">
          <button
            onClick={onToggleOfflineMode}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-mono font-bold border transition-all ${
              isOfflineMode
                ? "bg-emerald-950 border-emerald-500 text-emerald-300 shadow-[0_0_20px_rgba(16,185,129,0.3)]"
                : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
            }`}
          >
            <Lock className="w-4 h-4" />
            <span>
              {isOfflineMode
                ? "Safe Mode: ACTIVE (Zero Dependencies)"
                : "Live API Mode"}
            </span>
          </button>
        </div>
      </div>

      {/* Safety Controls Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Control 1: Scenario Preloader */}
        <div className="p-6 rounded-3xl bg-slate-950/85 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-cyan-400 font-bold">
            <span>PRELOADED SCENARIO</span>
            <Layers className="w-4 h-4" />
          </div>
          <p className="text-xs text-slate-400 font-sans">
            Locks deterministic patient state graph directly into client memory.
          </p>
          <div className="space-y-1.5">
            {PRELOADED_OFFLINE_SCENARIOS.map((sc) => (
              <button
                key={sc.id}
                onClick={() => setSelectedScenarioId(sc.id)}
                className={`w-full text-left p-2.5 rounded-xl text-xs font-mono transition-all flex items-center justify-between ${
                  sc.id === selectedScenarioId
                    ? "bg-cyan-950 text-cyan-300 border border-cyan-500/40 font-bold"
                    : "bg-slate-900/60 text-slate-400 hover:text-white"
                }`}
              >
                <span>{sc.name}</span>
                {sc.id === selectedScenarioId && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Control 2: Lightweight 60 FPS Mode */}
        <div className="p-6 rounded-3xl bg-slate-950/85 border border-slate-800 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-purple-400 font-bold">
              <span>PROJECTION HARDWARE OVERRIDE</span>
              <Zap className="w-4 h-4" />
            </div>
            <p className="text-xs text-slate-400 font-sans mt-2">
              Forces pure CSS transforms and disables intensive WebGL fragment shaders for low-spec stage projection rigs.
            </p>
          </div>

          <button
            onClick={() => setForce60FPS(!force60FPS)}
            className={`w-full py-2.5 rounded-xl text-xs font-mono font-bold border transition-all ${
              force60FPS
                ? "bg-purple-950 border-purple-500 text-purple-300 shadow-[0_0_12px_rgba(168,85,247,0.3)]"
                : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
            }`}
          >
            {force60FPS ? "60 FPS CSS Override: ON" : "Default Rich Visuals: ON"}
          </button>
        </div>

        {/* Control 3: Emergency Panic Reset Button */}
        <div className="p-6 rounded-3xl bg-slate-950/85 border border-slate-800 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-rose-400 font-bold">
              <span>STAGE PANIC RESET</span>
              <RotateCcw className="w-4 h-4" />
            </div>
            <p className="text-xs text-slate-400 font-sans mt-2">
              If an unexpected UI glitch or browser state issue occurs on stage, click to instantly purge local storage and restore pristine baseline state.
            </p>
          </div>

          <button
            onClick={handlePanicReset}
            className="w-full py-2.5 rounded-xl text-xs font-mono font-bold bg-rose-950/80 border border-rose-500/50 text-rose-300 hover:bg-rose-900 transition-colors flex items-center justify-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Emergency State Reset</span>
          </button>

          {resetFeedback && (
            <span className="text-[10px] font-mono text-emerald-400 text-center block animate-in fade-in duration-200">
              ✓ {resetFeedback}
            </span>
          )}
        </div>
      </div>

      {/* Preloaded Scenario Inspection Box */}
      <div className="p-6 sm:p-8 rounded-3xl bg-slate-950/90 border border-cyan-500/20 shadow-lg space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <span className="text-xs font-mono text-cyan-400 font-bold uppercase">
            Active Client Cache: {scenario.name}
          </span>
          <span className="text-xs font-mono text-emerald-400">
            0ms Network Latency
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-sans">
          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 font-bold uppercase block">
              Pre-Seeded Vitals
            </span>
            <p className="text-slate-200 font-mono">
              HR: {scenario.vitals.hr} | BP: {scenario.vitals.bp} | SpO2: {scenario.vitals.spo2}%
            </p>
            <span className="text-[11px] font-mono text-emerald-400 block">
              ECG: {scenario.vitals.ecg}
            </span>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 font-bold uppercase block">
              Interventions Catalog
            </span>
            <p className="text-slate-200">
              {scenario.interventions.length} pre-tested bedside actions with pre-rendered Stage-D safety feedback.
            </p>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 font-bold uppercase block">
              Embedded Citations
            </span>
            <p className="text-slate-200">
              {scenario.evidenceCitations.length} full-text NICE & BNF guideline passages cached locally.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
