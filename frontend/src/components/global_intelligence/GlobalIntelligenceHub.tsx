"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import GlobalMedicalBrain from "./GlobalMedicalBrain";
import MedicalAIMarketplace from "./MedicalAIMarketplace";
import ResearchIntelligence from "./ResearchIntelligence";
import ClinicalSimulationUniverse from "./ClinicalSimulationUniverse";
import PhysicianDigitalTwin from "./PhysicianDigitalTwin";
import GlobalHealthcareAnalytics from "./GlobalHealthcareAnalytics";
import AIGovernanceCenter from "./AIGovernanceCenter";
import MedicalAPIPlatform from "./MedicalAPIPlatform";
import KnowledgeSynchronization from "./KnowledgeSynchronization";
import MedicalPlabAcademy from "./MedicalPlabAcademy";
import StageXDemoController from "./StageXDemoController";

export default function GlobalIntelligenceHub() {
  const [activeModule, setActiveModule] = useState<string>("brain");
  const [showDemoController, setShowDemoController] = useState<boolean>(true);

  const modules = [
    { id: "brain", name: "Knowledge Brain", icon: "🧠", subtitle: "6-Step Diagnostic Flow" },
    { id: "marketplace", name: "AI Marketplace", icon: "🌐", subtitle: "Ecosystem Registry" },
    { id: "research", name: "Research Pipeline", icon: "🔬", subtitle: "Translational Synthesis" },
    { id: "simulation", name: "Hospital Sim", icon: "🏥", subtitle: "Physiological Twin" },
    { id: "twin", name: "Physician Twin", icon: "🩺", subtitle: "Cognitive Profile" },
    { id: "analytics", name: "Global Analytics", icon: "📊", subtitle: "Enterprise Hospitals" },
    { id: "governance", name: "AI Governance", icon: "🛡️", subtitle: "Trust & Safety Shield" },
    { id: "api", name: "Medical API", icon: "⚡", subtitle: "Developer Ecosystem" },
    { id: "sync", name: "Knowledge Sync", icon: "🔄", subtitle: "Autonomous Updates" },
    { id: "academy", name: "Global Academy", icon: "🎓", subtitle: "Degrees & CME" }
  ];

  const handleSelectModuleFromDemo = (modId: string) => {
    setActiveModule(modId);
  };

  return (
    <div className="min-h-screen bg-[#070b12] text-slate-100 p-4 md:p-8 space-y-6">
      {/* Top Global Command Center Header */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-slate-950 border border-cyan-500/30 rounded-3xl p-6 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-80 h-80 bg-blue-600/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col xl:flex-row xl:items-center justify-between gap-6 relative z-10">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-pulse shadow-sm shadow-cyan-400" />
              <span className="text-xs font-mono uppercase tracking-widest text-cyan-400 font-semibold">
                Stage-X Visionary Experience • Global Intelligence Layer
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-800 text-cyan-300">
                Core Ecosystem Online
              </span>
            </div>

            <h1 className="text-2xl md:text-4xl font-extrabold text-white tracking-tight leading-tight">
              MedicalPlab Global Intelligence
              <span className="block text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-teal-300 to-blue-400 text-xl md:text-2xl mt-1 font-semibold">
                The Intelligence Infrastructure Layer of Global Medicine
              </span>
            </h1>

            <p className="text-xs md:text-sm text-slate-400 mt-2 max-w-3xl leading-relaxed">
              Unifying clinical reasoning, evidence provenance, hospital flight simulations, and continuous medical education into a single enterprise infrastructure standard.
            </p>
          </div>

          {/* System Health Indicators & Demo Launcher */}
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
            {/* Telemetry Capsule */}
            <div className="bg-slate-950/90 border border-slate-800 rounded-2xl p-3.5 space-y-2 text-xs font-mono min-w-[240px]">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Global Knowledge Mesh:</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  ACTIVE (99.8%)
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">PhysioSim Engine:</span>
                <span className="text-cyan-400 font-bold">60 FPS DETERMINISTIC</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Inference Latency:</span>
                <span className="text-teal-400 font-bold">82ms SLA</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Safety & Governance:</span>
                <span className="text-indigo-400 font-bold">ZERO OMISSION</span>
              </div>
            </div>

            {/* Executive Pitch Experience Toggle Button */}
            <button
              onClick={() => setShowDemoController(!showDemoController)}
              className={`px-4 py-4 rounded-2xl font-bold font-mono text-xs transition-all shadow-xl flex flex-col items-center justify-center gap-1 ${
                showDemoController
                  ? "bg-cyan-500 text-black shadow-cyan-500/20"
                  : "bg-slate-900 border border-cyan-500/40 text-cyan-300 hover:bg-slate-800"
              }`}
            >
              <span className="text-base">🎬</span>
              <span>{showDemoController ? "Hide Pitch Controller" : "Launch Executive Demo"}</span>
            </button>
          </div>
        </div>

        {/* Global Macro Telemetry Strip */}
        <div className="mt-6 pt-5 border-t border-slate-800/80 grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Verified Node Triplets</span>
            <span className="text-xl font-bold font-mono text-cyan-400">14.8M Triples</span>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Affiliated Hospitals</span>
            <span className="text-xl font-bold font-mono text-blue-400">1,420 Centers</span>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Active Clinicians</span>
            <span className="text-xl font-bold font-mono text-teal-400">42,500 MDs</span>
          </div>
          <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Daily Clinical Inferences</span>
            <span className="text-xl font-bold font-mono text-emerald-400">2.1M / Day</span>
          </div>
        </div>
      </div>

      {/* Executive Demo Presentation Controller */}
      <AnimatePresence>
        {showDemoController && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3 }}
          >
            <StageXDemoController
              onSelectModule={handleSelectModuleFromDemo}
              activeModuleId={activeModule}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* 10-Module Command Navigation Tabs */}
      <div className="bg-slate-900/80 backdrop-blur-md border border-slate-800 rounded-2xl p-2.5 shadow-xl">
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 custom-scrollbar">
          {modules.map((m) => {
            const isActive = activeModule === m.id;
            return (
              <button
                key={m.id}
                onClick={() => setActiveModule(m.id)}
                className={`text-left px-3.5 py-2.5 rounded-xl text-xs font-mono transition-all whitespace-nowrap flex items-center gap-2 border ${
                  isActive
                    ? "bg-cyan-500 text-black font-bold border-cyan-400 shadow-md shadow-cyan-500/20"
                    : "bg-slate-950/60 text-slate-400 border-slate-800/80 hover:border-slate-700 hover:text-white"
                }`}
              >
                <span>{m.icon}</span>
                <div className="text-left">
                  <div className="font-semibold">{m.name}</div>
                  <div className={`text-[10px] ${isActive ? "text-slate-900" : "text-slate-500"}`}>
                    {m.subtitle}
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active Module Viewport */}
      <div className="transition-all duration-300">
        {activeModule === "brain" && <GlobalMedicalBrain />}
        {activeModule === "marketplace" && <MedicalAIMarketplace />}
        {activeModule === "research" && <ResearchIntelligence />}
        {activeModule === "simulation" && <ClinicalSimulationUniverse />}
        {activeModule === "twin" && <PhysicianDigitalTwin />}
        {activeModule === "analytics" && <GlobalHealthcareAnalytics />}
        {activeModule === "governance" && <AIGovernanceCenter />}
        {activeModule === "api" && <MedicalAPIPlatform />}
        {activeModule === "sync" && <KnowledgeSynchronization />}
        {activeModule === "academy" && <MedicalPlabAcademy />}
      </div>
    </div>
  );
}
