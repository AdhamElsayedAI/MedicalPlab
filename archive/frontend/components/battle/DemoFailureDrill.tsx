"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  RotateCcw,
  Zap,
  CheckCircle2,
  Lock,
  Server,
  WifiOff,
  Flame,
  HelpCircle,
  Sparkles,
} from "lucide-react";
import { DEMO_FAILURE_DRILLS } from "@/lib/stage-l-data";
import { FailureDrillScenario } from "@/lib/types";

export const DemoFailureDrill: React.FC = () => {
  const [activeDrillId, setActiveDrillId] = useState<string | null>(null);
  const [drillResolved, setDrillResolved] = useState<Record<string, boolean>>({});

  const triggerDrill = (id: string) => {
    setActiveDrillId(id);
    setDrillResolved((prev) => ({ ...prev, [id]: false }));
  };

  const executeRecovery = (id: string) => {
    setDrillResolved((prev) => ({ ...prev, [id]: true }));
  };

  const getDrillIcon = (id: string) => {
    switch (id) {
      case "drill_backend_fail":
        return <Server className="w-5 h-5 text-rose-400" />;
      case "drill_network_drop":
        return <WifiOff className="w-5 h-5 text-amber-400" />;
      case "drill_webgl_lag":
        return <Flame className="w-5 h-5 text-orange-400" />;
      case "drill_judge_curveball":
        return <HelpCircle className="w-5 h-5 text-cyan-400" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-rose-950 text-rose-300 border border-rose-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
              DEMO FAILURE DRILL & COMPETITION STRESS SIMULATOR
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              4 EMERGENCY PROTOCOLS
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Live Demo Stress Testing & Rapid Fault Recovery
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Practice recovering instantly from stage disasters: backend server crashes, venue Wi-Fi outages, WebGL GPU throttling, and hostile judge curveballs.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start md:self-center">
          <div className="px-4 py-2 rounded-xl bg-slate-900 border border-slate-700 text-xs font-mono text-emerald-400 font-bold flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4" />
            <span>Fail-Safe Redundancy: 100%</span>
          </div>
        </div>
      </div>

      {/* 4 Drill Scenarios Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {DEMO_FAILURE_DRILLS.map((drill) => {
          const isTriggered = activeDrillId === drill.id;
          const isResolved = drillResolved[drill.id];

          return (
            <div
              key={drill.id}
              className={`p-6 rounded-3xl border transition-all duration-300 space-y-4 ${
                isTriggered && !isResolved
                  ? "bg-rose-950/20 border-rose-500 shadow-[0_0_30px_rgba(244,63,94,0.25)] animate-pulse"
                  : isResolved
                  ? "bg-emerald-950/15 border-emerald-500/40"
                  : "bg-slate-950/80 border-slate-800 hover:border-slate-700"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-10 h-10 rounded-2xl bg-slate-900 border border-slate-700 flex items-center justify-center">
                    {getDrillIcon(drill.id)}
                  </div>
                  <div>
                    <span className="text-[10px] font-mono font-bold uppercase text-rose-400 block">
                      {drill.severity} STAGE RISK
                    </span>
                    <h4 className="font-bold text-white text-sm">{drill.title}</h4>
                  </div>
                </div>

                <button
                  onClick={() => triggerDrill(drill.id)}
                  className="px-3 py-1.5 rounded-xl text-xs font-mono font-bold bg-slate-900 border border-slate-700 text-slate-300 hover:text-white hover:border-rose-500/50 transition-colors"
                >
                  Test Drill
                </button>
              </div>

              {/* Symptom & Cause */}
              <div className="p-3 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-1 text-xs">
                <div>
                  <span className="font-mono text-slate-400 font-bold block text-[10px]">
                    Visible Symptom on Stage:
                  </span>
                  <p className="text-rose-200/90 font-sans">{drill.symptom}</p>
                </div>
                <div className="pt-1 border-t border-slate-800/80">
                  <span className="font-mono text-slate-500 block text-[10px]">
                    Underlying Trigger: {drill.underlyingCause}
                  </span>
                </div>
              </div>

              {/* Instant Recovery Action */}
              <div className="p-3.5 rounded-2xl bg-cyan-950/25 border border-cyan-500/30 space-y-1 text-xs">
                <span className="font-mono text-cyan-400 font-bold block text-[10px] uppercase">
                  Instant Recovery Action:
                </span>
                <p className="text-cyan-100 font-sans leading-relaxed">
                  {drill.instantRecoveryAction}
                </p>
                <div className="pt-1 font-mono text-[10px] text-emerald-400">
                  <code>{drill.recoveryCodeOrKey}</code>
                </div>
              </div>

              {/* Execution Feedback */}
              {isTriggered && (
                <div className="pt-2 flex items-center justify-between">
                  {isResolved ? (
                    <span className="text-xs font-mono text-emerald-400 font-bold flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" />
                      <span>Recovery Successfully Executed! State Pristine.</span>
                    </span>
                  ) : (
                    <button
                      onClick={() => executeRecovery(drill.id)}
                      className="w-full py-2.5 rounded-xl text-xs font-mono font-bold bg-gradient-to-r from-emerald-500 to-teal-600 text-black shadow-lg shadow-emerald-500/20 hover:scale-[1.01] transition-transform"
                    >
                      Execute Recovery Action Now
                    </button>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
