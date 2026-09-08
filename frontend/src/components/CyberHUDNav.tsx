"use client";

import React from "react";
import {
  Activity,
  Cpu,
  Layers,
  GraduationCap,
  ShieldCheck,
  Stethoscope,
  Terminal,
  Play,
  UserCheck,
  Sparkles,
} from "lucide-react";

import { NavigationMode, UserRole } from "@/lib/types";

interface CyberHUDNavProps {
  currentMode: NavigationMode;
  onSelectMode: (mode: NavigationMode) => void;
  userRole: UserRole;
  onSwitchRole: (role: UserRole) => void;
  onOpenPipelineModal: () => void;
  onStartDemoJourney: () => void;
}

export const CyberHUDNav: React.FC<CyberHUDNavProps> = ({
  currentMode,
  onSelectMode,
  userRole,
  onSwitchRole,
  onOpenPipelineModal,
  onStartDemoJourney,
}) => {
  const navItems: { mode: NavigationMode; label: string; icon: React.ReactNode }[] = [
    { mode: "landing", label: "Studio Portal", icon: <Cpu className="w-4 h-4" /> },
    { mode: "anatomy", label: "3D Anatomy Lab", icon: <Layers className="w-4 h-4" /> },
    { mode: "tutor", label: "AI Medical Tutor", icon: <Stethoscope className="w-4 h-4" /> },
    { mode: "quiz", label: "Clinical Quiz", icon: <GraduationCap className="w-4 h-4" /> },
    { mode: "simulation", label: "Emergency Sim", icon: <Activity className="w-4 h-4" /> },
    { mode: "command_center", label: "Command Center", icon: <Terminal className="w-4 h-4" /> },
    { mode: "admin", label: "Admin Analytics", icon: <UserCheck className="w-4 h-4" /> },
    { mode: "investor", label: "Investor Pitch", icon: <ShieldCheck className="w-4 h-4 text-emerald-400" /> },
    { mode: "founder", label: "Founder Hub", icon: <Sparkles className="w-4 h-4 text-cyan-300" /> },
  ];


  return (
    <header className="sticky top-0 z-50 w-full border-b border-cyan-500/20 bg-slate-950/80 backdrop-blur-xl">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & System Vitality */}
          <div className="flex items-center gap-4">
            <button
              onClick={() => onSelectMode("landing")}
              className="flex items-center gap-3 text-left group focus:outline-none"
            >
              <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-cyan-950/80 border border-cyan-400/40 shadow-[0_0_15px_rgba(0,242,254,0.35)]">
                <Activity className="w-5 h-5 text-cyan-400 animate-pulse" />
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping" />
                <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-500 rounded-full" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-extrabold text-base tracking-wider text-white group-hover:text-cyan-400 transition-colors">
                    MEDICAL<span className="text-cyan-400">PLAB</span>
                  </span>
                  <span className="px-1.5 py-0.5 text-[10px] font-mono tracking-widest uppercase bg-cyan-950/90 text-cyan-300 border border-cyan-500/40 rounded">
                    STAGE-I PROD
                  </span>
                </div>
                <div className="text-[11px] font-mono text-slate-400 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 inline-block" />
                  EVIDENCE-GROUNDED AI CORE
                </div>
              </div>
            </button>
          </div>

          {/* Center Navigation Tabs */}
          <nav className="hidden lg:flex items-center gap-1 bg-slate-900/60 p-1 rounded-xl border border-slate-800">
            {navItems.map((item) => {
              const isActive = currentMode === item.mode;
              return (
                <button
                  key={item.mode}
                  onClick={() => onSelectMode(item.mode)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_12px_rgba(0,242,254,0.25)]"
                      : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
                  }`}
                >
                  {item.icon}
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right Action Bar */}
          <div className="flex items-center gap-2.5">
            {/* Founder Hub Quick Button */}
            <button
              onClick={() => onSelectMode("founder")}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold border transition-all ${
                currentMode === "founder"
                  ? "bg-cyan-950 text-cyan-300 border-cyan-400 shadow-[0_0_12px_rgba(0,242,254,0.35)]"
                  : "bg-slate-900/90 text-cyan-300 border-cyan-500/40 hover:bg-cyan-950/40"
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
              <span>Founder Mode</span>
            </button>

            {/* 3-Minute Guided Demo Launch Button */}
            <button
              onClick={onStartDemoJourney}
              className="relative group flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-semibold bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>3-Min Demo Tour</span>
            </button>


            {/* Hackathon Architecture Deep Dive */}
            <button
              onClick={onOpenPipelineModal}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono bg-slate-900/80 text-cyan-300 border border-cyan-500/30 hover:border-cyan-400 hover:bg-cyan-950/30 transition-all"
            >
              <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
              <span className="hidden sm:inline">Pipeline</span>
              <span className="px-1 py-0.2 text-[9px] bg-cyan-900/60 text-cyan-300 rounded font-bold">
                R $\rightarrow$ G
              </span>
            </button>

            {/* Role Switcher Pill */}
            <div className="relative group">
              <select
                value={userRole}
                onChange={(e) => onSwitchRole(e.target.value as UserRole)}
                className="bg-slate-900/90 text-slate-300 text-xs font-mono rounded-lg px-2.5 py-1.5 border border-slate-700 hover:border-slate-500 focus:outline-none cursor-pointer"
              >
                <option value="STUDENT">Role: Student (Alice)</option>
                <option value="DOCTOR">Role: Doctor (Chen)</option>
                <option value="INSTITUTION_ADMIN">Role: Admin (Dean)</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
};
