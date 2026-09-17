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
  Activity,
  ArrowUpRight,
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
  const [universityCount, setUniversityCount] = useState<number>(6);
  const [loading, setLoading] = useState(true);
  const [tutorInput, setTutorInput] = useState("");

  useEffect(() => {
    const id = getAuthoritativeLearnerId();
    setLearnerId(id);

    async function loadData() {
      try {
        setLoading(true);
        const [recData, progData, subjectsData] = await Promise.allSettled([
          api.getAdaptiveRecommendation(id),
          api.getLearnerProgress(id),
          api.getUniversitySubjects(),
        ]);

        if (recData.status === "fulfilled") {
          setRecommendation(recData.value);
        }
        if (progData.status === "fulfilled") {
          setProgress(progData.value);
        }
        if (subjectsData.status === "fulfilled" && Array.isArray(subjectsData.value)) {
          const totalQuestions = subjectsData.value.reduce((acc, sub) => acc + (sub.count || 0), 0);
          if (totalQuestions > 0) {
            setUniversityCount(totalQuestions);
          }
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
        return "Recommended Next Educational Step";
    }
  };

  const accuracyPct = progress?.university?.accuracy !== null && progress?.university?.accuracy !== undefined
    ? Math.round(progress.university.accuracy * 100)
    : 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 med-fade-in">
      {/* 1. Header & Dynamic Hero Composition */}
      <div className="relative overflow-hidden rounded-3xl border border-sky-500/25 bg-gradient-to-br from-[#0c1a2e] via-[#091424] to-[#070e1a] p-6 sm:p-8 lg:p-10 shadow-2xl shadow-black/60">
        {/* Subtle Ambient Radial Lighting */}
        <div className="absolute top-0 right-1/4 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none animate-ambient-glow" />
        <div className="absolute bottom-0 right-0 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row items-stretch justify-between gap-8">
          {/* Left Column: Greeting, Value Prop & Personalized Recommendation */}
          <div className="flex-1 space-y-6">
            <div>
              <div className="flex items-center gap-2 mb-2.5">
                <span className="inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-[11px] font-semibold bg-sky-500/15 text-sky-300 border border-sky-500/30">
                  <Activity className="w-3 h-3 text-sky-400" />
                  Preclinical &amp; Clinical Track
                </span>
                <span className="text-xs text-slate-400 font-medium">
                  Medical Student
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold text-white tracking-tight font-['Plus_Jakarta_Sans',sans-serif]">
                Welcome back to MedicalPlab
              </h1>
              <p className="text-sm text-slate-300 mt-2 max-w-2xl leading-relaxed">
                An Adaptive Evidence-Grounded Medical Learning Platform. MedicalPlab does not only answer students—it learns how students learn.
              </p>
            </div>

            {/* Personalized Recommendation Card */}
            <div className="rounded-2xl border border-sky-500/30 bg-sky-950/20 p-5 space-y-3.5 backdrop-blur-md">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-sky-400/15 text-sky-300 border border-sky-400/30">
                    <Sparkles className="w-3.5 h-3.5 text-sky-400" />
                    Recommended Next Step
                  </span>
                </div>
                <span className="text-[11px] font-semibold text-sky-400 uppercase tracking-wider">
                  {recommendation?.priority === "high" ? "Targeted Focus" : "Active Focus"}
                </span>
              </div>

              <div>
                <h2 className="text-lg sm:text-xl font-bold text-white tracking-tight font-['Plus_Jakarta_Sans',sans-serif]">
                  {recommendation ? getActionTitle(recommendation.action) : "Start Preclinical Renal Physiology"}
                </h2>
                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mt-1">
                  {recommendation?.explanation ||
                    "Deepen your understanding of renal mechanisms. Practice clinical questions on RAAS enzymatic cascade and glomerular barrier permeability."}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 font-medium pt-1">
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

              <div className="flex flex-col sm:flex-row gap-3 pt-2">
                <Link
                  href={
                    recommendation?.action === "ASK_GROUNDED_TUTOR"
                      ? `/tutor?topic=${encodeURIComponent(recommendation.topic || "RAAS mechanisms")}`
                      : `/practice?topic=${encodeURIComponent(recommendation?.topic || "RAAS mechanisms")}`
                  }
                  className="btn-primary justify-center shadow-lg shadow-sky-500/25 text-xs sm:text-sm py-2.5 px-5 rounded-xl group"
                >
                  <span>Launch Recommended Action</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </Link>

                <Link
                  href="/progress"
                  className="btn-secondary justify-center text-xs py-2.5 px-4 rounded-xl text-slate-300 hover:text-white"
                >
                  View Learning Progress
                </Link>
              </div>
            </div>
          </div>

          {/* Right Column: Abstract Animated Cognitive Learning Network */}
          <div className="w-full lg:w-[410px] shrink-0 bg-[#0b1424]/90 border border-sky-500/20 rounded-3xl p-5 shadow-2xl relative overflow-hidden flex flex-col justify-between">
            <div className="flex items-center justify-between mb-3 border-b border-white/[0.06] pb-2.5">
              <div className="flex items-center gap-2">
                <BrainCircuit className="w-4 h-4 text-sky-400" />
                <span className="text-xs font-bold text-white tracking-wide">
                  Cognitive Learning Loop
                </span>
              </div>
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                Continuous Adaptivity
              </span>
            </div>

            {/* SVG Cognitive Learning Loop */}
            <div className="relative py-2 flex items-center justify-center">
              <svg viewBox="0 0 360 170" className="w-full h-auto max-h-[170px]" aria-label="Cognitive Learning Loop Diagram">
                <defs>
                  <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.8" />
                    <stop offset="50%" stopColor="#818cf8" stopOpacity="0.8" />
                    <stop offset="100%" stopColor="#34d399" stopOpacity="0.8" />
                  </linearGradient>
                  <radialGradient id="activeGlow" cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
                    <stop offset="100%" stopColor="#38bdf8" stopOpacity="0" />
                  </radialGradient>
                </defs>

                {/* Base track curve */}
                <path
                  d="M 36 85 C 80 20, 140 20, 180 85 C 220 150, 280 150, 324 85"
                  fill="none"
                  stroke="rgba(255,255,255,0.08)"
                  strokeWidth="3"
                />
                {/* Animated active path */}
                <path
                  d="M 36 85 C 80 20, 140 20, 180 85 C 220 150, 280 150, 324 85"
                  fill="none"
                  stroke="url(#lineGrad)"
                  strokeWidth="2.5"
                  className="animate-conduit-flow"
                />

                {/* Node 1: Attempt */}
                <g transform="translate(36, 85)">
                  <circle r="18" fill="#0b1120" stroke="#38bdf8" strokeWidth="1.5" />
                  <circle r="13" fill="#38bdf8" fillOpacity="0.1" />
                  <text textAnchor="middle" dy="3.5" fontSize="8" fill="#7dd3fc" fontWeight="bold">01</text>
                  <text textAnchor="middle" dy="30" fontSize="10" fill="#94a3b8" fontWeight="600">Attempt</text>
                </g>

                {/* Node 2: Understand */}
                <g transform="translate(108, 48)">
                  <circle r="18" fill="#0b1120" stroke="#6366f1" strokeWidth="1.5" />
                  <circle r="13" fill="#6366f1" fillOpacity="0.1" />
                  <text textAnchor="middle" dy="3.5" fontSize="8" fill="#a5b4fc" fontWeight="bold">02</text>
                  <text textAnchor="middle" dy="30" fontSize="10" fill="#94a3b8" fontWeight="600">Understand</text>
                </g>

                {/* Node 3: Adapt (Active Highlighted Node) */}
                <g transform="translate(180, 85)">
                  <circle r="26" fill="url(#activeGlow)" className="animate-pulse" />
                  <circle r="20" fill="#0c2338" stroke="#38bdf8" strokeWidth="2.5" className="animate-cognitive-pulse" />
                  <circle r="14" fill="#38bdf8" fillOpacity="0.2" />
                  <text textAnchor="middle" dy="3.5" fontSize="9" fill="#e0f2fe" fontWeight="bold">03</text>
                  <text textAnchor="middle" dy="-26" fontSize="9" fill="#38bdf8" fontWeight="bold">ACTIVE</text>
                  <text textAnchor="middle" dy="34" fontSize="10" fill="#38bdf8" fontWeight="bold">Adapt</text>
                </g>

                {/* Node 4: Remediate */}
                <g transform="translate(252, 122)">
                  <circle r="18" fill="#0b1120" stroke="#f59e0b" strokeWidth="1.5" />
                  <circle r="13" fill="#f59e0b" fillOpacity="0.1" />
                  <text textAnchor="middle" dy="3.5" fontSize="8" fill="#fcd34d" fontWeight="bold">04</text>
                  <text textAnchor="middle" dy="30" fontSize="10" fill="#94a3b8" fontWeight="600">Remediate</text>
                </g>

                {/* Node 5: Transfer */}
                <g transform="translate(324, 85)">
                  <circle r="18" fill="#0b1120" stroke="#10b981" strokeWidth="1.5" />
                  <circle r="13" fill="#10b981" fillOpacity="0.1" />
                  <text textAnchor="middle" dy="3.5" fontSize="8" fill="#6ee7b7" fontWeight="bold">05</text>
                  <text textAnchor="middle" dy="30" fontSize="10" fill="#94a3b8" fontWeight="600">Transfer</text>
                </g>
              </svg>
            </div>

            <div className="mt-2 bg-white/[0.02] border border-white/[0.05] rounded-xl p-2.5 text-[11px] text-slate-300 flex items-center justify-between">
              <span className="text-slate-400">Intervention Mode:</span>
              <span className="font-semibold text-sky-300">Targeted Socratic Scaffolding</span>
            </div>
          </div>
        </div>
      </div>

      {/* 2. Your Adaptive Learning Path */}
      <div className="med-card p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/[0.06] pb-3">
          <div>
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-sky-400" />
              <h3 className="text-base font-bold text-white font-['Plus_Jakarta_Sans',sans-serif]">
                Your Adaptive Learning Path
              </h3>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-500/10 text-sky-300 border border-sky-500/20">
                Personalized Trajectory
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              MedicalPlab continuously sequences topics based on your clinical and preclinical reasoning signals.
            </p>
          </div>
          <span className="text-xs text-slate-400 font-medium">
            Active Organ System: <strong className="text-slate-200">Renal Physiology</strong>
          </span>
        </div>

        {/* 4-Step Learning Path */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-1">
          {/* Step 1 */}
          <div className="p-4 rounded-xl bg-white/[0.02] border border-emerald-500/20 relative overflow-hidden">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-[10px] font-mono text-emerald-400 font-semibold uppercase">Step 1 · Verified</span>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            </div>
            <h4 className="text-sm font-bold text-white mb-1">Renal Hemodynamics</h4>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Arteriole resistance, GFR autoregulation, and basic transport mechanics demonstrated.
            </p>
          </div>

          {/* Step 2 */}
          <div className="p-4 rounded-xl bg-white/[0.02] border border-sky-500/20 relative overflow-hidden">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-[10px] font-mono text-sky-400 font-semibold uppercase">Step 2 · In Progress</span>
              <Activity className="w-3.5 h-3.5 text-sky-400 animate-pulse" />
            </div>
            <h4 className="text-sm font-bold text-white mb-1">Glomerular Filtration</h4>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Podocyte slit diaphragm permeability and Starling physical filtration pressures.
            </p>
          </div>

          {/* Step 3 (Current Recommended) */}
          <div className="p-4 rounded-xl bg-sky-950/30 border border-sky-400/40 relative overflow-hidden shadow-md shadow-sky-950/40">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-[10px] font-mono text-sky-300 font-bold uppercase">Step 3 · Recommended Next</span>
              <span className="w-2 h-2 rounded-full bg-sky-400 animate-ping" />
            </div>
            <h4 className="text-sm font-bold text-sky-200 mb-1">
              {recommendation?.topic || "RAAS Reinforcement"}
            </h4>
            <p className="text-[11px] text-slate-300 leading-relaxed">
              Targeted Socratic consolidation on renin enzymatic cleavages and vascular tone.
            </p>
          </div>

          {/* Step 4 */}
          <div className="p-4 rounded-xl bg-white/[0.01] border border-white/[0.06] relative overflow-hidden opacity-75">
            <div className="flex items-center justify-between text-xs mb-2">
              <span className="text-[10px] font-mono text-slate-400 font-semibold uppercase">Step 4 · Milestone</span>
              <Clock className="w-3.5 h-3.5 text-slate-500" />
            </div>
            <h4 className="text-sm font-bold text-slate-200 mb-1">Clinical Transfer Check</h4>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Independent clinical scenario verification without scaffolding assistance.
            </p>
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
          <div className="med-card med-track-university p-6 flex flex-col justify-between group transition-all">
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
              <span className="text-slate-400 font-medium">{universityCount} Questions Available</span>
              <Link
                href="/practice?track=university"
                className="text-sky-400 hover:text-sky-300 font-semibold flex items-center gap-1 group-hover:translate-x-0.5 transition-all"
              >
                Practice <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* PLAB Clinical Track */}
          <div className="med-card med-track-plab p-6 flex flex-col justify-between group transition-all">
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

          {/* 3D Spatial Anatomy Track */}
          <div className="med-card med-track-anatomy p-6 flex flex-col justify-between group transition-all">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="w-10 h-10 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400">
                  <Layers3 className="w-5 h-5" />
                </div>
                <span className="med-badge bg-purple-500/10 text-purple-300 border-purple-500/20">
                  Interactive 3D
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

          <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-slate-400 bg-white/[0.02] rounded-xl px-4 py-2.5 border border-white/[0.06]">
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

      {/* 5. MedicalPlab — Future Intelligence (Roadmap Only) */}
      <div className="pt-8 border-t border-white/[0.08] space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold tracking-wider uppercase bg-indigo-500/10 text-indigo-300 border border-indigo-500/30">
                Future Research &amp; Product Roadmap
              </span>
              <span className="text-xs text-slate-500">Non-Production Vision</span>
            </div>
            <h3 className="text-xl font-bold text-white tracking-tight mt-1 font-['Plus_Jakarta_Sans',sans-serif]">
              MedicalPlab — Future Intelligence
            </h3>
            <p className="text-xs text-slate-400 mt-0.5 max-w-2xl">
              Technically credible next-generation capabilities under active architectural research. Clearly distinguished from current frozen production APIs.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {/* Card 1 */}
          <div className="p-5 rounded-2xl bg-white/[0.02] border border-dashed border-white/[0.12] space-y-2 hover:border-indigo-400/30 transition-colors">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-indigo-500/15 text-indigo-300 border border-indigo-500/25">
                ROADMAP
              </span>
              <BrainCircuit className="w-4 h-4 text-indigo-400/60" />
            </div>
            <h4 className="text-sm font-bold text-white">Multimodal Medical Learning</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Educational interpretation of diagrams, radiology teaching images, pathology slides, and anatomy visuals through evidence-grounded multimodal learning.
            </p>
          </div>

          {/* Card 2 */}
          <div className="p-5 rounded-2xl bg-white/[0.02] border border-dashed border-white/[0.12] space-y-2 hover:border-indigo-400/30 transition-colors">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-indigo-500/15 text-indigo-300 border border-indigo-500/25">
                ROADMAP
              </span>
              <Compass className="w-4 h-4 text-sky-400/60" />
            </div>
            <h4 className="text-sm font-bold text-white">Stronger Medical Retrieval</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Evaluate next-generation domain embeddings and reranking approaches while preserving evidence verification and fail-closed behavior.
            </p>
          </div>

          {/* Card 3 */}
          <div className="p-5 rounded-2xl bg-white/[0.02] border border-dashed border-white/[0.12] space-y-2 hover:border-indigo-400/30 transition-colors">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-indigo-500/15 text-indigo-300 border border-indigo-500/25">
                ROADMAP
              </span>
              <TrendingUp className="w-4 h-4 text-teal-400/60" />
            </div>
            <h4 className="text-sm font-bold text-white">Personalized Curriculum Sequencing</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Longitudinal learning-path optimization based on accumulated multi-session learner evidence and knowledge state estimation.
            </p>
          </div>

          {/* Card 4 */}
          <div className="p-5 rounded-2xl bg-white/[0.02] border border-dashed border-white/[0.12] space-y-2 hover:border-indigo-400/30 transition-colors">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-indigo-500/15 text-indigo-300 border border-indigo-500/25">
                ROADMAP
              </span>
              <ShieldCheck className="w-4 h-4 text-emerald-400/60" />
            </div>
            <h4 className="text-sm font-bold text-white">Clinician Feedback Loop</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Senior clinician review signals feeding controlled quality improvement workflows and consensus-based distractor taxonomy validation.
            </p>
          </div>

          {/* Card 5 */}
          <div className="p-5 rounded-2xl bg-white/[0.02] border border-dashed border-white/[0.12] space-y-2 hover:border-indigo-400/30 transition-colors">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-indigo-500/15 text-indigo-300 border border-indigo-500/25">
                ROADMAP
              </span>
              <Layers3 className="w-4 h-4 text-purple-400/60" />
            </div>
            <h4 className="text-sm font-bold text-white">Expanded Interactive Anatomy</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Additional organ systems (Cardiovascular, Respiratory, Neuroanatomy) built using scientifically licensed reference assets and HRA cross-links.
            </p>
          </div>

          {/* Card 6 */}
          <div className="p-5 rounded-2xl bg-white/[0.02] border border-dashed border-white/[0.12] space-y-2 hover:border-indigo-400/30 transition-colors">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-indigo-500/15 text-indigo-300 border border-indigo-500/25">
                ROADMAP
              </span>
              <Stethoscope className="w-4 h-4 text-amber-400/60" />
            </div>
            <h4 className="text-sm font-bold text-white">Golden PLAB Expansion</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Clinician-reviewed production question bank expansion across all 18 GMC clinical areas with formal psychometric reliability auditing.
            </p>
          </div>

          {/* Card 7 */}
          <div className="p-5 rounded-2xl bg-white/[0.02] border border-dashed border-white/[0.12] space-y-2 hover:border-indigo-400/30 transition-colors">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-wider bg-indigo-500/15 text-indigo-300 border border-indigo-500/25">
                ROADMAP
              </span>
              <BookOpen className="w-4 h-4 text-sky-400/60" />
            </div>
            <h4 className="text-sm font-bold text-white">Native Mobile Experience</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Native iOS and Android learner applications consuming the frozen MedicalPlab API with offline study caching and tactile 3D navigation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
