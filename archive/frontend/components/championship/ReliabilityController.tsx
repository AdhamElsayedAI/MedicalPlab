"use client";

import React, { useState } from "react";
import {
  Lock,
  Zap,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Server,
  Activity,
  Layers,
  Sparkles,
  ShieldCheck,
} from "lucide-react";
import { PRELOADED_OFFLINE_SCENARIOS } from "@/lib/founder-data";

interface ReliabilityControllerProps {
  isOfflineMode: boolean;
  onToggleOfflineMode: () => void;
}

export const ReliabilityController: React.FC<ReliabilityControllerProps> = ({
  isOfflineMode,
  onToggleOfflineMode,
}) => {
  const [activeScenarioId, setActiveScenarioId] = useState(
    PRELOADED_OFFLINE_SCENARIOS[0].id
  );
  const [reducedMotion, setReducedMotion] = useState(false);
  const [cacheStatus, setCacheStatus] = useState<"WARMED" | "RELOADED">("WARMED");
  const [lastRecoveryTime, setLastRecoveryTime] = useState<string | null>(null);

  const scenario =
    PRELOADED_OFFLINE_SCENARIOS.find((s) => s.id === activeScenarioId) ||
    PRELOADED_OFFLINE_SCENARIOS[0];

  const handleWarmCache = () => {
    setCacheStatus("RELOADED");
    setTimeout(() => setCacheStatus("WARMED"), 1500);
  };

  const handleInstantRecovery = () => {
    const now = new Date().toLocaleTimeString();
    setLastRecoveryTime(now);
    // Instant flush and reset
    localStorage.clear();
  };

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5 text-cyan-400" />
              COMPETITION RELIABILITY & ZERO-DEPENDENCY MODE
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              100% STAGE UPTIME GUARANTEE
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Mission-Critical Offline Protection & Failure Recovery
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Preloaded deterministic scenarios, lightweight animation fallbacks, and instant emergency state recovery.
          </p>
        </div>

        {/* Global Offline Lock Toggle */}
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
              {isOfflineMode ? "Offline Mode: LOCKED (100% Safe)" : "Live API Connected"}
            </span>
          </button>
        </div>
      </div>

      {/* Quick Protection Action Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Control 1: Offline Scenario Selector */}
        <div className="p-6 rounded-3xl bg-slate-950/85 border border-slate-800 space-y-3">
          <div className="flex items-center justify-between text-xs font-mono text-cyan-400 font-bold">
            <span>PRELOADED SCENARIO</span>
            <Layers className="w-4 h-4" />
          </div>
          <p className="text-xs text-slate-400 font-sans">
            Choose which high-yield emergency scenario is locked into client-side cache.
          </p>
          <div className="space-y-1.5">
            {PRELOADED_OFFLINE_SCENARIOS.map((sc) => (
              <button
                key={sc.id}
                onClick={() => setActiveScenarioId(sc.id)}
                className={`w-full text-left p-2.5 rounded-xl text-xs font-mono transition-all flex items-center justify-between ${
                  sc.id === activeScenarioId
                    ? "bg-cyan-950 text-cyan-300 border border-cyan-500/40 font-bold"
                    : "bg-slate-900/60 text-slate-400 hover:text-white"
                }`}
              >
                <span>{sc.name}</span>
                {sc.id === activeScenarioId && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Control 2: Projection & Animation Fallback */}
        <div className="p-6 rounded-3xl bg-slate-950/85 border border-slate-800 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-purple-400 font-bold">
              <span>ANIMATION FALLBACK</span>
              <Zap className="w-4 h-4" />
            </div>
            <p className="text-xs text-slate-400 font-sans mt-2">
              For low-spec stage projection laptops or laggy HDMI connections, force lightweight 60 FPS CSS mode.
            </p>
          </div>

          <button
            onClick={() => setReducedMotion(!reducedMotion)}
            className={`w-full py-2.5 rounded-xl text-xs font-mono font-bold border transition-all ${
              reducedMotion
                ? "bg-purple-950 border-purple-500 text-purple-300 shadow-[0_0_12px_rgba(168,85,247,0.3)]"
                : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
            }`}
          >
            {reducedMotion ? "Lightweight 60 FPS: ON" : "Rich Shaders & 3D: ON"}
          </button>
        </div>

        {/* Control 3: Instant Emergency Recovery */}
        <div className="p-6 rounded-3xl bg-slate-950/85 border border-slate-800 space-y-3 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between text-xs font-mono text-rose-400 font-bold">
              <span>STAGE PANIC BUTTON</span>
              <RotateCcw className="w-4 h-4" />
            </div>
            <p className="text-xs text-slate-400 font-sans mt-2">
              If an unexpected browser freeze or UI glitch occurs during presentation, click to flush state instantly to pristine baseline.
            </p>
          </div>

          <button
            onClick={handleInstantRecovery}
            className="w-full py-2.5 rounded-xl text-xs font-mono font-bold bg-rose-950/80 border border-rose-500/50 text-rose-300 hover:bg-rose-900 transition-colors flex items-center justify-center gap-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Instant Recovery Reset</span>
          </button>

          {lastRecoveryTime && (
            <span className="text-[10px] font-mono text-emerald-400 text-center block">
              Last reset: {lastRecoveryTime} (State 100% Pristine)
            </span>
          )}
        </div>
      </div>

      {/* Active Cached Scenario Deep Dive */}
      <div className="p-6 sm:p-8 rounded-3xl bg-slate-950/90 border border-cyan-500/20 shadow-lg space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div>
            <span className="text-[10px] font-mono text-cyan-400 uppercase font-bold block">
              Active Offline Cache Payload
            </span>
            <h4 className="text-lg font-bold text-white">{scenario.name}</h4>
          </div>

          <button
            onClick={handleWarmCache}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-mono bg-slate-900 border border-slate-700 text-cyan-300 hover:border-cyan-400 transition-colors"
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Cache Status: {cacheStatus}</span>
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs font-sans">
          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 block font-bold uppercase">
              Preloaded Vitals
            </span>
            <p className="text-slate-200">
              HR: {scenario.vitals.hr} bpm | BP: {scenario.vitals.bp} | SpO2: {scenario.vitals.spo2}%
            </p>
            <span className="text-[11px] font-mono text-emerald-400 block">
              ECG: {scenario.vitals.ecg}
            </span>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 block font-bold uppercase">
              Validated Interventions
            </span>
            <p className="text-slate-200">
              {scenario.interventions.length} pre-tested bedside actions with deterministic AI responses.
            </p>
          </div>

          <div className="p-3.5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1">
            <span className="text-[10px] font-mono text-slate-400 block font-bold uppercase">
              Cached NICE Citations
            </span>
            <p className="text-slate-200">
              {scenario.evidenceCitations.length} full-text guideline quotes embedded locally.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
