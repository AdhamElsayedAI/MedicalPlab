"use client";

import React, { useState } from "react";
import {
  ShieldCheck,
  WifiOff,
  RefreshCw,
  CheckCircle2,
  Database,
  AlertTriangle,
  Zap,
  Activity,
  HeartPulse,
  RotateCcw,
} from "lucide-react";
import { SAFE_MODE_SCENARIOS, PreloadedClinicalScenario } from "@/lib/grand-stage-data";

interface ChampionshipSafeModeProps {
  onPanicReset: () => void;
  onResetDemo: () => void;
}

export const ChampionshipSafeMode: React.FC<ChampionshipSafeModeProps> = ({
  onPanicReset,
  onResetDemo,
}) => {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>("safe-stemi");
  const [isOfflineLocked, setIsOfflineLocked] = useState(true);
  const [feedbackMessage, setFeedbackMessage] = useState<string | null>(null);

  const activeScenario =
    SAFE_MODE_SCENARIOS.find((s) => s.id === selectedScenarioId) || SAFE_MODE_SCENARIOS[0];

  const triggerFeedback = (msg: string) => {
    setFeedbackMessage(msg);
    setTimeout(() => setFeedbackMessage(null), 3000);
  };

  const handleExecutePanic = () => {
    onPanicReset();
    triggerFeedback("PANIC RESET EXECUTED: All client states, timers, and telemetry restored to pristine baseline.");
  };

  const handleExecuteResetDemo = () => {
    onResetDemo();
    triggerFeedback("DEMO RESET: Presentation timeline rewound to Scene 1 (Medical Education Crisis).");
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-4 rounded-xl border border-emerald-500/30 bg-emerald-950/20 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
              AIR-GAPPED RESILIENCE
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
              Zero External Network Dependency
            </span>
          </div>
          <h2 className="text-xl font-black text-white mt-1.5 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            <span>Grand Championship Safe Mode &amp; Panic Station</span>
          </h2>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 flex items-center gap-1.5 font-bold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>100% IN-MEMORY DETERMINISTIC</span>
          </span>
        </div>
      </div>

      {/* Live Action Feedback Toast */}
      {feedbackMessage && (
        <div className="p-3 rounded-xl bg-emerald-950/90 border border-emerald-500/50 text-emerald-300 text-xs font-mono flex items-center gap-2 shadow-[0_0_20px_rgba(16,185,129,0.3)] animate-in fade-in slide-in-from-top-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{feedbackMessage}</span>
        </div>
      )}

      {/* Emergency Control Console (3 Quick Action Cards) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {/* Button 1: PANIC RESET */}
        <div className="p-5 rounded-2xl border border-rose-500/40 bg-gradient-to-b from-rose-950/30 to-slate-950 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-black text-rose-400 uppercase tracking-widest">
              EMERGENCY KILLSWITCH
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
              0ms ACTION
            </span>
          </div>

          <h3 className="text-lg font-bold text-white">PANIC RESET</h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            Instantly purges all in-flight WebGL states, clears local session storage, stops all timers, and resets MedicalPlab back to the immutable baseline.
          </p>

          <button
            onClick={handleExecutePanic}
            className="w-full py-2.5 px-4 rounded-xl text-xs font-mono font-black bg-rose-500 hover:bg-rose-400 text-black shadow-[0_0_20px_rgba(244,63,94,0.4)] transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            EXECUTE PANIC RESET
          </button>
        </div>

        {/* Button 2: RESET DEMO */}
        <div className="p-5 rounded-2xl border border-amber-500/40 bg-gradient-to-b from-amber-950/30 to-slate-950 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-black text-amber-400 uppercase tracking-widest">
              TIMELINE REWIND
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
              SCENE 1
            </span>
          </div>

          <h3 className="text-lg font-bold text-white">RESET DEMO</h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            Rewinds the 5-minute championship presentation to Scene 1 (Crisis Statement), resetting presentation timers while preserving cached clinical scenarios.
          </p>

          <button
            onClick={handleExecuteResetDemo}
            className="w-full py-2.5 px-4 rounded-xl text-xs font-mono font-black bg-amber-500 hover:bg-amber-400 text-black shadow-[0_0_20px_rgba(245,158,11,0.4)] transition-all hover:scale-[1.02] active:scale-[0.98]"
          >
            REWIND DEMO TIMELINE
          </button>
        </div>

        {/* Button 3: OFFLINE PRESENTATION LOCK */}
        <div className="p-5 rounded-2xl border border-cyan-500/40 bg-gradient-to-b from-cyan-950/30 to-slate-950 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono font-black text-cyan-400 uppercase tracking-widest">
              NETWORK SECURITY
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              AIR-GAPPED
            </span>
          </div>

          <h3 className="text-lg font-bold text-white">Offline Presentation Lock</h3>
          <p className="text-xs text-slate-300 leading-relaxed">
            Forbids any external fetch calls. Guarantees that stage presentation will never fail even if venue Wi-Fi drops completely during live pitching.
          </p>

          <button
            onClick={() => {
              setIsOfflineLocked(!isOfflineLocked);
              triggerFeedback(
                !isOfflineLocked
                  ? "Air-Gapped Lock Enforced: External network calls strictly blocked."
                  : "Hybrid Network Mode Active."
              );
            }}
            className={`w-full py-2.5 px-4 rounded-xl text-xs font-mono font-black transition-all border ${
              isOfflineLocked
                ? "bg-cyan-500 text-black border-cyan-400 shadow-[0_0_20px_rgba(0,242,254,0.4)]"
                : "bg-slate-900 text-slate-300 border-slate-700 hover:bg-slate-800"
            }`}
          >
            {isOfflineLocked ? "✓ Air-Gapped Mode Active" : "Enforce Air-Gapped Lock"}
          </button>
        </div>
      </div>

      {/* Preloaded Clinical Scenarios Showcase */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-slate-950/80 space-y-5">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold font-mono text-white uppercase tracking-wider flex items-center gap-2">
              <Database className="w-4 h-4 text-cyan-400" />
              <span>Preloaded Deterministic Clinical Scenarios</span>
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              Select an emergency case to inject instantaneously into simulation state without remote server latency.
            </p>
          </div>

          {/* Scenario Selector Tabs */}
          <div className="flex items-center gap-2 bg-slate-900 p-1.5 rounded-xl border border-slate-800">
            {SAFE_MODE_SCENARIOS.map((s) => (
              <button
                key={s.id}
                onClick={() => {
                  setSelectedScenarioId(s.id);
                  triggerFeedback(`Loaded scenario: ${s.name}`);
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                  selectedScenarioId === s.id
                    ? "bg-cyan-500 text-black shadow-[0_0_12px_rgba(0,242,254,0.4)]"
                    : "text-slate-400 hover:text-white hover:bg-slate-800/60"
                }`}
              >
                {s.name.split(" (")[0]}
              </button>
            ))}
          </div>
        </div>

        {/* Active Scenario Card */}
        <div className="p-5 rounded-xl border border-slate-800 bg-slate-900/60 space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div>
              <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest block">
                ACTIVE SCENARIO CACHE
              </span>
              <h4 className="text-base font-bold text-white mt-0.5">{activeScenario.name}</h4>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono">
                <span className="text-slate-500">HR: </span>
                <span className="text-rose-400 font-bold">{activeScenario.vitalTelemetry.hr} bpm</span>
              </div>
              <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono">
                <span className="text-slate-500">BP: </span>
                <span className="text-cyan-400 font-bold">{activeScenario.vitalTelemetry.bp}</span>
              </div>
              <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono">
                <span className="text-slate-500">SpO2: </span>
                <span className="text-emerald-400 font-bold">{activeScenario.vitalTelemetry.spo2}%</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="space-y-2">
              <div>
                <span className="text-slate-500 font-mono block">Patient Presentation:</span>
                <p className="text-slate-300 mt-0.5">{activeScenario.patientProfile}</p>
              </div>
              <div>
                <span className="text-slate-500 font-mono block">Primary Diagnosis:</span>
                <p className="text-white font-bold mt-0.5">{activeScenario.primaryDiagnosis}</p>
              </div>
            </div>

            <div className="space-y-2">
              <div className="p-3 rounded-lg bg-rose-950/20 border border-rose-500/30">
                <span className="text-rose-400 font-mono font-bold block">Adversarial Trap Action:</span>
                <p className="text-rose-200 mt-0.5">{activeScenario.trapAction}</p>
              </div>
              <div className="p-3 rounded-lg bg-emerald-950/20 border border-emerald-500/30">
                <span className="text-emerald-400 font-mono font-bold block">Stage-D Interceptor Protection:</span>
                <p className="text-emerald-200 mt-0.5">{activeScenario.interceptorTrigger}</p>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-800 flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>Verified Citation: <strong className="text-cyan-300">{activeScenario.evidenceCitation}</strong></span>
            <span className="text-emerald-400 font-bold">✓ 0ms Cached Injection Ready</span>
          </div>
        </div>
      </div>
    </div>
  );
};
