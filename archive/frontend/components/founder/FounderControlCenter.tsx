"use client";

import React, { useState } from "react";
import {
  Sparkles,
  Presentation,
  Scale,
  Zap,
  ShieldCheck,
  DollarSign,
  Activity,
  ChevronRight,
  Lock,
} from "lucide-react";
import { FounderPitchEngine } from "./FounderPitchEngine";
import { JudgeIntelligenceSimulator } from "./JudgeIntelligenceSimulator";
import { FinalDemoController } from "./FinalDemoController";
import { CompetitiveMatrixView } from "./CompetitiveMatrixView";
import { StartupBusinessLayer } from "./StartupBusinessLayer";
import { SystemTelemetryCard } from "./SystemTelemetryCard";
import { FounderSubTab, NavigationMode } from "@/lib/types";

interface FounderControlCenterProps {
  onNavigateToMode: (mode: NavigationMode) => void;
}

export const FounderControlCenter: React.FC<FounderControlCenterProps> = ({
  onNavigateToMode,
}) => {
  const [activeTab, setActiveTab] = useState<FounderSubTab>("pitch");
  const [isOfflineMode, setIsOfflineMode] = useState(false);

  const tabs: { id: FounderSubTab; label: string; icon: React.ReactNode; badge?: string }[] = [
    {
      id: "pitch",
      label: "Founder Pitch Deck",
      icon: <Presentation className="w-4 h-4" />,
      badge: "10 Slides",
    },
    {
      id: "judge_qa",
      label: "Judge Q&A Simulator",
      icon: <Scale className="w-4 h-4" />,
      badge: "11 Hardball",
    },
    {
      id: "demo_controller",
      label: "Final Demo Controller",
      icon: <Zap className="w-4 h-4 text-cyan-400" />,
      badge: "8 Scenes",
    },
    {
      id: "competitive",
      label: "Competitive Matrix",
      icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
      badge: "Moats",
    },
    {
      id: "business",
      label: "Business & TAM",
      icon: <DollarSign className="w-4 h-4 text-purple-400" />,
      badge: "$4.8B",
    },
    {
      id: "telemetry",
      label: "AI Telemetry & Cache",
      icon: <Activity className="w-4 h-4 text-amber-400" />,
      badge: isOfflineMode ? "Offline Lock" : "Live API",
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8 animate-in fade-in duration-300">
      {/* Top Banner & Mode Identifier */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-cyan-500/20 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-1 rounded-lg bg-gradient-to-r from-cyan-950 to-blue-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5 shadow-[0_0_15px_rgba(0,242,254,0.2)]">
              <Sparkles className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
              STAGE-J: FOUNDER MODE & COMPETITION WINNING LAYER
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              INVESTOR & HACKATHON READY
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-wide">
            MedicalPlab Founder Command Center
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-300 font-sans max-w-3xl leading-relaxed">
            A comprehensive startup presentation system designed to win hackathons and convince Tier-1 medical & AI investors.
          </p>
        </div>

        {/* Global Offline Fallback Quick Indicator */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <button
            onClick={() => setIsOfflineMode(!isOfflineMode)}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-mono border transition-all ${
              isOfflineMode
                ? "bg-emerald-950 border-emerald-500 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)]"
                : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
            }`}
            title="Toggle offline presentation resilience mode"
          >
            <Lock className="w-3.5 h-3.5" />
            <span>{isOfflineMode ? "Offline Fallback (Active)" : "Live API Connected"}</span>
          </button>
        </div>
      </div>

      {/* Sub-Tab Navigation Bar */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 p-1.5 rounded-2xl bg-slate-950/80 border border-slate-800">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-mono font-bold whitespace-nowrap transition-all ${
                isActive
                  ? "bg-cyan-500/20 text-cyan-300 border border-cyan-400/50 shadow-[0_0_15px_rgba(0,242,254,0.25)]"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  className={`px-1.5 py-0.2 text-[9px] rounded font-mono ${
                    isActive
                      ? "bg-cyan-400/20 text-cyan-200"
                      : "bg-slate-800 text-slate-400"
                  }`}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Active Tab View Rendering */}
      <div className="pt-2">
        {activeTab === "pitch" && <FounderPitchEngine />}

        {activeTab === "judge_qa" && <JudgeIntelligenceSimulator />}

        {activeTab === "demo_controller" && (
          <FinalDemoController
            onNavigateToScene={onNavigateToMode}
            isOfflineMode={isOfflineMode}
            onToggleOfflineMode={() => setIsOfflineMode(!isOfflineMode)}
          />
        )}

        {activeTab === "competitive" && <CompetitiveMatrixView />}

        {activeTab === "business" && <StartupBusinessLayer />}

        {activeTab === "telemetry" && (
          <SystemTelemetryCard
            isOfflineMode={isOfflineMode}
            onToggleOfflineMode={() => setIsOfflineMode(!isOfflineMode)}
          />
        )}
      </div>
    </div>
  );
};
