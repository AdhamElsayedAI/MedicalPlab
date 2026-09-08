"use client";

import React, { useState } from "react";
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Activity,
  Compass,
  Layers,
  Award,
  ChevronRight,
} from "lucide-react";
import { JOURNEY_PHASES } from "@/lib/stage-m-data";
import { NavigationMode } from "@/lib/types";

interface StudentJourneySimulatorProps {
  onNavigateToMode?: (mode: NavigationMode) => void;
}

export const StudentJourneySimulator: React.FC<StudentJourneySimulatorProps> = ({
  onNavigateToMode,
}) => {
  const [activePhaseIdx, setActivePhaseIdx] = useState(0);
  const currentPhase = JOURNEY_PHASES[activePhaseIdx];

  return (
    <div className="space-y-6">
      {/* Top Banner with Compliance Badge */}
      <div className="p-4 rounded-xl border border-cyan-500/30 bg-cyan-950/20 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
              4-PHASE SIMULATOR
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
              [Demo Simulation &amp; Prototype Projection]
            </span>
          </div>
          <h2 className="text-xl font-black text-white mt-1.5 flex items-center gap-2">
            <span>The Candidate Transformation Journey</span>
            <span className="text-sm font-normal text-slate-400">
              — Diagnostic $\rightarrow$ Gap Detection $\rightarrow$ Adaptive Remediation $\rightarrow$ Certified Mastery
            </span>
          </h2>
        </div>

        {/* Phase Stepper Pills */}
        <div className="flex items-center gap-1.5 bg-slate-900/90 p-1.5 rounded-xl border border-slate-800">
          {JOURNEY_PHASES.map((p, idx) => (
            <button
              key={p.id}
              onClick={() => setActivePhaseIdx(idx)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${
                activePhaseIdx === idx
                  ? "bg-cyan-500 text-black shadow-[0_0_12px_rgba(0,242,254,0.4)]"
                  : "text-slate-400 hover:text-white hover:bg-slate-800/60"
              }`}
            >
              <span>Phase {p.phaseNumber}</span>
              {activePhaseIdx === idx && (
                <span className="w-1.5 h-1.5 rounded-full bg-black animate-pulse" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Main 4-Phase Interactive Showcase */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Phase Visual Stepper (4 cols) */}
        <div className="lg:col-span-4 space-y-3">
          {JOURNEY_PHASES.map((phase, idx) => {
            const isSelected = activePhaseIdx === idx;
            return (
              <div
                key={phase.id}
                onClick={() => setActivePhaseIdx(idx)}
                className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 ${
                  isSelected
                    ? "bg-slate-900 border-cyan-400 shadow-[0_0_20px_rgba(0,242,254,0.15)] ring-1 ring-cyan-400/50"
                    : "bg-slate-950/60 border-slate-800 hover:border-slate-700 opacity-75 hover:opacity-100"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono tracking-widest text-slate-500 uppercase">
                    PHASE {phase.phaseNumber} OF 4
                  </span>
                  <span
                    className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                      idx === 0
                        ? "bg-rose-500/20 text-rose-300"
                        : idx === 1
                        ? "bg-amber-500/20 text-amber-300"
                        : idx === 2
                        ? "bg-cyan-500/20 text-cyan-300"
                        : "bg-emerald-500/20 text-emerald-300"
                    }`}
                  >
                    Score: {phase.userState.diagnosticScore}%
                  </span>
                </div>

                <h4 className="text-sm font-bold text-white mt-1.5 flex items-center justify-between">
                  <span>{phase.phaseTitle}</span>
                  {isSelected && <ChevronRight className="w-4 h-4 text-cyan-400" />}
                </h4>

                <p className="text-xs text-slate-400 mt-1 line-clamp-2">
                  {phase.userState.errorState}
                </p>

                <div className="mt-3 pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <span>{phase.aiAction.stage.split(" ")[0]}</span>
                  <span className="text-cyan-400">{phase.aiAction.runtimeLatency}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right: Phase Deep Dive Canvas (8 cols) */}
        <div className="lg:col-span-8 space-y-5">
          {/* Phase Hero Status Card */}
          <div className="p-6 rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900/90 to-slate-950 relative overflow-hidden">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
                <span className="text-xs font-mono font-bold text-cyan-400 tracking-wider">
                  ACTIVE SIMULATION STAGE: PHASE {currentPhase.phaseNumber}
                </span>
              </div>
              <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {currentPhase.visualTransition.hudBadge}
              </span>
            </div>

            <h3 className="text-2xl font-black text-white">
              {currentPhase.phaseTitle}
            </h3>
            <p className="text-sm text-slate-300 mt-2">
              Persona: <strong className="text-cyan-300">{currentPhase.userState.persona}</strong>
            </p>

            {/* Score Progress Bar */}
            <div className="mt-4 p-4 rounded-xl bg-slate-950/80 border border-slate-800">
              <div className="flex items-center justify-between text-xs font-mono mb-2">
                <span className="text-slate-400">Clinical Readiness Benchmark:</span>
                <span className="font-bold text-cyan-400 text-sm">
                  {currentPhase.userState.diagnosticScore}% PLAB 1 Competence
                </span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-3 overflow-hidden border border-slate-800">
                <div
                  className={`h-full transition-all duration-500 ${
                    currentPhase.userState.diagnosticScore >= 80
                      ? "bg-gradient-to-r from-emerald-500 to-teal-400"
                      : currentPhase.userState.diagnosticScore >= 65
                      ? "bg-gradient-to-r from-cyan-500 to-blue-500"
                      : "bg-gradient-to-r from-rose-500 to-amber-500"
                  }`}
                  style={{ width: `${currentPhase.userState.diagnosticScore}%` }}
                />
              </div>
              <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400">
                <span>Pass Threshold: 68%</span>
                <span>Target Mastery: 85%+</span>
              </div>
            </div>

            {/* 3 Core Intelligence Dimensions */}
            <div className="mt-5 grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* User State */}
              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
                <div className="flex items-center gap-2 text-xs font-mono font-bold text-amber-400 mb-2">
                  <Activity className="w-3.5 h-3.5" />
                  <span>CANDIDATE STATE</span>
                </div>
                <div className="space-y-1.5 text-xs">
                  <div>
                    <span className="text-slate-500">Confidence: </span>
                    <span className="text-slate-200 font-semibold">{currentPhase.userState.clinicalConfidence}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Clinical Defect: </span>
                    <span className="text-rose-300 font-mono">{currentPhase.userState.errorState}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Cognitive State: </span>
                    <span className="text-slate-300 italic">{currentPhase.userState.sentiment}</span>
                  </div>
                </div>
              </div>

              {/* AI Engine Action */}
              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
                <div className="flex items-center gap-2 text-xs font-mono font-bold text-cyan-400 mb-2">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>AI PIPELINE INTERVENTION</span>
                </div>
                <div className="space-y-1.5 text-xs">
                  <div>
                    <span className="text-slate-500">Active Module: </span>
                    <span className="text-cyan-300 font-mono font-bold">{currentPhase.aiAction.stage}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Algorithm: </span>
                    <span className="text-slate-300">{currentPhase.aiAction.algorithm}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Execution: </span>
                    <span className="text-slate-300">{currentPhase.aiAction.intervention}</span>
                  </div>
                </div>
              </div>

              {/* Medical Learning Objective */}
              <div className="p-4 rounded-xl bg-slate-900/70 border border-slate-800">
                <div className="flex items-center gap-2 text-xs font-mono font-bold text-emerald-400 mb-2">
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>CLINICAL OBJECTIVE</span>
                </div>
                <div className="space-y-1.5 text-xs">
                  <div>
                    <span className="text-slate-500">Guideline: </span>
                    <span className="text-emerald-300 font-mono font-semibold">{currentPhase.medicalObjective.guidelineRef}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Core Goal: </span>
                    <span className="text-slate-300">{currentPhase.medicalObjective.learningGoal}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Safety Rule: </span>
                    <span className="text-amber-300 font-mono text-[11px]">{currentPhase.medicalObjective.safetyRule}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Stepper Controls */}
            <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between">
              <button
                disabled={activePhaseIdx === 0}
                onClick={() => setActivePhaseIdx((prev) => Math.max(0, prev - 1))}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-bold border border-slate-700 bg-slate-900 text-slate-300 hover:bg-slate-800 disabled:opacity-30 transition-all"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>Previous Phase</span>
              </button>

              <div className="flex items-center gap-3">
                {onNavigateToMode && (
                  <button
                    onClick={() => onNavigateToMode(activePhaseIdx === 2 ? "anatomy" : "tutor")}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-mono font-bold bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-cyan-500/30 transition-all"
                  >
                    <Layers className="w-3.5 h-3.5" />
                    <span>Launch Corresponding Lab</span>
                  </button>
                )}

                <button
                  disabled={activePhaseIdx === JOURNEY_PHASES.length - 1}
                  onClick={() => setActivePhaseIdx((prev) => Math.min(JOURNEY_PHASES.length - 1, prev + 1))}
                  className="flex items-center gap-2 px-5 py-2 rounded-lg text-xs font-mono font-bold bg-cyan-500 hover:bg-cyan-400 text-black shadow-[0_0_15px_rgba(0,242,254,0.3)] disabled:opacity-30 transition-all"
                >
                  <span>Advance to Phase {Math.min(4, activePhaseIdx + 2)}</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
