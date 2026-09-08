"use client";

import React from "react";
import {
  Award,
  AlertTriangle,
  TrendingUp,
  ArrowRight,
  Layers3,
  BookOpen,
  Activity,
  CheckCircle,
  BookMarked,
  BarChart3,
  Sparkles,
} from "lucide-react";
import { INITIAL_STUDENT_PROFILE } from "@/lib/demo-data";
import { NavigationMode, StudentMasteryProfile } from "@/lib/types";

interface StudentCommandCenterProps {
  profile?: StudentMasteryProfile;
  onNavigate: (mode: NavigationMode) => void;
}

const MASTERY_COLORS: Record<string, string> = {
  MASTERY: "#22c55e",
  COMPETENT: "#38bdf8",
  DEVELOPING: "#f59e0b",
  NOVICE: "#94a3b8",
};

const PRIORITY_STYLES: Record<string, { bg: string; color: string; border: string }> = {
  HIGH: { bg: 'rgba(239,68,68,0.08)', color: '#fca5a5', border: 'rgba(239,68,68,0.2)' },
  MEDIUM: { bg: 'rgba(245,158,11,0.08)', color: '#fcd34d', border: 'rgba(245,158,11,0.2)' },
  LOW: { bg: 'rgba(14,165,233,0.08)', color: '#7dd3fc', border: 'rgba(14,165,233,0.2)' },
};

const ACTION_ICONS: Partial<Record<NavigationMode, React.ReactNode>> = {
  tutor: <BookOpen className="w-4 h-4" />,
  anatomy: <Layers3 className="w-4 h-4" />,
  simulation: <Activity className="w-4 h-4" />,
  quiz: <BookMarked className="w-4 h-4" />,
};

export const StudentCommandCenter: React.FC<StudentCommandCenterProps> = ({
  profile = INITIAL_STUDENT_PROFILE,
  onNavigate,
}) => {
  const masteryColor = MASTERY_COLORS[profile.masteryLevel] || "#94a3b8";
  const accuracyPct = Math.round(profile.overallAccuracy * 100);

  return (
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 med-fade-in" aria-label="Learning Dashboard">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5 mb-2">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: 'rgba(14,165,233,0.15)', border: '1px solid rgba(14,165,233,0.25)' }}>
              <BarChart3 className="w-5 h-5 text-sky-400" />
            </div>
            <h2 className="section-header">Learning Dashboard</h2>
          </div>
          <p className="section-subtext">Welcome back, {profile.studentName}. Here's your clinical progress.</p>
        </div>

        <div className="flex items-center gap-2.5">
          <div
            className="flex items-center gap-2 px-4 py-2 rounded-xl text-[13px] font-semibold"
            style={{ background: `${masteryColor}15`, color: masteryColor, border: `1px solid ${masteryColor}30` }}
          >
            <Sparkles className="w-4 h-4" />
            {profile.masteryLevel.charAt(0) + profile.masteryLevel.slice(1).toLowerCase()} Level
          </div>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">

        {/* Accuracy */}
        <div className="med-card p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-[12px] font-semibold text-slate-500 uppercase tracking-wider">Clinical Accuracy</span>
            <Award className="w-4 h-4 text-sky-400" />
          </div>
          <div className="text-[42px] font-extrabold leading-none mb-3" style={{ color: '#38bdf8', fontFamily: "'Plus Jakarta Sans', sans-serif", letterSpacing: '-0.04em' }}>
            {accuracyPct}%
          </div>
          <div className="progress-track">
            <div className="progress-fill-primary" style={{ width: `${accuracyPct}%` }} />
          </div>
          <div className="mt-2 text-[11px] text-slate-500">Target: 80%+ for exam readiness</div>
        </div>

        {/* Attempts */}
        <div className="med-card p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-[12px] font-semibold text-slate-500 uppercase tracking-wider">Total Attempts</span>
            <TrendingUp className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-[42px] font-extrabold leading-none mb-3 text-white" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", letterSpacing: '-0.04em' }}>
            {profile.totalAttempts}
          </div>
          <div className="flex items-center gap-1.5 text-[12px] text-emerald-400">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>All attempts saved &amp; audited</span>
          </div>
        </div>

        {/* Weak Topics */}
        <div className="med-card p-6">
          <div className="flex items-center justify-between mb-4">
            <span className="text-[12px] font-semibold text-slate-500 uppercase tracking-wider">Areas to Improve</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-[42px] font-extrabold leading-none mb-3 text-amber-400" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif", letterSpacing: '-0.04em' }}>
            {profile.weakTopics.length}
          </div>
          <div className="text-[12px] text-slate-500">Topics flagged for focused revision</div>
        </div>
      </div>

      {/* Specialty + Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Specialty Mastery */}
        <div className="med-card p-6">
          <h3 className="text-[14px] font-semibold text-white mb-5 pb-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
            Specialty Breakdown
          </h3>
          <div className="space-y-4">
            {profile.specialtyMastery.map((spec) => {
              const pct = Math.round(spec.accuracy * 100);
              const color = spec.accuracy >= 0.75 ? '#22c55e' : spec.accuracy >= 0.6 ? '#38bdf8' : '#f59e0b';
              return (
                <div key={spec.specialty}>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[13px] font-medium text-slate-300">{spec.specialty}</span>
                    <span className="text-[13px] font-bold" style={{ color }}>{pct}%</span>
                  </div>
                  <div className="progress-track">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{ width: `${pct}%`, background: `linear-gradient(90deg, ${color}99, ${color})` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Adaptive Recommendations */}
        <div className="med-card p-6">
          <h3 className="text-[14px] font-semibold text-white mb-5 pb-3" style={{ borderBottom: '1px solid rgba(255,255,255,0.07)' }}>
            Recommended for You
          </h3>
          <div className="space-y-3">
            {profile.activeRecommendations.map((rec) => {
              const style = PRIORITY_STYLES[rec.priority] || PRIORITY_STYLES.LOW;
              return (
                <div
                  key={rec.id}
                  className="p-4 rounded-xl transition-all"
                  style={{ background: style.bg, border: `1px solid ${style.border}` }}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <div className="med-badge" style={{ background: style.bg, color: style.color, border: `1px solid ${style.border}` }}>
                          {rec.priority}
                        </div>
                        <span className="text-[13px] font-semibold text-white truncate">{rec.title}</span>
                      </div>
                      <p className="text-[12px] text-slate-400 leading-relaxed">{rec.reason}</p>
                    </div>
                    <button
                      onClick={() => onNavigate(rec.actionType)}
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[12px] font-semibold text-white flex-shrink-0 transition-all"
                      style={{ background: 'linear-gradient(135deg, #0ea5e9, #2563eb)', boxShadow: '0 2px 8px rgba(14,165,233,0.2)' }}
                    >
                      {ACTION_ICONS[rec.actionType] || <ArrowRight className="w-4 h-4" />}
                      Start
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Quick Launch Strip */}
      <div>
        <h3 className="text-[14px] font-semibold text-slate-400 mb-4">Quick Access</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { mode: "tutor" as NavigationMode, label: "AI Tutor", icon: <BookOpen className="w-5 h-5" />, color: '#38bdf8', bg: 'rgba(14,165,233,0.1)', border: 'rgba(14,165,233,0.2)' },
            { mode: "anatomy" as NavigationMode, label: "Anatomy Lab", icon: <Layers3 className="w-5 h-5" />, color: '#a78bfa', bg: 'rgba(139,92,246,0.1)', border: 'rgba(139,92,246,0.2)' },
            { mode: "simulation" as NavigationMode, label: "Simulation", icon: <Activity className="w-5 h-5" />, color: '#34d399', bg: 'rgba(52,211,153,0.1)', border: 'rgba(52,211,153,0.2)' },
            { mode: "quiz" as NavigationMode, label: "Clinical Quiz", icon: <BookMarked className="w-5 h-5" />, color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.2)' },
          ].map((item) => (
            <button
              key={item.mode}
              onClick={() => onNavigate(item.mode)}
              className="med-card p-5 flex flex-col items-start gap-3 text-left group transition-all"
              onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.borderColor = item.border; }}
              onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.borderColor = ''; }}
            >
              <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: item.bg, color: item.color }}>
                {item.icon}
              </div>
              <div>
                <div className="text-[13px] font-semibold text-white">{item.label}</div>
                <div className="flex items-center gap-1 text-[11px] mt-0.5 transition-colors" style={{ color: item.color }}>
                  <span>Open</span>
                  <ArrowRight className="w-3 h-3 transition-transform group-hover:translate-x-0.5" />
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </section>
  );
};
