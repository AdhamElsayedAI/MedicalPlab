"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  GraduationCap,
  Sparkles,
  Layers,
  Award,
  CheckCircle2,
  TrendingUp,
  AlertCircle,
  Clock,
  ArrowRight,
  BookOpen,
  HelpCircle,
  RefreshCw,
  BarChart3,
  Box,
  BrainCircuit,
  Target,
  ShieldCheck,
} from "lucide-react";
import { api, getAuthoritativeLearnerId } from "@/lib/api-client";
import type { UnifiedLearnerProgress } from "@/lib/types";

export const UnifiedProgressView: React.FC = () => {
  const [progress, setProgress] = useState<UnifiedLearnerProgress | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "topics" | "tracks">("overview");

  const loadProgress = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getLearnerProgress();
      setProgress(data);
    } catch (err: any) {
      setError(err?.message || "Failed to load learner progress data.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProgress();
  }, []);

  const learnerId = progress?.learner_id || getAuthoritativeLearnerId();

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/20 text-teal-400 text-xs font-semibold tracking-wide uppercase mb-2">
            <Target className="w-3.5 h-3.5" />
            Learning Journey Intelligence
          </div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Unified Clinical &amp; Preclinical Mastery
          </h1>
          <p className="text-slate-400 text-sm mt-1 max-w-2xl">
            Real-time mastery tracking across Preclinical University, Clinical PLAB, 3D Anatomy Lab, and Adaptive Socratic Remediation.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex flex-col items-end text-right">
            <span className="text-xs text-slate-400">Student Profile</span>
            <span className="text-xs font-medium text-teal-300 bg-teal-950/40 px-2.5 py-0.5 rounded-full border border-teal-800/50 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
              Active Session
            </span>
          </div>
          <button
            onClick={loadProgress}
            disabled={loading}
            className="p-2.5 rounded-lg bg-slate-800/80 hover:bg-slate-700 border border-slate-700/70 text-slate-300 hover:text-white transition disabled:opacity-50"
            title="Refresh Progress"
            aria-label="Refresh Progress"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-teal-400" : ""}`} />
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1 text-sm">
            <p className="font-semibold text-rose-200">Unable to load progress</p>
            <p className="text-xs text-rose-300/90 mt-0.5">{error}</p>
          </div>
          <button
            onClick={loadProgress}
            className="px-3 py-1 bg-rose-900/60 hover:bg-rose-800 text-xs font-semibold rounded-md border border-rose-700"
          >
            Retry
          </button>
        </div>
      )}

      {/* Loading Skeleton */}
      {loading && !progress && (
        <div className="space-y-6 animate-pulse">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-28 bg-slate-900/60 rounded-xl border border-slate-800" />
            ))}
          </div>
          <div className="h-64 bg-slate-900/60 rounded-xl border border-slate-800" />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="h-56 bg-slate-900/60 rounded-xl border border-slate-800" />
            <div className="h-56 bg-slate-900/60 rounded-xl border border-slate-800" />
          </div>
        </div>
      )}

      {progress && (
        <>
          {/* Key Metric Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Total Attempted */}
            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-sky-500/5 rounded-full blur-xl pointer-events-none" />
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium uppercase tracking-wider">Total Questions</span>
                <GraduationCap className="w-4 h-4 text-sky-400" />
              </div>
              <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                {progress.summary?.total_questions_attempted ?? (progress.university?.attempted || 0)}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Across Preclinical &amp; PLAB
              </p>
            </div>

            {/* University Accuracy */}
            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-teal-500/5 rounded-full blur-xl pointer-events-none" />
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium uppercase tracking-wider">University Accuracy</span>
                <Award className="w-4 h-4 text-teal-400" />
              </div>
              <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                {progress.university?.accuracy !== null && progress.university?.accuracy !== undefined
                  ? `${Math.round(progress.university.accuracy * 100)}%`
                  : "—"}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                {progress.university?.correct || 0} of {progress.university?.attempted || 0} correct
              </p>
            </div>

            {/* 3D Anatomy Lab */}
            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-purple-500/5 rounded-full blur-xl pointer-events-none" />
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium uppercase tracking-wider">3D Challenges</span>
                <Box className="w-4 h-4 text-purple-400" />
              </div>
              <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                {progress.anatomy?.challenges_passed ?? 0}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                {progress.anatomy?.completed_sessions ?? 0} completed sessions
              </p>
            </div>

            {/* Adaptive Next Target */}
            <div className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 backdrop-blur-sm relative overflow-hidden">
              <div className="absolute top-0 right-0 w-24 h-24 bg-indigo-500/5 rounded-full blur-xl pointer-events-none" />
              <div className="flex items-center justify-between text-slate-400 mb-2">
                <span className="text-xs font-medium uppercase tracking-wider">Mastered Topics</span>
                <BrainCircuit className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
                {progress.adaptive?.mastered_topics_count ?? 0}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                {progress.adaptive?.weak_topics?.length || 0} topics require review
              </p>
            </div>
          </div>

          {/* Contextual Recommendation Banner */}
          {progress.adaptive?.top_recommendation && (
            <div className="p-6 rounded-2xl bg-gradient-to-r from-teal-950/40 via-slate-900/80 to-sky-950/30 border border-teal-500/30 shadow-lg relative overflow-hidden">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
                <div className="space-y-2">
                  <div className="inline-flex items-center gap-2 px-2.5 py-0.5 rounded-full bg-teal-500/20 text-teal-300 text-xs font-semibold">
                    <Sparkles className="w-3.5 h-3.5" />
                    Adaptive Learning Recommendation
                  </div>
                  <h2 className="text-xl font-bold text-white">
                    {progress.adaptive.top_recommendation.topic}
                  </h2>
                  <p className="text-sm text-slate-300 max-w-2xl leading-relaxed">
                    {progress.adaptive.top_recommendation.explanation ||
                      progress.adaptive.top_recommendation.reason}
                  </p>
                </div>

                <div className="shrink-0 flex items-center gap-3">
                  <Link
                    href={`/practice?track=university`}
                    className="px-5 py-2.5 rounded-xl bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-sm transition shadow-md shadow-teal-500/20 inline-flex items-center gap-2"
                  >
                    Start Practice
                    <ArrowRight className="w-4 h-4" />
                  </Link>
                  <Link
                    href={`/tutor?topic=${encodeURIComponent(progress.adaptive.top_recommendation.topic)}`}
                    className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium border border-slate-700 transition"
                  >
                    Ask Tutor
                  </Link>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-slate-800">
            <button
              onClick={() => setActiveTab("overview")}
              className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition -mb-px flex items-center gap-2 ${
                activeTab === "overview"
                  ? "border-teal-400 text-teal-300"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              Overview &amp; Tracks
            </button>
            <button
              onClick={() => setActiveTab("topics")}
              className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition -mb-px flex items-center gap-2 ${
                activeTab === "topics"
                  ? "border-teal-400 text-teal-300"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <Layers className="w-4 h-4" />
              Preclinical Topics Mastery
            </button>
            <button
              onClick={() => setActiveTab("tracks")}
              className={`px-4 py-2.5 text-sm font-semibold border-b-2 transition -mb-px flex items-center gap-2 ${
                activeTab === "tracks"
                  ? "border-teal-400 text-teal-300"
                  : "border-transparent text-slate-400 hover:text-slate-200"
              }`}
            >
              <GraduationCap className="w-4 h-4" />
              Clinical PLAB &amp; 3D Anatomy
            </button>
          </div>

          {/* Tab 1: Overview & Tracks */}
          {activeTab === "overview" && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Preclinical University Card */}
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-lg bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
                      <GraduationCap className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-white">Preclinical University</h3>
                      <p className="text-xs text-slate-400">Physiology &amp; Foundations</p>
                    </div>
                  </div>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                    Active
                  </span>
                </div>

                <div className="space-y-3 pt-2">
                  <div className="flex justify-between text-xs text-slate-300">
                    <span>Attempts</span>
                    <span className="font-semibold text-white">{progress.university?.attempted || 0}</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-300">
                    <span>Correct</span>
                    <span className="font-semibold text-white">{progress.university?.correct || 0}</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-300">
                    <span>Accuracy</span>
                    <span className="font-semibold text-white">
                      {progress.university?.accuracy !== null && progress.university?.accuracy !== undefined
                        ? `${Math.round(progress.university.accuracy * 100)}%`
                        : "No attempts yet"}
                    </span>
                  </div>
                </div>

                <Link
                  href="/practice?track=university"
                  className="w-full mt-4 py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-sky-300 border border-slate-700 transition flex items-center justify-center gap-1.5"
                >
                  Go to Preclinical Practice
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {/* Clinical PLAB Track Card */}
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-lg bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400">
                      <BookOpen className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-white">Clinical PLAB 1</h3>
                      <p className="text-xs text-slate-400">UK Medical Licensing</p>
                    </div>
                  </div>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-sky-500/10 text-sky-300 border border-sky-500/20">
                    Preview QA
                  </span>
                </div>

                <div className="space-y-3 pt-2">
                  <div className="flex justify-between text-xs text-slate-300">
                    <span>Questions Available</span>
                    <span className="font-semibold text-white">{progress.plab?.question_count ?? 87}</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-300">
                    <span>Attempts Logged</span>
                    <span className="font-semibold text-white">{progress.plab?.total_attempts || 0}</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-300">
                    <span>Governance Status</span>
                    <span className="font-semibold text-teal-300 text-[11px]">Clinical Review Mode</span>
                  </div>
                </div>

                <Link
                  href="/practice?track=plab"
                  className="w-full mt-4 py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-teal-300 border border-slate-700 transition flex items-center justify-center gap-1.5"
                >
                  Enter PLAB Preview
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {/* 3D Anatomy Lab Card */}
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-lg bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                      <Box className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-white">3D Anatomy Lab</h3>
                      <p className="text-xs text-slate-400">HRA Renal Vasculature</p>
                    </div>
                  </div>
                  <span className="text-xs font-semibold px-2 py-0.5 rounded bg-purple-500/10 text-purple-300 border border-purple-500/20">
                    Interactive
                  </span>
                </div>

                <div className="space-y-3 pt-2">
                  <div className="flex justify-between text-xs text-slate-300">
                    <span>Guided Objectives</span>
                    <span className="font-semibold text-white">Renal Blood Flow &amp; Hilum</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-300">
                    <span>Completed Sessions</span>
                    <span className="font-semibold text-white">{progress.anatomy?.completed_sessions || 0}</span>
                  </div>
                  <div className="flex justify-between text-xs text-slate-300">
                    <span>Challenge Pass</span>
                    <span className="font-semibold text-emerald-300">
                      {progress.anatomy?.challenges_passed ? `${progress.anatomy.challenges_passed} passed` : "Pending"}
                    </span>
                  </div>
                </div>

                <Link
                  href="/anatomy"
                  className="w-full mt-4 py-2 px-3 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-semibold text-purple-300 border border-slate-700 transition flex items-center justify-center gap-1.5"
                >
                  Launch 3D Lab
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          )}

          {/* Tab 2: Preclinical Topics Mastery */}
          {activeTab === "topics" && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white">Topic Competency Analysis</h3>
                <span className="text-xs text-slate-400">
                  {progress.university?.topics?.length || 0} topics indexed
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {progress.university?.topics?.map((topicItem, idx) => {
                  const mastery = topicItem.mastery || "not_started";
                  const isMastered = mastery === "mastered";
                  const isCompetent = mastery === "competent";
                  const isDeveloping = mastery === "developing";
                  const isNeedsReview = mastery === "beginner" && topicItem.attempted > 0;

                  return (
                    <div
                      key={idx}
                      className="p-5 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                            {topicItem.subject}
                          </span>
                          <h4 className="text-base font-semibold text-white mt-0.5">
                            {topicItem.topic}
                          </h4>
                        </div>
                        <span
                          className={`text-xs font-semibold px-2.5 py-0.5 rounded-full capitalize ${
                            isMastered
                              ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                              : isCompetent
                              ? "bg-teal-500/20 text-teal-300 border border-teal-500/30"
                              : isDeveloping
                              ? "bg-sky-500/20 text-sky-300 border border-sky-500/30"
                              : isNeedsReview
                              ? "bg-amber-500/20 text-amber-300 border border-amber-500/30"
                              : "bg-slate-800 text-slate-400 border border-slate-700"
                          }`}
                        >
                          {mastery.replace("_", " ")}
                        </span>
                      </div>

                      <div className="flex items-center justify-between text-xs text-slate-400 pt-2 border-t border-slate-800">
                        <span>Attempts: <strong className="text-slate-200">{topicItem.attempted}</strong></span>
                        <span>Correct: <strong className="text-slate-200">{topicItem.correct}</strong></span>
                        <span>
                          Accuracy:{" "}
                          <strong className="text-slate-200">
                            {topicItem.accuracy !== null ? `${Math.round(topicItem.accuracy * 100)}%` : "—"}
                          </strong>
                        </span>
                      </div>

                      <div className="pt-2 flex items-center justify-end gap-2">
                        <Link
                          href={`/tutor?topic=${encodeURIComponent(topicItem.topic)}`}
                          className="text-xs text-sky-400 hover:text-sky-300 font-medium flex items-center gap-1"
                        >
                          Ask Tutor <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Tab 3: Clinical PLAB & 3D Anatomy Details */}
          {activeTab === "tracks" && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* PLAB Deep Dive */}
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center text-teal-400">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">PLAB 1 Clinical Review Status</h3>
                    <p className="text-xs text-slate-400">UK Medical Licensing Examination Assessment</p>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 text-xs text-slate-300 space-y-2">
                  <p className="font-semibold text-teal-300">
                    Governance Note: Preview QA Active
                  </p>
                  <p>
                    Questions are evaluated against UK GMC standards. Content shown in Preview QA is under clinical evaluation and does not represent locked golden curriculum.
                  </p>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1.5 border-b border-slate-800 text-slate-300">
                    <span>Clinical Item Bank</span>
                    <span className="font-semibold text-white">{progress.plab?.question_count || 87} questions</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800 text-slate-300">
                    <span>Attempt Count</span>
                    <span className="font-semibold text-white">{progress.plab?.total_attempts || 0}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800 text-slate-300">
                    <span>Overall Accuracy</span>
                    <span className="font-semibold text-white">
                      {progress.plab?.overall_accuracy !== null && progress.plab?.overall_accuracy !== undefined
                        ? `${Math.round(progress.plab.overall_accuracy * 100)}%`
                        : "No attempts yet"}
                    </span>
                  </div>
                </div>

                <Link
                  href="/practice?track=plab"
                  className="inline-flex items-center gap-2 text-xs font-semibold text-teal-400 hover:text-teal-300 pt-2"
                >
                  Open PLAB Clinical Practice <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>

              {/* Anatomy Deep Dive */}
              <div className="p-6 rounded-2xl bg-slate-900/60 border border-slate-800/80 space-y-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                    <Box className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white">HRA 3D Anatomy Curricula</h3>
                    <p className="text-xs text-slate-400">Human Reference Atlas Renal Structures</p>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-700/60 text-xs text-slate-300 space-y-2">
                  <p className="font-semibold text-purple-300">
                    Curriculum Invariants:
                  </p>
                  <ul className="list-disc list-inside space-y-1 text-slate-400">
                    <li>Guided Target: Left Renal Vein (Anterior hilum)</li>
                    <li>Transfer Challenge: Left Renal Artery (Intermediate hilum)</li>
                    <li>Internal Cutaway: Renal Pelvis &amp; Medulla</li>
                  </ul>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between py-1.5 border-b border-slate-800 text-slate-300">
                    <span>Total 3D Sessions</span>
                    <span className="font-semibold text-white">{progress.anatomy?.total_sessions || 0}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800 text-slate-300">
                    <span>Completed Objectives</span>
                    <span className="font-semibold text-white">{progress.anatomy?.completed_sessions || 0}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800 text-slate-300">
                    <span>Anatomy Challenges Passed</span>
                    <span className="font-semibold text-emerald-300">{progress.anatomy?.challenges_passed || 0}</span>
                  </div>
                </div>

                <Link
                  href="/anatomy"
                  className="inline-flex items-center gap-2 text-xs font-semibold text-purple-400 hover:text-purple-300 pt-2"
                >
                  Enter 3D Laboratory <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
