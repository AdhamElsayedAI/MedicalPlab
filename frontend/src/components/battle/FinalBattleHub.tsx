"use client";

import React, { useState } from "react";
import {
  Swords,
  Play,
  Volume2,
  ShieldAlert,
  Award,
  BrainCircuit,
  BookOpen,
  AlertTriangle,
  FileText,
  Activity,
  Lock,
  Sparkles,
} from "lucide-react";
import { FinalDemoMaster } from "./FinalDemoMaster";
import { FounderPitchTrainer } from "./FounderPitchTrainer";
import { JudgeArena } from "./JudgeArena";
import { LiveJudgePanel } from "./LiveJudgePanel";
import { FounderCoach } from "./FounderCoach";
import { DefenseLibrary } from "./DefenseLibrary";
import { DemoFailureDrill } from "./DemoFailureDrill";
import { SubmissionPro } from "./SubmissionPro";
import { PresentationAnalytics } from "./PresentationAnalytics";
import { CompetitionSafeMode } from "./CompetitionSafeMode";
import { BattleSubTab, NavigationMode } from "@/lib/types";

interface FinalBattleHubProps {
  onNavigateToMode: (mode: NavigationMode) => void;
}

export const FinalBattleHub: React.FC<FinalBattleHubProps> = ({
  onNavigateToMode,
}) => {
  const [activeTab, setActiveTab] = useState<BattleSubTab>("demo_master");
  const [isOfflineMode, setIsOfflineMode] = useState(false);

  const tabs: {
    id: BattleSubTab;
    label: string;
    icon: React.ReactNode;
    badge?: string;
  }[] = [
    {
      id: "demo_master",
      label: "Demo Master",
      icon: <Play className="w-4 h-4 text-cyan-400 fill-current" />,
      badge: "8 Scenes",
    },
    {
      id: "pitch_trainer",
      label: "Pitch Trainer",
      icon: <Volume2 className="w-4 h-4 text-emerald-400" />,
      badge: "Rehearsal",
    },
    {
      id: "judge_arena",
      label: "Judge Arena",
      icon: <ShieldAlert className="w-4 h-4 text-rose-400" />,
      badge: "12 Scenarios",
    },
    {
      id: "judge_panel",
      label: "Judge Panel",
      icon: <Award className="w-4 h-4 text-amber-400" />,
      badge: "98.5 Score",
    },
    {
      id: "founder_coach",
      label: "Founder Coach",
      icon: <BrainCircuit className="w-4 h-4 text-purple-400" />,
      badge: "Strategy",
    },
    {
      id: "defense_library",
      label: "Defense Library",
      icon: <BookOpen className="w-4 h-4 text-blue-400" />,
      badge: "6 Domains",
    },
    {
      id: "failure_drills",
      label: "Failure Drills",
      icon: <AlertTriangle className="w-4 h-4 text-orange-400" />,
      badge: "Stress Test",
    },
    {
      id: "submission_pro",
      label: "Submission Pro",
      icon: <FileText className="w-4 h-4 text-teal-400" />,
      badge: "80/80 Audit",
    },
    {
      id: "presentation_analytics",
      label: "Analytics",
      icon: <Activity className="w-4 h-4 text-pink-400" />,
      badge: "Pacing",
    },
    {
      id: "safe_mode",
      label: "Safe Mode",
      icon: <Lock className="w-4 h-4 text-emerald-400" />,
      badge: isOfflineMode ? "Locked ON" : "100% Ready",
    },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-8 animate-in fade-in duration-300">
      {/* Grand Battle Station Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-cyan-500/20 pb-6">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-3 py-1 rounded-lg bg-gradient-to-r from-red-500/20 via-cyan-500/20 to-amber-500/20 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5 shadow-[0_0_20px_rgba(0,242,254,0.25)]">
              <Swords className="w-4 h-4 text-cyan-400 animate-pulse" />
              STAGE-L: FINAL BATTLE & JUDGE MASTERY LAYER
            </span>
            <span className="text-xs font-mono text-amber-400 font-bold">
              FINAL CHAMPIONSHIP STATION
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black text-white tracking-wide">
            MedicalPlab Final Battle Command Center
          </h1>
          <p className="mt-1 text-xs sm:text-sm text-slate-300 font-sans max-w-3xl leading-relaxed">
            The complete competition-winning operating cockpit: cinematic 8-scene demo master, pitch rehearsal trainer, adversarial judge arena, simulated 3-judge panel, defense encyclopedia, stress failure drills, and zero-network safe mode.
          </p>
        </div>

        {/* Top Badges & Safe Mode Switch */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <div className="px-4 py-2 rounded-2xl bg-slate-900/90 border border-cyan-500/30 text-right">
            <span className="text-[10px] font-mono text-slate-400 block">CHAMPIONSHIP VERDICT</span>
            <span className="text-base font-black text-emerald-400 font-mono">GRAND CHAMPION</span>
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
              {isOfflineMode ? "Safe Mode: ON" : "Live API"}
            </span>
          </button>
        </div>
      </div>

      {/* Battle Navigation Ribbon */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-2 p-1.5 rounded-2xl bg-slate-950/80 border border-slate-800">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-3 py-2 rounded-xl text-xs font-mono font-bold whitespace-nowrap transition-all ${
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
        {activeTab === "demo_master" && (
          <FinalDemoMaster
            onLaunchScene={onNavigateToMode}
            isOfflineMode={isOfflineMode}
          />
        )}

        {activeTab === "pitch_trainer" && <FounderPitchTrainer />}

        {activeTab === "judge_arena" && <JudgeArena />}

        {activeTab === "judge_panel" && <LiveJudgePanel />}

        {activeTab === "founder_coach" && <FounderCoach />}

        {activeTab === "defense_library" && <DefenseLibrary />}

        {activeTab === "failure_drills" && <DemoFailureDrill />}

        {activeTab === "submission_pro" && <SubmissionPro />}

        {activeTab === "presentation_analytics" && <PresentationAnalytics />}

        {activeTab === "safe_mode" && (
          <CompetitionSafeMode
            isOfflineMode={isOfflineMode}
            onToggleOfflineMode={() => setIsOfflineMode(!isOfflineMode)}
          />
        )}
      </div>
    </div>
  );
};
