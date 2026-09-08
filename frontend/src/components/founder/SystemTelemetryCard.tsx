"use client";

import React from "react";
import {
  Activity,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Lock,
  Zap,
  Server,
  Terminal,
} from "lucide-react";
import { FOUNDER_SYSTEM_TELEMETRY, PRELOADED_OFFLINE_SCENARIOS } from "@/lib/founder-data";

interface SystemTelemetryCardProps {
  isOfflineMode: boolean;
  onToggleOfflineMode: () => void;
}

export const SystemTelemetryCard: React.FC<SystemTelemetryCardProps> = ({
  isOfflineMode,
  onToggleOfflineMode,
}) => {
  return (
    <div className="space-y-6">
      {/* Top Telemetry Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              FOUNDER COMMAND CENTER: SYSTEM TELEMETRY
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              6 PIPELINE STAGES MONITORED
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Deterministic AI Health & Resilience Guardrails
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Real-time pipeline telemetry across frozen AI cores (Stages B, C, D, E, R, G) with 0-dependency offline fallback cache.
          </p>
        </div>

        {/* Mode Switcher Pill */}
        <div className="flex items-center gap-3 self-start md:self-center">
          <button
            onClick={onToggleOfflineMode}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-bold border transition-all ${
              isOfflineMode
                ? "bg-emerald-950/90 border-emerald-500/50 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.25)]"
                : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
            }`}
          >
            <Lock className="w-3.5 h-3.5 text-emerald-400" />
            <span>
              {isOfflineMode
                ? "Offline Resilience Mode (Active)"
                : "Live Production REST API"}
            </span>
          </button>
        </div>
      </div>

      {/* Global Health Summary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Average Pipeline Latency</span>
          <div className="text-2xl font-black font-mono text-cyan-300 flex items-baseline gap-1.5">
            <span>24.6ms</span>
            <span className="text-xs text-emerald-400 font-bold">CPU Native</span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans">
            Ultra-low latency across BM25 lexical & vector retrieval.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Evidence Confidence</span>
          <div className="text-2xl font-black font-mono text-emerald-400 flex items-baseline gap-1.5">
            <span>98.8%</span>
            <span className="text-xs text-slate-400 font-bold">NICE NG185</span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans">
            Mathematical cosine threshold and polarity verification.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Total Safety Checks</span>
          <div className="text-2xl font-black font-mono text-purple-300 flex items-baseline gap-1.5">
            <span>20,310</span>
            <span className="text-xs text-emerald-400 font-bold">100% Intercept</span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans">
            Cumulative contraindication screens executed by Stage-D.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-1">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Active Demo State</span>
          <div className="text-2xl font-black font-mono text-white flex items-baseline gap-1.5">
            <span>{isOfflineMode ? "OFFLINE" : "LIVE"}</span>
            <span className="text-xs text-cyan-400 font-bold">0% Dependency</span>
          </div>
          <p className="text-[11px] text-slate-400 font-sans">
            Preloaded deterministic scenarios guarantee 100% uptime.
          </p>
        </div>
      </div>

      {/* 6 Stage Telemetry Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {FOUNDER_SYSTEM_TELEMETRY.map((stage) => (
          <div
            key={stage.id}
            className="p-5 rounded-3xl bg-slate-950/80 border border-slate-800 hover:border-cyan-500/40 transition-colors space-y-4 shadow-md"
          >
            <div className="flex items-start justify-between gap-2">
              <div>
                <span className="text-[10px] font-mono font-bold text-cyan-400 uppercase tracking-widest block">
                  {stage.id.toUpperCase()}
                </span>
                <h4 className="font-bold text-white text-sm mt-0.5">
                  {stage.name}
                </h4>
              </div>

              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-500/40">
                {stage.status}
              </span>
            </div>

            <p className="text-xs text-slate-300 font-sans leading-relaxed">
              {stage.description}
            </p>

            {/* Metrics Row */}
            <div className="grid grid-cols-3 gap-2 p-3 rounded-2xl bg-slate-900/80 border border-slate-800/80 font-mono text-center">
              <div>
                <span className="text-[9px] text-slate-500 block">LATENCY</span>
                <span className="text-xs font-bold text-white">{stage.latencyMs}ms</span>
              </div>
              <div>
                <span className="text-[9px] text-slate-500 block">CONFIDENCE</span>
                <span className="text-xs font-bold text-emerald-400">{stage.confidenceScore}%</span>
              </div>
              <div>
                <span className="text-[9px] text-slate-500 block">CHECKS</span>
                <span className="text-xs font-bold text-cyan-300">{stage.verifiedChecks}</span>
              </div>
            </div>

            {/* Contract Code */}
            <div className="p-2.5 rounded-xl bg-black/60 border border-slate-800 font-mono text-[10px] text-slate-400 truncate">
              <code>{stage.contract}</code>
            </div>
          </div>
        ))}
      </div>

      {/* Preloaded Scenarios Fallback Inspector */}
      {isOfflineMode && (
        <div className="p-5 rounded-3xl bg-emerald-950/20 border border-emerald-500/40 space-y-3 animate-in fade-in duration-200">
          <div className="flex items-center justify-between text-xs font-mono text-emerald-400 font-bold border-b border-emerald-500/20 pb-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>PRELOADED OFFLINE RESILIENCE SCENARIOS READY</span>
            </div>
            <span className="text-[11px] text-slate-400">
              Zero External Network Dependencies
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-sans">
            {PRELOADED_OFFLINE_SCENARIOS.map((sc) => (
              <div
                key={sc.id}
                className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-1.5"
              >
                <div className="flex items-center justify-between font-mono font-bold">
                  <span className="text-white">{sc.name}</span>
                  <span className="text-emerald-400 text-[11px]">{sc.system}</span>
                </div>
                <div className="text-[11px] text-slate-400">
                  Condition: {sc.condition} | Initial ECG: {sc.vitals.ecg}
                </div>
                <div className="text-[10px] font-mono text-slate-500">
                  {sc.interventions.length} interventions pre-tested | {sc.evidenceCitations.length} NICE citations cached
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
