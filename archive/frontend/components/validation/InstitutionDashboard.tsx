"use client";

import React, { useState } from "react";
import {
  Building2,
  Users,
  GraduationCap,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowUpRight,
  Send,
  Zap,
} from "lucide-react";
import { INSTITUTION_DATA } from "@/lib/stage-m-data";

export const InstitutionDashboard: React.FC = () => {
  const [assignedActionId, setAssignedActionId] = useState<string | null>(null);

  const handleAssignIntervention = (title: string) => {
    setAssignedActionId(title);
    setTimeout(() => {
      setAssignedActionId(null);
    }, 3000);
  };

  return (
    <div className="space-y-6">
      {/* Deanery Header Banner */}
      <div className="p-6 rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-900 via-slate-950 to-slate-900 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/40">
              B2B ENTERPRISE COCKPIT
            </span>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
              [Prototype Projection]
            </span>
          </div>
          <h2 className="text-2xl font-black text-white flex items-center gap-3">
            <Building2 className="w-6 h-6 text-purple-400" />
            <span>{INSTITUTION_DATA.deaneryName}</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time cohort telemetry across Foundation Year 1 (FY1) trainees and international medical graduates.
          </p>
        </div>

        {/* 4 Quick Stat Badges */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 shrink-0">
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Total Candidates</span>
            <span className="text-xl font-bold font-mono text-white">{INSTITUTION_DATA.activeCandidates}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Daily Active</span>
            <span className="text-xl font-bold font-mono text-cyan-400">{INSTITUTION_DATA.engagementIndicators.dailyActivePct}%</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Safety Intercepts</span>
            <span className="text-xl font-bold font-mono text-emerald-400">{INSTITUTION_DATA.engagementIndicators.safetyIncidentsIntercepted}</span>
          </div>
          <div className="p-3 rounded-xl bg-slate-950/80 border border-slate-800 text-center">
            <span className="text-[10px] font-mono text-slate-400 uppercase block">Avg Study Hrs</span>
            <span className="text-xl font-bold font-mono text-purple-400">{INSTITUTION_DATA.averageStudyHours}h</span>
          </div>
        </div>
      </div>

      {/* Cohort Mastery Distribution */}
      <div className="p-5 rounded-2xl border border-slate-800 bg-slate-950/60">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider flex items-center gap-2">
            <GraduationCap className="w-4 h-4 text-cyan-400" />
            <span>Cohort Licensing Readiness Distribution</span>
          </h3>
          <span className="text-xs font-mono text-slate-400">
            Pass Benchmark: $\ge 68\%$ PLAB 1 Score
          </span>
        </div>

        {/* Stacked Progress Bar */}
        <div className="w-full bg-slate-900 rounded-full h-4 overflow-hidden flex border border-slate-800">
          <div
            className="bg-gradient-to-r from-emerald-500 to-teal-400 h-full transition-all"
            style={{ width: `${INSTITUTION_DATA.examReadyPct}%` }}
            title={`Exam Ready: ${INSTITUTION_DATA.examReadyPct}%`}
          />
          <div
            className="bg-gradient-to-r from-cyan-500 to-blue-500 h-full transition-all"
            style={{ width: `${INSTITUTION_DATA.developingPct}%` }}
            title={`Developing: ${INSTITUTION_DATA.developingPct}%`}
          />
          <div
            className="bg-gradient-to-r from-rose-500 to-amber-500 h-full transition-all"
            style={{ width: `${INSTITUTION_DATA.criticalRemediationPct}%` }}
            title={`Critical Remediation: ${INSTITUTION_DATA.criticalRemediationPct}%`}
          />
        </div>

        {/* Legend */}
        <div className="mt-3 flex flex-wrap items-center justify-between gap-4 text-xs font-mono">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-emerald-400" />
            <span className="text-white font-bold">{INSTITUTION_DATA.examReadyPct}% Exam Ready</span>
            <span className="text-slate-400">(232 Doctors on Track)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-cyan-400" />
            <span className="text-white font-bold">{INSTITUTION_DATA.developingPct}% Developing Competence</span>
            <span className="text-slate-400">(82 Doctors)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-rose-400" />
            <span className="text-white font-bold">{INSTITUTION_DATA.criticalRemediationPct}% Critical Remediation</span>
            <span className="text-rose-400 font-bold">(28 Doctors at Risk)</span>
          </div>
        </div>
      </div>

      {/* Two Column Section: High-Risk Topics & Curriculum Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* High Risk Topics (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400" />
              <span>High-Risk Clinical Deficit Heatmap</span>
            </h3>
            <span className="text-[11px] font-mono text-rose-400">
              Triggering Faculty Interventions
            </span>
          </div>

          <div className="space-y-3">
            {INSTITUTION_DATA.highRiskTopics.map((topic, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-slate-800 bg-slate-950/70 hover:border-rose-500/40 transition-all"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-400 font-semibold">
                    {topic.guidelineRef}
                  </span>
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 border border-rose-500/30">
                    {topic.failureRate}% Failure Rate
                  </span>
                </div>

                <h4 className="text-sm font-bold text-white mt-1.5">{topic.topic}</h4>

                <p className="text-xs text-slate-300 mt-2 font-mono bg-slate-900/80 p-2 rounded border border-slate-800/80">
                  <span className="text-cyan-400 font-bold">Suggested Action: </span>
                  {topic.suggestedIntervention}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Curriculum Recommendations & 1-Click Assignment (6 cols) */}
        <div className="lg:col-span-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold font-mono text-white uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-purple-400" />
              <span>AI Deanery Intervention Protocols</span>
            </h3>
            <span className="text-[11px] font-mono text-purple-400">
              Automated Remediation Engine
            </span>
          </div>

          <div className="space-y-3">
            {INSTITUTION_DATA.curriculumRecommendations.map((rec, idx) => {
              const isAssigned = assignedActionId === rec.title;
              return (
                <div
                  key={idx}
                  className="p-4 rounded-xl border border-slate-800 bg-slate-950/70 hover:border-purple-500/40 transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between">
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                          rec.priority === "HIGH"
                            ? "bg-rose-500/20 text-rose-300 border-rose-500/30"
                            : rec.priority === "MEDIUM"
                            ? "bg-amber-500/20 text-amber-300 border-amber-500/30"
                            : "bg-cyan-500/20 text-cyan-300 border-cyan-500/30"
                        }`}
                      >
                        {rec.priority} PRIORITY
                      </span>
                      <span className="text-xs font-mono text-slate-400">
                        Targeting {rec.targetCandidates} Trainees
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-white mt-2">{rec.title}</h4>
                    <p className="text-xs text-slate-300 mt-1.5 leading-relaxed">{rec.actionPlan}</p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                    <span className="text-[11px] font-mono text-slate-400">
                      Auto-syncs with student learning path
                    </span>

                    <button
                      onClick={() => handleAssignIntervention(rec.title)}
                      disabled={isAssigned}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
                        isAssigned
                          ? "bg-emerald-500 text-black shadow-[0_0_12px_rgba(16,185,129,0.5)]"
                          : "bg-purple-600/30 hover:bg-purple-600 text-purple-200 border border-purple-500/40"
                      }`}
                    >
                      {isAssigned ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Dispatched to 28 Doctors!</span>
                        </>
                      ) : (
                        <>
                          <Send className="w-3.5 h-3.5" />
                          <span>Dispatch Intervention</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};
