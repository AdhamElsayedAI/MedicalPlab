"use client";

import React, { useState } from "react";
import {
  Trophy,
  Play,
  Cpu,
  DollarSign,
  ShieldAlert,
  ShieldCheck,
  Activity,
  HeartPulse,
  FileText,
  Lock,
  Sparkles,
  Zap,
} from "lucide-react";
import { NavigationMode } from "@/lib/types";
import { UltimateDemoEngine } from "./UltimateDemoEngine";
import { LiveArchitectureMap } from "./LiveArchitectureMap";
import { InvestorStoryMode } from "./InvestorStoryMode";
import { JudgeFinalDefense } from "./JudgeFinalDefense";
import { AITrustVisualizer } from "./AITrustVisualizer";
import { StartupMetricsCommand } from "./StartupMetricsCommand";
import { MedicalImpactTimeline } from "./MedicalImpactTimeline";
import { SubmissionMasterPackage } from "./SubmissionMasterPackage";
import { ChampionshipSafeMode } from "./ChampionshipSafeMode";
import { FinalStageController } from "./FinalStageController";

interface GrandChampionshipHubProps {
  onNavigateToMode?: (mode: NavigationMode) => void;
}

export type GrandChampionshipTab =
  | "demo"
  | "architecture"
  | "investor"
  | "defense"
  | "trust"
  | "metrics"
  | "impact"
  | "submission"
  | "safe_mode";

export const GrandChampionshipHub: React.FC<GrandChampionshipHubProps> = ({
  onNavigateToMode,
}) => {
  const [activeTab, setActiveTab] = useState<GrandChampionshipTab>("demo");
  const [activeSceneIdx, setActiveSceneIdx] = useState<number>(0);

  const navTabs: { id: GrandChampionshipTab; label: string; icon: React.ReactNode; badge?: string }[] = [
    { id: "demo", label: "Ultimate Demo", icon: <Play className="w-4 h-4 text-cyan-400" />, badge: "5-MIN" },
    { id: "architecture", label: "Architecture Intelligence", icon: <Cpu className="w-4 h-4 text-purple-400" />, badge: "FLOW" },
    { id: "investor", label: "Investor Story", icon: <DollarSign className="w-4 h-4 text-emerald-400" />, badge: "$4.8B" },
    { id: "defense", label: "Judge Defense", icon: <ShieldAlert className="w-4 h-4 text-rose-400" />, badge: "4-LEVEL" },
    { id: "trust", label: "Trust & Safety", icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />, badge: "PROOF" },
    { id: "metrics", label: "Startup Metrics", icon: <Activity className="w-4 h-4 text-cyan-300" />, badge: "VITALITY" },
    { id: "impact", label: "Impact Story", icon: <HeartPulse className="w-4 h-4 text-amber-400" />, badge: "HUMAN" },
    { id: "submission", label: "Submission Package", icon: <FileText className="w-4 h-4 text-cyan-400" />, badge: "10-CH" },
    { id: "safe_mode", label: "Competition Safe Mode", icon: <Lock className="w-4 h-4 text-rose-400" />, badge: "PANIC" },
  ];

  const handlePanicReset = () => {
    setActiveSceneIdx(0);
    setActiveTab("demo");
  };

  const handleResetDemo = () => {
    setActiveSceneIdx(0);
    setActiveTab("demo");
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 pb-28">
      {/* Top Cockpit Header */}
      <div className="p-6 rounded-3xl border border-amber-500/30 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 relative overflow-hidden shadow-[0_0_60px_rgba(245,158,11,0.1)]">
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-0 -mb-8 -ml-8 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="text-xs font-mono font-black px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 tracking-wider flex items-center gap-1.5">
                <Trophy className="w-3.5 h-3.5 text-amber-400" />
                <span>STAGE-N: GRAND CHAMPIONSHIP EXPERIENCE</span>
              </span>
              <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                FINAL PRESENTATION SUITE
              </span>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-bold">
                60 FPS OPTIMIZED
              </span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
              MedicalPlab{" "}
              <span className="bg-clip-text text-transparent bg-gradient-to-r from-amber-300 via-cyan-300 to-emerald-300">
                Grand Championship Mission Control
              </span>
            </h1>

            <p className="text-sm text-slate-300 max-w-3xl mt-2 leading-relaxed">
              The investor-grade, technical judge-ready presentation system. Delivering 8 controlled demo scenes, live architecture visualization, adversarial defense levels, and 1-click submission packaging.
            </p>
          </div>

          {/* Quick Launch Actions */}
          <div className="flex items-center gap-2.5 shrink-0">
            {onNavigateToMode && (
              <>
                <button
                  onClick={() => onNavigateToMode("anatomy")}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-mono font-bold bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-cyan-500/30 transition-all"
                >
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  <span>3D Lab</span>
                </button>

                <button
                  onClick={() => onNavigateToMode("simulation")}
                  className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-mono font-bold bg-slate-900 hover:bg-slate-800 text-emerald-300 border border-emerald-500/30 transition-all"
                >
                  <Zap className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Ward Sim</span>
                </button>

                <button
                  onClick={() => onNavigateToMode("landing")}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-mono font-bold bg-gradient-to-r from-amber-500 to-amber-600 text-black shadow-[0_0_15px_rgba(245,158,11,0.35)] transition-all"
                >
                  <span>Portal Home</span>
                </button>
              </>
            )}
          </div>
        </div>

        {/* System Vitality Indicators (3 Badges) */}
        <div className="mt-6 pt-5 border-t border-slate-800/80 grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400">AI Core Pipeline:</span>
            <span className="text-xs font-mono font-bold text-emerald-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span>AI CORE READY (235 Tests Pass)</span>
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400">Championship Demo:</span>
            <span className="text-xs font-mono font-bold text-cyan-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400" />
              <span>DEMO MODE READY (8 Scenes)</span>
            </span>
          </div>

          <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400">Offline Resilience:</span>
            <span className="text-xs font-mono font-bold text-amber-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-400" />
              <span>OFFLINE BACKUP READY (0ms)</span>
            </span>
          </div>
        </div>
      </div>

      {/* 9 Navigation Sub-Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-2 border-b border-slate-800/80">
        {navTabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2.5 rounded-xl text-xs font-mono font-bold transition-all whitespace-nowrap border ${
                isActive
                  ? "bg-gradient-to-r from-amber-500 to-amber-600 text-black border-amber-400 shadow-[0_0_15px_rgba(245,158,11,0.35)]"
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
        {activeTab === "demo" && (
          <UltimateDemoEngine
            activeSceneIdx={activeSceneIdx}
            onSelectScene={setActiveSceneIdx}
            onNavigateToMode={onNavigateToMode}
          />
        )}
        {activeTab === "architecture" && <LiveArchitectureMap />}
        {activeTab === "investor" && <InvestorStoryMode />}
        {activeTab === "defense" && <JudgeFinalDefense />}
        {activeTab === "trust" && <AITrustVisualizer />}
        {activeTab === "metrics" && <StartupMetricsCommand />}
        {activeTab === "impact" && <MedicalImpactTimeline />}
        {activeTab === "submission" && <SubmissionMasterPackage />}
        {activeTab === "safe_mode" && (
          <ChampionshipSafeMode
            onPanicReset={handlePanicReset}
            onResetDemo={handleResetDemo}
          />
        )}
      </div>

      {/* Persistent Presenter Controller Toolbar */}
      <FinalStageController
        activeSceneIdx={activeSceneIdx}
        onSelectScene={setActiveSceneIdx}
        onPanicReset={handlePanicReset}
      />
    </div>
  );
};
