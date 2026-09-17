"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  BookOpen,
  Layers3,
  TrendingUp,
  ArrowRight,
  ShieldCheck,
  BrainCircuit,
  Stethoscope,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  Activity,
  Layers,
  ArrowUpRight,
  Flame,
  Clock,
  Compass,
} from "lucide-react";
import { api, getAuthoritativeLearnerId } from "@/lib/api-client";
import type { AdaptiveRecommendation, UnifiedLearnerProgress } from "@/lib/types";

export const LearningHub: React.FC = () => {
  const router = useRouter();
  const [learnerId, setLearnerId] = useState<string>("");
  const [recommendation, setRecommendation] = useState<AdaptiveRecommendation | null>(null);
  const [progress, setProgress] = useState<UnifiedLearnerProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [tutorInput, setTutorInput] = useState("");

  useEffect(() => {
    const id = getAuthoritativeLearnerId();
    setLearnerId(id);

    async function loadData() {
      try {
        setLoading(true);
        const [recData, progData] = await Promise.allSettled([
          api.getAdaptiveRecommendation(id),
          api.getLearnerProgress(id),
        ]);

        if (recData.status === "fulfilled") {
          setRecommendation(recData.value);
        }
        if (progData.status === "fulfilled") {
          setProgress(progData.value);
        }
      } catch (err) {
        console.error("Failed to load learning hub data:", err);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const handleTutorSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (tutorInput.trim()) {
      router.push(`/tutor?query=${encodeURIComponent(tutorInput.trim())}`);
    } else {
      router.push("/tutor");
    }
  };

  const getActionTitle = (action?: string) => {
    switch (action) {
      case "ASK_GROUNDED_TUTOR":
        return "Socratic Remediation Recommended";
      case "SOLVE_TARGETED_QUESTION":
        return "Targeted Question Practice";
      case "REVIEW_CONCEPT":
        return "Concept Reinforcement";
      case "REPEAT_TOPIC":
        return "Topic Practice Session";
      default:
        return "Next Educational Intervention";
    }
  };

  const accuracyPct = progress?.university?.accuracy !== null && progress?.university?.accuracy !== undefined
    ? Math.round(progress.university.accuracy * 100)
    : 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 med-fade-in">
      {/* 1. Header & Identity Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/[0.08]">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/20">
              <Activity className="w-3 h-3 text-sky-400" />
              Preclinical &amp; Clinical Track
            </span>
            <span className="text-xs text-slate-400 font-medium">
              Medical Student
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight font-['Plus_Jakarta_Sans',sans-serif]">
            Welcome back to MedicalPlab
          </h1>
          <p className="text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
            An Adaptive Evidence-Grounded Medical Learning Platform. MedicalPlab does not only answer students—it learns how students learn.
          </p>
        </div>

        {/* Learning Loop Visualizer Badge */}
        <div className="bg-white/[0.03] border border-white/[0.08] p-3 rounded-2xl flex flex-col gap-1.5 min-w-[260px]">
          <div className="flex items-center justify-between text-[11px]">
            <span className="text-slate-400 font-medium">Cognitive Learning Loop</span>
            <span className="text-emerald-400 font-semibold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Connected
            </span>
          </div>
          <div className="flex items-center gap-1 text-[10px] font-mono text-slate-300 font-medium">
            <span className="px-1.5 py-0.5 rounded bg-sky-500/10 text-sky-300">Attempt</span>
            <span className="text-slate-600">→</span>
            <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-300">Adapt</span>
            <span className="text-slate-600">→</span>
            <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-300">Remediate</span>
            <span className="text-slate-600">→</span>
            <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-300">Transfer</span>
          </div>
        </div>
      </div>

      {/* 2. Today's Recommended Action (Hero Intervention Card) */}
      <div className="relative overflow-hidden rounded-3xl border border-sky-500/25 bg-gradient-to-br from-[#0e2238] via-[#0d1c2e] to-[#091322] p-6 sm:p-8 shadow-xl shadow-sky-950/30">
        <div className="absolute top-0 right-0 w-80 h-80 bg-sky-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-3 max-w-3xl">
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-sky-400/15 text-sky-300 border border-sky-400/30">
                <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                Adaptive Decision Engine
              </span>
              <span className="text-xs text-slate-400 font-medium">
                {recommendation?.priority ? `${recommendation.priority.toUpperCase()} PRIORITY` : "HIGH PRIORITY"}
              </span>
            </div>

            <h2 className="text-xl sm:text-2xl font-bold text-white tracking-tight font-['Plus_Jakarta_Sans',sans-serif]">
              {recommendation ? getActionTitle(recommendation.action) : "Start Preclinical Renal Physiology"}
            </h2>

            <p className="text-sm text-slate-300 leading-relaxed">
              {recommendation?.explanation ||
                "Deepen your understanding of renal mechanisms. Practice clinical questions on RAAS enzymatic cascade and glomerular barrier permeability."}
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-1 text-xs text-slate-400 font-medium">
              <span className="flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-sky-400" />
                Subject: <span className="text-slate-200">{recommendation?.subject || "Renal physiology"}</span>
              </span>
              <span className="text-slate-600">•</span>
              <span className="flex items-center gap-1.5">
                <BrainCircuit className="w-3.5 h-3.5 text-indigo-400" />
                Topic: <span className="text-slate-200">{recommendation?.topic || "RAAS mechanisms"}</span>
              </span>
            </div>
          </div>

          <div className="flex-shrink-0 flex flex-col sm:flex-row lg:flex-col gap-3">
            <Link
              href={
                recommendation?.action === "ASK_GROUNDED_TUTOR"
                  ? `/tutor?topic=${encodeURIComponent(recommendation.topic || "RAAS mechanisms")}`
                  : `/practice?topic=${encodeURIComponent(recommendation?.topic || "RAAS mechanisms")}`
              }
              className="btn-primary justify-center shadow-lg shadow-sky-500/25 text-sm py-3 px-6 rounded-xl group"
            >
              <span>Launch Recommended Action</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              href="/progress"
              className="btn-secondary justify-center text-xs py-2.5 px-4 rounded-xl text-slate-300 hover:text-white"
            >
              View Detailed Reasoning Radar
            </Link>
          </div>
        </div>
      </div>

      {/* 3. Core Learning Tracks (3 Modalities) */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white tracking-tight font-['Plus_Jakarta_Sans',sans-serif]">
              Core Learning Tracks
            </h3>
            <p className="text-xs text-slate-400">
              Three integrated modalities for mastery, reasoning, and spatial understanding.
            </p>
          </div>
          <Link href="/practice" className="text-xs text-sky-400 hover:text-sky-300 flex items-center gap-1 font-semibold">
            All practice modules <ArrowRight className="w-3 h-3" />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Preclinical University Track */}
          <div className="med-card p-6 flex flex-col justify-between group hover:border-sky-500/30 transition-all">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 flex items-center justify-center text-sky-400">
                  <BookOpen className="w-5 h-5" />
                </div>
                <span className="med-badge med-badge-primary">Preclinical Core</span>
              </div>
              <h4 className="text-base font-bold text-white group-hover:text-sky-300 transition-colors">
                University Question Bank
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Single-best-answer MCQs with verified distractor taxonomies. Trigger intelligent Socratic remediation on incorrect attempts.
              </p>
            </div>
            <div className="pt-6 border-t border-white/[0.06] mt-4 flex items-center justify-between text-xs">
              <span className="text-slate-400 font-medium">5 Questions Available</span>
              <Link
                href="/practice?track=university"
                className="text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition-all"
              >
                Practice <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* PLAB Clinical Track */}
          <div className="med-card p-6 flex flex-col justify-between group hover:border-indigo-500/30 transition-all">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <Stethoscope className="w-5 h-5" />
                </div>
                <span className="med-badge med-badge-warning">Preview QA</span>
              </div>
              <h4 className="text-base font-bold text-white group-hover:text-indigo-300 transition-colors">
                PLAB Clinical Exam
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                UK clinical scenario vignettes covering Cardiology, Respiratory, and Emergency protocols. Strictly governed in Preview QA mode.
              </p>
            </div>
            <div className="pt-6 border-t border-white/[0.06] mt-4 flex items-center justify-between text-xs">
              <span className="text-slate-400 font-medium">36 Candidate Questions</span>
              <Link
                href="/practice?track=plab"
                className="text-indigo-400 hover:text-indigo-300 font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition-all"
              >
                Review Track <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* 3D Spatial Anatomy Hero Track */}
          <div className="med-card p-6 flex flex-col justify-between group hover:border-purple-500/30 transition-all">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                  <Layers3 className="w-5 h-5" />
                </div>
                <span className="med-badge bg-purple-500/10 text-purple-300 border-purple-500/20">
                  3D Spatial Hero
                </span>
              </div>
              <h4 className="text-base font-bold text-white group-hover:text-purple-300 transition-colors">
                Generative 3D Anatomy Lab
              </h4>
              <p className="text-xs text-slate-400 leading-relaxed">
                Interactive spatial atlas grounded in HRA anatomy ontologies. Master renal vasculature with guided steps and 3D pin challenges.
              </p>
            </div>
            <div className="pt-6 border-t border-white/[0.06] mt-4 flex items-center justify-between text-xs">
              <span className="text-slate-400 font-medium">Renal Hilum Active</span>
              <Link
                href="/anatomy"
                className="text-purple-400 hover:text-purple-300 font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition-all"
              >
                Launch Atlas <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Live Progress Snapshot & AI Tutor Quick Prompt */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Progress Snapshot Card (2 cols) */}
        <div className="lg:col-span-2 med-card p-6 space-y-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <TrendingUp className="w-5 h-5 text-sky-400" />
              <h3 className="text-base font-bold text-white font-['Plus_Jakarta_Sans',sans-serif]">
                Unified Learner Progress
              </h3>
            </div>
            <Link href="/progress" className="text-xs text-sky-400 hover:text-sky-300 font-semibold">
              Full Analytics →
            </Link>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-4">
              <span className="text-[11px] text-slate-400 font-medium block mb-1">Preclinical Accuracy</span>
              <div className="text-2xl font-extrabold text-white font-['Plus_Jakarta_Sans',sans-serif]">
                {accuracyPct}%
              </div>
              <div className="w-full bg-white/10 h-1.5 rounded-full mt-2 overflow-hidden">
                <div className="bg-sky-400 h-full rounded-full transition-all" style={{ width: `${accuracyPct}%` }} />
              </div>
            </div>

            <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-4">
              <span className="text-[11px] text-slate-400 font-medium block mb-1">Total Attempts</span>
              <div className="text-2xl font-extrabold text-white font-['Plus_Jakarta_Sans',sans-serif]">
                {progress?.university?.attempted ?? 0}
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">University Track</span>
            </div>

            <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-4">
              <span className="text-[11px] text-slate-400 font-medium block mb-1">3D Challenges</span>
              <div className="text-2xl font-extrabold text-purple-400 font-['Plus_Jakarta_Sans',sans-serif]">
                {progress?.anatomy?.challenges_passed ?? 0}
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">Pin Tests Passed</span>
            </div>

            <div className="bg-white/[0.02] border border-white/[0.06] rounded-2xl p-4">
              <span className="text-[11px] text-slate-400 font-medium block mb-1">Active Weakness</span>
              <div className="text-2xl font-extrabold text-amber-400 font-['Plus_Jakarta_Sans',sans-serif]">
                {progress?.adaptive?.weak_topics?.length ?? 0}
              </div>
              <span className="text-[10px] text-slate-500 mt-1 block">In Remediation</span>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-400 bg-white/[0.02] rounded-xl px-4 py-2.5 border border-white/[0.06]">
            <span>Active Educational Corpus: <strong className="text-slate-200">12 Verified Sources (CC BY 4.0)</strong></span>
            <span>Data Integrity: <strong className="text-emerald-400">Fail-Closed Verified</strong></span>
          </div>
        </div>

        {/* AI Tutor Prompt Card (1 col) */}
        <div className="med-card p-6 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <h3 className="text-base font-bold text-white font-['Plus_Jakarta_Sans',sans-serif]">
                Grounded AI Tutor
              </h3>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Ask open-ended preclinical or clinical questions. Every response is verified with extractive citations from medical literature.
            </p>
          </div>

          <form onSubmit={handleTutorSubmit} className="space-y-3">
            <div className="relative">
              <input
                type="text"
                value={tutorInput}
                onChange={(e) => setTutorInput(e.target.value)}
                placeholder="Ask e.g. How does renin act on angiotensinogen?"
                className="w-full bg-white/[0.04] border border-white/[0.1] rounded-xl py-2.5 px-3.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-sky-400 focus:ring-1 focus:ring-sky-400/50"
              />
            </div>

            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() => setTutorInput("How does renin act on angiotensinogen?")}
                className="text-[10px] text-slate-400 hover:text-sky-300 bg-white/[0.03] hover:bg-white/[0.06] px-2 py-1 rounded-md border border-white/[0.06] transition-colors"
              >
                RAAS Cascade
              </button>
              <button
                type="button"
                onClick={() => setTutorInput("Explain the glomerular filtration barrier layers.")}
                className="text-[10px] text-slate-400 hover:text-sky-300 bg-white/[0.03] hover:bg-white/[0.06] px-2 py-1 rounded-md border border-white/[0.06] transition-colors"
              >
                Glomerular Barrier
              </button>
            </div>

            <button
              type="submit"
              className="w-full btn-primary justify-center text-xs py-2.5 rounded-xl mt-2"
            >
              <span>Consult Grounded AI Tutor</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
