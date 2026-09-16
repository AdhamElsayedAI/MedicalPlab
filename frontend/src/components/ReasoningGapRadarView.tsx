"use client";

import React, { useEffect, useState } from "react";
import { api } from "../lib/api-client";
import { ReasoningGapRadarResponse, ReasoningGapAggregate } from "../lib/types";

export function ReasoningGapRadarView() {
  const [cohortId, setCohortId] = useState<string>("cohort_demo_renal_01");
  const [topicFilter, setTopicFilter] = useState<string>("");
  const [radarData, setRadarData] = useState<ReasoningGapRadarResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedEvidence, setExpandedEvidence] = useState<Record<string, boolean>>({});

  const loadRadar = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getReasoningGapRadar(cohortId, topicFilter || undefined);
      setRadarData(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load reasoning gap radar");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRadar();
  }, [cohortId, topicFilter]);

  const toggleEvidence = (patternId: string) => {
    setExpandedEvidence((prev) => ({
      ...prev,
      [patternId]: !prev[patternId],
    }));
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 md:p-10">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Top Header */}
        <header className="border-b border-slate-800 pb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-white">
                Class Reasoning-Gap Radar
              </h1>
              {radarData?.is_demo_data && (
                <span
                  id="demo-cohort-badge"
                  className="px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40"
                >
                  Synthetic Demo Cohort
                </span>
              )}
            </div>
            <p className="text-slate-400 text-sm mt-1">
              Cross-learner cognitive gap intelligence & independent transfer analytics
            </p>
          </div>

          {/* Controls */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5">
              <label htmlFor="cohort-select" className="text-xs text-slate-400 font-medium">
                Cohort:
              </label>
              <select
                id="cohort-select"
                value={cohortId}
                onChange={(e) => setCohortId(e.target.value)}
                className="bg-transparent text-sm text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="cohort_demo_renal_01" className="bg-slate-900">
                  Preclinical Year 1 (Demo)
                </option>
                <option value="cohort_unknown_rejected" className="bg-slate-900">
                  Unknown Cohort (Rejection Test)
                </option>
              </select>
            </div>

            <div className="flex items-center gap-2 bg-slate-900 border border-slate-800 rounded-lg px-3 py-1.5">
              <label htmlFor="topic-filter" className="text-xs text-slate-400 font-medium">
                Topic:
              </label>
              <select
                id="topic-filter"
                value={topicFilter}
                onChange={(e) => setTopicFilter(e.target.value)}
                className="bg-transparent text-sm text-slate-200 focus:outline-none cursor-pointer"
              >
                <option value="" className="bg-slate-900">
                  All Topics
                </option>
                <option value="preclinical_renal" className="bg-slate-900">
                  Preclinical Renal / RAAS
                </option>
              </select>
            </div>

            <button
              id="refresh-radar-btn"
              onClick={loadRadar}
              disabled={loading}
              className="px-3.5 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg border border-slate-700 transition"
            >
              {loading ? "Loading..." : "Refresh"}
            </button>
          </div>
        </header>

        {/* Demo Data Notice */}
        {radarData?.is_demo_data && (
          <div
            id="demo-disclaimer-banner"
            className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-xs text-amber-200 flex items-start gap-3"
          >
            <span className="text-amber-400 font-bold text-sm">ℹ</span>
            <div>
              <span className="font-semibold">DEMO DATA NOTICE:</span>{" "}
              {radarData.demo_disclaimer ||
                "These records are synthetic demonstration fixtures used to evaluate cross-learner reasoning gap radar capabilities. No real student data is used."}
            </div>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-300">
            {error}
          </div>
        )}

        {/* Loading Spinner */}
        {loading && !radarData && (
          <div className="py-20 text-center text-slate-500">
            <div className="inline-block animate-spin w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full mb-3" />
            <p className="text-sm">Aggregating cross-learner reasoning signals...</p>
          </div>
        )}

        {/* Main Content */}
        {radarData && (
          <>
            {/* Small-N Privacy Suppression View */}
            {radarData.sufficiency_status === "INSUFFICIENT_COHORT_DATA" ? (
              <div
                id="insufficient-cohort-card"
                className="rounded-2xl border border-slate-800 bg-slate-900/60 p-10 text-center space-y-4 max-w-xl mx-auto"
              >
                <div className="w-12 h-12 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center mx-auto text-xl font-bold">
                  🛡️
                </div>
                <h2 className="text-lg font-bold text-slate-200">
                  Insufficient Cohort Data (N &lt; {radarData.min_cohort_n})
                </h2>
                <p className="text-sm text-slate-400 leading-relaxed">
                  To protect learner privacy and avoid asserting spurious group patterns,
                  MedicalPlab requires at least {radarData.min_cohort_n} unique learners before
                  displaying reasoning-gap analytics.
                </p>
                <div className="text-xs text-slate-500">
                  Current eligible learners in cohort:{" "}
                  <span className="font-semibold text-slate-300">
                    {radarData.total_eligible_learners}
                  </span>
                </div>
              </div>
            ) : (
              /* Sufficient Cohort Data View */
              <div className="space-y-8">
                {/* KPI Summary Banner */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div
                    id="kpi-eligible-learners"
                    className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm"
                  >
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Eligible Learners
                    </div>
                    <div className="text-3xl font-extrabold text-white mt-2">
                      {radarData.total_eligible_learners}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Unique students with completed sessions
                    </div>
                  </div>

                  <div
                    id="kpi-observed-patterns"
                    className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm"
                  >
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Observed Reasoning Gaps
                    </div>
                    <div className="text-3xl font-extrabold text-indigo-400 mt-2">
                      {radarData.reasoning_gaps.length}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Distinct cognitive pattern signals
                    </div>
                  </div>

                  <div
                    id="kpi-transfer-rate"
                    className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm"
                  >
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Independent Transfer Rate
                    </div>
                    <div className="text-3xl font-extrabold text-emerald-400 mt-2">
                      {radarData.overall_transfer_effectiveness.transfer_demonstration_rate !== null
                        ? `${Math.round(
                            radarData.overall_transfer_effectiveness.transfer_demonstration_rate *
                              100
                          )}%`
                        : "N/A"}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      {radarData.overall_transfer_effectiveness.transfer_demonstrated_count} of{" "}
                      {radarData.overall_transfer_effectiveness.qualified_independent_transfer_count} qualified independent attempts
                      demonstrated
                    </div>
                  </div>

                  <div
                    id="kpi-assisted-excluded"
                    className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 backdrop-blur-sm"
                  >
                    <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                      Assisted Attempts Excluded
                    </div>
                    <div className="text-3xl font-extrabold text-sky-400 mt-2">
                      {radarData.overall_transfer_effectiveness.assisted_excluded_count}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      Non-independent attempts excluded from transfer rate
                    </div>
                  </div>
                </div>

                {/* Section Header */}
                <div className="space-y-1">
                  <h2 className="text-lg font-bold text-white">Observed Reasoning Gaps</h2>
                  <p className="text-xs text-slate-400">
                    Epistemically modest hypotheses based on distractor clustering and Socratic
                    remediation trajectories.
                  </p>
                </div>

                {/* Reasoning Gap Cards */}
                <div className="space-y-4">
                  {radarData.reasoning_gaps.map((gap: ReasoningGapAggregate) => {
                    const isEvidenceOpen = !!expandedEvidence[gap.pattern_id];
                    const demonstrated = gap.transfer_metrics.transfer_demonstrated_count;
                    const attempted = gap.transfer_metrics.transfer_attempted_count;
                    const transferPct =
                      gap.transfer_metrics.transfer_demonstration_rate !== null
                        ? Math.round(gap.transfer_metrics.transfer_demonstration_rate * 100)
                        : null;

                    return (
                      <div
                        key={gap.pattern_id}
                        id={`gap-card-${gap.pattern_id}`}
                        className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6 space-y-5 transition hover:border-slate-700"
                      >
                        {/* Header: Category, Title, Epistemic Badge */}
                        <div className="flex flex-col md:flex-row md:items-start justify-between gap-3">
                          <div className="space-y-1.5">
                            <div className="flex flex-wrap items-center gap-2">
                              <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-indigo-950 text-indigo-300 border border-indigo-800/60">
                                {gap.category.replace(/_/g, " ")}
                              </span>
                              <span className="px-2 py-0.5 text-xs font-medium rounded-md bg-blue-950 text-blue-300 border border-blue-800/60">
                                Possible shared reasoning gap
                              </span>
                              <span className="text-xs text-slate-500 font-mono">
                                {gap.pattern_id}
                              </span>
                            </div>
                            <h3 className="text-base md:text-lg font-semibold text-white">
                              {gap.reasoning_pattern}
                            </h3>
                          </div>

                          <div className="text-right shrink-0">
                            <div className="text-sm font-semibold text-slate-200">
                              Observed pattern: {gap.unique_learners_count} of{" "}
                              {radarData.total_eligible_learners} eligible learners
                            </div>
                            <div className="text-xs text-slate-400">
                              Prevalence: {(gap.prevalence_rate * 100).toFixed(1)}% (
                              {gap.sessions_count} sessions)
                            </div>
                          </div>
                        </div>

                        {/* Prevalence Progress Bar */}
                        <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-indigo-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(100, gap.prevalence_rate * 100)}%` }}
                          />
                        </div>

                        {/* Transfer Effectiveness Breakdown */}
                        <div className="rounded-xl border border-slate-800/80 bg-slate-950/60 p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                              Independent Transfer
                            </div>
                            <div className="text-sm font-semibold text-slate-200 mt-1">
                              {transferPct !== null
                                ? `${demonstrated} of ${gap.transfer_metrics.qualified_independent_transfer_count} qualified independent attempts demonstrated transfer (${transferPct}%)`
                                : "No qualified transfer attempts recorded"}
                            </div>
                            <div className="text-xs text-slate-400 mt-1">
                              {gap.transfer_metrics.transfer_not_demonstrated_count > 0 ? (
                                <span className="text-slate-400">
                                  {gap.transfer_metrics.transfer_not_demonstrated_count} qualified attempt
                                  {gap.transfer_metrics.transfer_not_demonstrated_count > 1 ? "s" : ""} did not demonstrate transfer
                                </span>
                              ) : (
                                <span className="text-emerald-400/80">
                                  All qualified independent attempts demonstrated transfer
                                </span>
                              )}
                            </div>
                          </div>

                          <div>
                            <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                              Assisted Attempts Excluded
                            </div>
                            <div className="text-sm font-semibold text-slate-200 mt-1">
                              {gap.transfer_metrics.assisted_excluded_count}
                            </div>
                            <div className="text-xs text-slate-400 mt-1">
                              {gap.transfer_metrics.assisted_excluded_count > 0 ? (
                                <span className="text-amber-300 font-medium">
                                  ⚠️ Excluded from both numerator and denominator
                                </span>
                              ) : (
                                <span className="text-slate-400">
                                  ✓ No assisted attempts in this pattern
                                </span>
                              )}
                            </div>
                          </div>
                        </div>

                        {/* Grounded Clinical Evidence Section */}
                        {gap.evidence_references && gap.evidence_references.length > 0 && (
                          <div className="pt-2 border-t border-slate-800/60">
                            <button
                              id={`toggle-evidence-${gap.pattern_id}`}
                              onClick={() => toggleEvidence(gap.pattern_id)}
                              className="text-xs font-medium text-indigo-400 hover:text-indigo-300 flex items-center gap-1.5 transition"
                            >
                              <span>{isEvidenceOpen ? "▼ Hide" : "▶ View"} Grounded Clinical Evidence</span>
                              <span className="text-slate-500 font-mono text-[10px]">
                                ({gap.evidence_references.length} source reference
                                {gap.evidence_references.length > 1 ? "s" : ""})
                              </span>
                            </button>

                            {isEvidenceOpen && (
                              <div className="mt-3 space-y-2">
                                {gap.evidence_references.map((ev, idx) => (
                                  <div
                                    key={idx}
                                    className="rounded-lg border border-slate-800 bg-slate-950/80 p-3 text-xs space-y-1"
                                  >
                                    <div className="flex items-center justify-between text-slate-400">
                                      <span className="font-mono text-indigo-300 font-medium">
                                        {ev.document_id}
                                        {ev.chunk_id ? ` · ${ev.chunk_id}` : ""}
                                      </span>
                                      {ev.license && (
                                        <span className="px-1.5 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300">
                                          {ev.license}
                                        </span>
                                      )}
                                    </div>
                                    {ev.title && (
                                      <p className="text-slate-200 font-medium">{ev.title}</p>
                                    )}
                                    {ev.source_url && (
                                      <a
                                        href={ev.source_url}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="inline-block text-indigo-400 hover:underline text-[11px] mt-1"
                                      >
                                        Open verified source ↗
                                      </a>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
