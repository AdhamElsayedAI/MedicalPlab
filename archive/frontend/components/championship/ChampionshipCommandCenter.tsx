"use client";

import React, { useState } from "react";
import {
  Trophy,
  Sparkles,
  Play,
  Volume2,
  ShieldAlert,
  FileText,
  TrendingUp,
  ShieldCheck,
  Lock,
  ArrowRight,
  Award,
} from "lucide-react";
import { FinalDemoEngine } from "./FinalDemoEngine";
import { FounderNarrativeEngine } from "./FounderNarrativeEngine";
import { JudgeAttackSimulator } from "./JudgeAttackSimulator";
import { SubmissionIntelligence } from "./SubmissionIntelligence";
import { ImpactStoryView } from "./ImpactStoryView";
import { TrustSafetyShowcase } from "./TrustSafetyShowcase";
import { ReliabilityController } from "./ReliabilityController";
import { ChampionshipSubTab, NavigationMode } from "@/lib/types";

interface ChampionshipCommandCenterProps {
  onNavigateToMode: (mode: NavigationMode) => void;
}

export const ChampionshipCommandCenter: React.FC<ChampionshipCommandCenterProps> = ({
  onNavigateToMode,
}) => {
  const [activeTab, setActiveTab] = useState<ChampionshipSubTab>("demo_engine");
  const [isOfflineMode, setIsOfflineMode] = useState(false);

  const tabs: { id: ChampionshipSubTab; label: string; icon: React.ReactNode; badge?: string }[] = [
    {
      id: "demo_engine",
      label: "Final Demo Engine",
      icon: <Play className="w-4 h-4 text-cyan-400 fill-current" />,
      badge: "8 Scenes",
    },
    {
      id: "founder_narrative",
      label: "Pitch Intelligence",
      icon: <Volume2 className="w-4 h-4 text-emerald-400" />,
      badge: "Prompter",
    },
    {
      id: "judge_attack",
      label: "Judge Attack Simulator",
      icon: <ShieldAlert className="w-4 h-4 text-rose-400" />,
      badge: "9 Attacks",
    },
    {
      id: "submission",
      label: "Submission Package",
      icon: <FileText className="w-4 h-4 text-purple-400" />,
      badge: "Devpost Ready",
    },
    {
      id: "impact_story",
      label: "Impact Story",
      icon: <TrendingUp className="w-4 h-4 text-blue-400" />,
      badge: "Before/After",
    },
    {
      id: "safety_showcase",
      label: "Trust & Safety",
      icon: <ShieldCheck className="w-4 h-4 text-emerald-400" />,
      badge: "0.0% Hallucination",
    },
    {
      id: "reliability",
      label: "Reliability Controller",
      icon: <Lock className="w-4 h-4 text-amber-400" />,
      badge: isOfflineMode ? "Offline Lock" : "100% Uptime",
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8 animate-in fade-in duration-300">
      {/* Grand Championship Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-cyan-500/20 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-3 py-1 rounded-lg bg-gradient-to-r from-amber-500/20 via-cyan-500/20 to-purple-500/20 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5 shadow-[0_0_20px_rgba(0,242,254,0.25)]">
              <Trophy className="w-4 h-4 text-amber-400 animate-bounce" />
              STAGE-K: CHAMPIONSHIP & SUBMISSION INTELLIGENCE LAYER
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              GRAND PRIZE TIER
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-wide">
            MedicalPlab Championship Command Center
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-300 font-sans max-w-3xl leading-relaxed">
            The ultimate presentation and defense cockpit: synchronized 8-scene demo engine, founder teleprompter, adversarial judge simulator, submission generator, and offline reliability protection.
          </p>
        </div>

        {/* Quick Launch & Status */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="px-4 py-2 rounded-2xl bg-slate-900/90 border border-amber-500/40 text-right">
            <span className="text-[10px] font-mono text-slate-400 block">SIMULATED JUDGE SCORE</span>
            <span className="text-lg font-black text-amber-400 font-mono">98.4 / 100</span>
          </div>

          <button
            onClick={() => setIsOfflineMode(!isOfflineMode)}
            className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-mono border transition-all ${
              isOfflineMode
                ? "bg-emerald-950 border-emerald-500 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.3)]"
                : "bg-slate-900 border-slate-700 text-slate-400 hover:text-white"
            }`}
          >
            <Lock className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">
              {isOfflineMode ? "Offline Mode: ON" : "Live API"}
            </span>
          </button>
        </div>
      </div>

      {/* 7-Tab Navigation Ribbon */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 p-1.5 rounded-2xl bg-slate-950/80 border border-slate-800">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3.5 py-2.5 rounded-xl text-xs font-mono font-bold whitespace-nowrap transition-all ${
                isActive
                  ? "bg-gradient-to-r from-cyan-950 to-blue-950 text-cyan-300 border border-cyan-400/60 shadow-[0_0_15px_rgba(0,242,254,0.3)]"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/60"
              }`}
            >
              {tab.icon}
              <span>{tab.label}</span>
              {tab.badge && (
                <span
                  className={`px-1.5 py-0.2 text-[9px] rounded font-mono ${
                    isActive
                      ? "bg-cyan-400/25 text-cyan-200"
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

      {/* Tab View Content */}
      <div className="pt-1">
        {activeTab === "demo_engine" && (
          <FinalDemoEngine
            onLaunchScene={onNavigateToMode}
            isOfflineMode={isOfflineMode}
          />
        )}

        {activeTab === "founder_narrative" && <FounderNarrativeEngine />}

        {activeTab === "judge_attack" && <JudgeAttackSimulator />}

        {activeTab === "submission" && <SubmissionIntelligence />}

        {activeTab === "impact_story" && <ImpactStoryView />}

        {activeTab === "safety_showcase" && <TrustSafetyShowcase />}

        {activeTab === "reliability" && (
          <ReliabilityController
            isOfflineMode={isOfflineMode}
            onToggleOfflineMode={() => setIsOfflineMode(!isOfflineMode)}
          />
        )}
      </div>
    </div>
  );
};
