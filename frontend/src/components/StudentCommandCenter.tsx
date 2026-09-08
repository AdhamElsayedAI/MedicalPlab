"use client";

import React from "react";
import {
  Terminal,
  Award,
  AlertTriangle,
  Sparkles,
  TrendingUp,
  Clock,
  ArrowRight,
  Layers,
  GraduationCap,
  Activity,
  CheckCircle2,
} from "lucide-react";
import { INITIAL_STUDENT_PROFILE } from "@/lib/demo-data";
import { NavigationMode, StudentMasteryProfile } from "@/lib/types";

interface StudentCommandCenterProps {
  profile?: StudentMasteryProfile;
  onNavigate: (mode: NavigationMode) => void;
}

export const StudentCommandCenter: React.FC<StudentCommandCenterProps> = ({
  profile = INITIAL_STUDENT_PROFILE,
  onNavigate,
}) => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-500/40">
              <Terminal className="w-4 h-4" />
            </span>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-wide">
              STUDENT COMMAND CENTER
            </h2>
          </div>
          <p className="text-xs text-slate-400 font-mono">
            STAGE-E ADAPTIVE LEARNING INTELLIGENCE // REAL-TIME MASTERY TRACKING
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-700 text-xs font-mono text-cyan-300">
            CANDIDATE: {profile.studentName}
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-cyan-950 border border-cyan-500/40 text-xs font-mono font-bold text-cyan-300">
            TIER: {profile.masteryLevel}
          </span>
        </div>
      </div>

      {/* Top 3 KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="cyber-card rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/85">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
            <span>OVERALL CLINICAL ACCURACY</span>
            <Award className="w-4 h-4 text-cyan-400" />
          </div>
          <div className="text-3xl font-black font-mono text-cyan-300">
            {(profile.overallAccuracy * 100).toFixed(1)}%
          </div>
          <div className="mt-3 w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
            <div
              className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full rounded-full"
              style={{ width: `${profile.overallAccuracy * 100}%` }}
            />
          </div>
        </div>

        <div className="cyber-card rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/85">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
            <span>TOTAL DIAGNOSTIC ATTEMPTS</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-3xl font-black font-mono text-white">
            {profile.totalAttempts}
          </div>
          <span className="mt-3 text-[11px] font-mono text-slate-400 block">
            Saved & Audited in Stage-G Repository
          </span>
        </div>

        <div className="cyber-card rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/85">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 mb-2">
            <span>ACTIVE REMEDIATION TOPICS</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-3xl font-black font-mono text-amber-400">
            {profile.weakTopics.length}
          </div>
          <span className="mt-3 text-[11px] font-mono text-slate-400 block">
            Flagged for High-Yield Revision
          </span>
        </div>
      </div>

      {/* Specialty Breakdown & Weak Topic Remediation */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 6 Cols: Specialty Mastery Bars */}
        <div className="lg:col-span-6 cyber-card rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/85 space-y-4">
          <span className="text-xs font-mono text-cyan-400 font-bold block border-b border-slate-800 pb-2">
            SPECIALTY MASTERY RADAR
          </span>

          <div className="space-y-3.5">
            {profile.specialtyMastery.map((spec) => (
              <div key={spec.specialty} className="space-y-1">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-slate-300 font-semibold">{spec.specialty}</span>
                  <span
                    className={
                      spec.accuracy >= 0.75
                        ? "text-emerald-400 font-bold"
                        : spec.accuracy >= 0.6
                        ? "text-cyan-300"
                        : "text-amber-400 font-bold"
                    }
                  >
                    {(spec.accuracy * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                  <div
                    className={`h-full rounded-full ${
                      spec.accuracy >= 0.75
                        ? "bg-emerald-500"
                        : spec.accuracy >= 0.6
                        ? "bg-cyan-500"
                        : "bg-amber-500"
                    }`}
                    style={{ width: `${spec.accuracy * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right 6 Cols: Weak Topics & Adaptive Recommendations */}
        <div className="lg:col-span-6 cyber-card rounded-2xl p-5 border border-cyan-500/20 bg-slate-950/85 space-y-4">
          <span className="text-xs font-mono text-amber-400 font-bold block border-b border-slate-800 pb-2">
            STAGE-E EXPLAINABLE RECOMMENDATIONS
          </span>

          <div className="space-y-3">
            {profile.activeRecommendations.map((rec) => (
              <div
                key={rec.id}
                className="p-3.5 rounded-xl bg-slate-900/90 border border-slate-800 hover:border-cyan-500/40 transition-colors flex items-start justify-between gap-3"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950/80 text-amber-400 border border-amber-500/30">
                      {rec.priority}
                    </span>
                    <span className="text-xs font-bold text-white">{rec.title}</span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed font-sans">
                    {rec.reason}
                  </p>
                </div>

                <button
                  onClick={() => onNavigate(rec.actionType)}
                  className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex-shrink-0 transition-colors"
                >
                  Launch
                </button>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
