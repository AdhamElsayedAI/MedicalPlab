"use client";

import React, { useState } from "react";
import {
  Activity,
  Compass,
  TrendingUp,
  Building2,
  Calculator,
  BookOpen,
  ShieldAlert,
  ShieldCheck,
  Zap,
  ArrowRight,
  Layers,
  Sparkles,
} from "lucide-react";
import { ValidationSubTab, NavigationMode } from "@/lib/types";
import { StudentJourneySimulator } from "./StudentJourneySimulator";
import { OutcomeMetricsEngine } from "./OutcomeMetricsEngine";
import { InstitutionDashboard } from "./InstitutionDashboard";
import { AIROICalculator } from "./AIROICalculator";
import { ImpactStoryMode } from "./ImpactStoryMode";
import { JudgeImpactDefense } from "./JudgeImpactDefense";
import { ValidationSafeMode } from "./ValidationSafeMode";

interface ValidationHubProps {
  onNavigateToMode?: (mode: NavigationMode) => void;
}

export const ValidationHub: React.FC<ValidationHubProps> = ({ onNavigateToMode }) => {
  const [activeTab, setActiveTab] = useState<ValidationSubTab>("journey");

  const navTabs: { id: ValidationSubTab; label: string; icon: React.ReactNode; badge?: string }[] = [
    { id: "journey", label: "Student Journey", icon: <Compass className="w-4 h-4 text-cyan-400" />, badge: "4-PHASE" },
    { id: "outcomes", label: "Outcome Metrics", icon: <TrendingUp className="w-4 h-4 text-emerald-400" />, badge: "BEFORE/AFTER" },
    { id: "institution", label: "Institution Analytics", icon: <Building2 className="w-4 h-4 text-purple-400" />, badge: "B2B DEANERY" },
    { id: "roi", label: "ROI Calculator", icon: <Calculator className="w-4 h-4 text-amber-400" />, badge: "HEALTH ECON" },
    { id: "story", label: "Impact Stories", icon: <BookOpen className="w-4 h-4 text-cyan-300" />, badge: "CINEMATIC" },
    { id: "defense", label: "Judge Defense", icon: <ShieldAlert className="w-4 h-4 text-rose-400" />, badge: "Q&A" },
    { id: "safe_mode", label: "Safe Mode", icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />, badge: "0-NET" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Cockpit Header */}
      <div className="p-6 rounded-3xl border border-cyan-500/30 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 relative overflow-hidden shadow-[0_0_50px_rgba(0,242,254,0.08)]">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 -mb-8 -ml-8 w-64 h-64 bg-purple-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-xs font-mono font-black px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 tracking-wider">
                STAGE-M IMPACT ENGINE
              </span>
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                UK PLAB &amp; GMC CLINICAL TRIAL READY
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30">
                [Prototype Projection &amp; Demo Simulation]
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
              Real-World Validation &amp;{" "}
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-emerald-300 to-teal-200">
                Clinical Impact Layer
              </span>
            </h1>

            <p className="text-sm text-slate-300 max-w-3xl mt-2 leading-relaxed">
              Demonstrating measurable educational outcomes, multi-tenant NHS hospital deanery telemetry, health economics ROI, and transparent adversarial judge defenses.
            </p>
          </div>

          {/* Quick Jump Action Bar */}
          <div className="flex items-center gap-2.5 shrink-0">
            {onNavigateToMode && (
              <>
                <button
                  onClick={() => onNavigateToMode("battle")}
                  className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-mono font-bold bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-cyan-500/30 transition-all"
                >
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Final Battle</span>
                </button>

                <button
                  onClick={() => onNavigateToMode("anatomy")}
                  className="flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-mono font-bold bg-cyan-500 hover:bg-cyan-400 text-black shadow-[0_0_15px_rgba(0,242,254,0.35)] transition-all"
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>3D Anatomy Lab</span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* 4 Executive Metric Badges */}
        <div className="mt-6 pt-5 border-t border-slate-800/80 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">First-Attempt Pass Rate</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-xl font-bold font-mono text-emerald-400">+30.8%</span>
              <span className="text-[10px] font-mono text-slate-400">[Projection]</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Bedside Error Drop</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-xl font-bold font-mono text-cyan-400">-97.2%</span>
              <span className="text-[10px] font-mono text-slate-400">[Simulation]</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Trust Net ROI Multiplier</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-xl font-bold font-mono text-purple-400">8.5x ROI</span>
              <span className="text-[10px] font-mono text-slate-400">[Target]</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Study Time Saved</span>
            <div className="flex items-baseline gap-2 mt-0.5">
              <span className="text-xl font-bold font-mono text-amber-400">-48.2%</span>
              <span className="text-[10px] font-mono text-slate-400">[Projection]</span>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Sub-Tabs Ribbon */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-800/80">
        {navTabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-mono font-bold transition-all whitespace-nowrap border ${
                isActive
                  ? "bg-gradient-to-r from-cyan-500 to-blue-600 text-black border-cyan-400 shadow-[0_0_15px_rgba(0,242,254,0.35)]"
                  : "bg-slate-950/80 text-slate-400 border-slate-800 hover:text-white hover:bg-slate-900"
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  className={`text-[9px] px-1.5 py-0.2 rounded font-bold ${
                    isActive ? "bg-black/30 text-white" : "bg-slate-900 text-slate-500 border border-slate-800"
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Dynamic Sub-Tab View Rendering */}
      <div className="min-h-[500px]">
        {activeTab === "journey" && (
          <StudentJourneySimulator onNavigateToMode={onNavigateToMode} />
        )}
        {activeTab === "outcomes" && <OutcomeMetricsEngine />}
        {activeTab === "institution" && <InstitutionDashboard />}
        {activeTab === "roi" && <AIROICalculator />}
        {activeTab === "story" && <ImpactStoryMode />}
        {activeTab === "defense" && <JudgeImpactDefense />}
        {activeTab === "safe_mode" && <ValidationSafeMode />}
      </div>
    </div>
  );
};
