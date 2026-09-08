"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { SIMULATION_SCENARIOS, SimulationScenario } from "@/lib/stage-x-data";

export default function ClinicalSimulationUniverse() {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>(SIMULATION_SCENARIOS[0].id);
  const [activeDecisionsExecuted, setActiveDecisionsExecuted] = useState<string[]>([]);
  const [decisionFeedback, setDecisionFeedback] = useState<{
    id: string;
    safe: boolean;
    feedback: string;
    effect: string;
  } | null>(null);

  const scenario = SIMULATION_SCENARIOS.find((s) => s.id === selectedScenarioId) || SIMULATION_SCENARIOS[0];

  const handleDecisionClick = (dec: (typeof scenario.criticalDecisions)[0]) => {
    setActiveDecisionsExecuted((prev) => [...prev, dec.id]);
    setDecisionFeedback({
      id: dec.id,
      safe: dec.safe,
      feedback: dec.feedback,
      effect: dec.outcomeEffect
    });
  };

  const handleResetScenario = () => {
    setActiveDecisionsExecuted([]);
    setDecisionFeedback(null);
  };

  // Dynamically compute simulated vitals based on interventions
  const hasDecompressed = activeDecisionsExecuted.includes("dec-1");
  const hasWrongCT = activeDecisionsExecuted.includes("dec-2");
  const hasTransfusion = activeDecisionsExecuted.includes("dec-3");

  const currentHR = hasWrongCT ? 0 : hasDecompressed ? 98 : scenario.baselineVitals.hr;
  const currentBP = hasWrongCT ? "0/0 (ASYSTOLE)" : hasDecompressed ? "112/72" : scenario.baselineVitals.bp;
  const currentSpO2 = hasWrongCT ? 0 : hasDecompressed ? 96 : scenario.baselineVitals.spo2;
  const currentGCS = hasWrongCT ? 3 : hasDecompressed ? 14 : scenario.baselineVitals.gcs;

  return (
    <div className="space-y-6">
      {/* Simulation / Demo Clear Disclaimer Banner */}
      <div className="bg-amber-950/40 border border-amber-500/50 rounded-2xl p-4 text-xs text-amber-300 flex items-center justify-between gap-4 shadow-xl">
        <div className="flex items-center gap-3">
          <span className="w-3 h-3 rounded-full bg-amber-400 animate-ping shrink-0" />
          <div>
            <span className="font-bold uppercase tracking-wider font-mono">
              Regulatory Notice • Clinical Flight Simulation Mode
            </span>
            <p className="text-amber-200/80 text-[11px] mt-0.5">
              This interactive environment is an in-silico physiological digital twin intended for training, assessment, and algorithmic stress-testing. Not for direct real-world patient triaging.
            </p>
          </div>
        </div>
        <span className="text-[10px] font-mono px-2.5 py-1 rounded bg-amber-900/60 border border-amber-700 text-amber-200 shrink-0 font-bold">
          [SIMULATION / DEMO]
        </span>
      </div>

      {/* Top Banner & Environment Tabs */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-cyan-500/20 rounded-2xl p-5 shadow-2xl">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span className="text-xs uppercase tracking-widest font-mono text-cyan-400">
                Hospital Simulation Universe
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 border border-cyan-800 text-cyan-300">
                PhysioSim Engine 60 FPS
              </span>
            </div>
            <h2 className="text-xl md:text-2xl font-bold text-white tracking-tight">
              Virtual Healthcare Simulation Universe
            </h2>
            <p className="text-xs md:text-sm text-slate-400 mt-0.5">
              Train high-risk clinical resuscitation without endangering a single human life.
            </p>
          </div>

          {/* Environment Switcher */}
          <div className="flex items-center gap-2">
            {SIMULATION_SCENARIOS.map((sc) => (
              <button
                key={sc.id}
                onClick={() => {
                  setSelectedScenarioId(sc.id);
                  handleResetScenario();
                }}
                className={`text-xs px-3.5 py-2 rounded-xl border transition-all font-medium ${
                  selectedScenarioId === sc.id
                    ? "bg-cyan-500 text-black font-semibold border-cyan-400 shadow-md shadow-cyan-500/20"
                    : "bg-slate-950/70 text-slate-400 border-slate-800 hover:border-slate-700 hover:text-white"
                }`}
              >
                {sc.environment}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Simulation Theater */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 4 Cols: Patient Monitor & Real-Time Biometric Telemetry */}
        <div className="lg:col-span-4 space-y-5">
          {/* Patient Card */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-slate-800">
              <span className="text-xs font-mono text-cyan-400 uppercase">
                Patient Biometric Monitor
              </span>
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                  hasWrongCT
                    ? "bg-red-950 border border-red-500 text-red-300 animate-pulse"
                    : hasDecompressed
                    ? "bg-emerald-950 border border-emerald-500 text-emerald-300"
                    : "bg-cyan-950 border border-cyan-800 text-cyan-300"
                }`}
              >
                {hasWrongCT ? "CARDIAC ARREST" : hasDecompressed ? "STABILIZED" : scenario.simulationState}
              </span>
            </div>

            <div className="space-y-1">
              <div className="text-sm font-bold text-white">{scenario.patientName}</div>
              <div className="text-xs text-slate-400 font-mono">
                {scenario.patientAge} yo • {scenario.gender} • {scenario.environment}
              </div>
              <p className="text-xs text-slate-300 mt-2 bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                {scenario.chiefComplaint}
              </p>
            </div>

            {/* Live Vital Sign Grid */}
            <div className="grid grid-cols-2 gap-2.5 mt-4">
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-500 uppercase block">Heart Rate</span>
                <span
                  className={`text-xl font-bold font-mono ${
                    currentHR === 0 ? "text-red-500" : currentHR > 120 ? "text-amber-400" : "text-emerald-400"
                  }`}
                >
                  {currentHR} <span className="text-xs text-slate-500">BPM</span>
                </span>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-500 uppercase block">Blood Pressure</span>
                <span
                  className={`text-sm font-bold font-mono ${
                    hasWrongCT ? "text-red-500" : "text-cyan-400"
                  }`}
                >
                  {currentBP}
                </span>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-500 uppercase block">Oxygen SpO2</span>
                <span
                  className={`text-xl font-bold font-mono ${
                    currentSpO2 < 90 ? "text-red-400" : "text-emerald-400"
                  }`}
                >
                  {currentSpO2}%
                </span>
              </div>

              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                <span className="text-[10px] font-mono text-slate-500 uppercase block">Neurologic GCS</span>
                <span className="text-xl font-bold font-mono text-indigo-400">
                  {currentGCS}/15
                </span>
              </div>
            </div>

            {/* Safety Warnings */}
            <div className="mt-4 pt-3 border-t border-slate-800 space-y-2">
              <span className="text-[10px] font-mono text-red-400 uppercase tracking-wider block">
                Active Safety Warnings
              </span>
              {scenario.safetyWarnings.map((warn, i) => (
                <div
                  key={i}
                  className="p-2.5 rounded-lg bg-red-950/40 border border-red-900/50 text-[11px] text-red-300 flex items-center gap-2"
                >
                  <span className="text-red-400 font-bold font-mono">⚠</span>
                  <span>{warn}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right 8 Cols: Critical Decisions, Real-Time Feedback & Objectives */}
        <div className="lg:col-span-8 space-y-5">
          {/* Active Scenario Title & Clinical Objectives */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono text-cyan-400 uppercase">
                Active Resuscitation Protocol
              </span>
              <button
                onClick={handleResetScenario}
                className="text-[11px] font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:text-white"
              >
                Reset Scenario ↺
              </button>
            </div>

            <h3 className="text-lg font-bold text-white">{scenario.title}</h3>

            <div className="mt-3 bg-slate-950/70 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
              <span className="text-[10px] font-mono text-slate-400 uppercase block">
                Clinical Objectives
              </span>
              {scenario.clinicalObjectives.map((obj, i) => (
                <div key={i} className="text-xs text-slate-300 flex items-center gap-2">
                  <span className="text-cyan-400 text-xs">✓</span>
                  <span>{obj}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Interactive Decision Matrix */}
          <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
            <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider block">
              Execute Clinical Interventions
            </span>

            <div className="space-y-2.5">
              {scenario.criticalDecisions.map((dec) => {
                const isExecuted = activeDecisionsExecuted.includes(dec.id);

                return (
                  <button
                    key={dec.id}
                    onClick={() => handleDecisionClick(dec)}
                    disabled={hasWrongCT}
                    className={`w-full text-left p-4 rounded-xl border transition-all relative ${
                      isExecuted
                        ? dec.safe
                          ? "bg-emerald-950/40 border-emerald-500/60 text-emerald-200"
                          : "bg-red-950/50 border-red-500/80 text-red-200"
                        : "bg-slate-950/80 border-slate-800 hover:border-cyan-500 text-slate-200"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs md:text-sm font-semibold">{dec.action}</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                        {isExecuted ? "EXECUTED" : "SELECT"}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Real-time Physiological Feedback HUD */}
          <AnimatePresence>
            {decisionFeedback && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className={`p-4 rounded-2xl border ${
                  decisionFeedback.safe
                    ? "bg-emerald-950/60 border-emerald-500/50 text-emerald-200"
                    : "bg-red-950/60 border-red-500/50 text-red-200"
                } shadow-2xl`}
              >
                <div className="flex items-center justify-between mb-1.5 font-mono text-xs font-bold uppercase">
                  <span>{decisionFeedback.safe ? "Patient Response: Favorable" : "CRITICAL CONTRAINDICATION"}</span>
                  <span>{decisionFeedback.safe ? "+40 Reasoning Pts" : "-100 Penalty"}</span>
                </div>
                <p className="text-xs font-mono font-medium">{decisionFeedback.effect}</p>
                <p className="text-[11px] text-slate-300 mt-2 italic">{decisionFeedback.feedback}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
