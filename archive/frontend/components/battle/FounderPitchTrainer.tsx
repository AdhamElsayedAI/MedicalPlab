"use client";

import React, { useState, useEffect } from "react";
import {
  Volume2,
  Clock,
  CheckCircle2,
  AlertCircle,
  Play,
  Pause,
  RotateCcw,
  Sparkles,
  Star,
  Award,
  ChevronRight,
  ChevronLeft,
} from "lucide-react";
import { BATTLE_SCENES } from "@/lib/stage-l-data";

export const FounderPitchTrainer: React.FC = () => {
  const [currentSlideIdx, setCurrentSlideIdx] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [ratings, setRatings] = useState<Record<number, number>>({});
  const [checkedChecklist, setCheckedChecklist] = useState<Record<string, boolean>>({
    eye_contact: true,
    posture: true,
  });

  const scene = BATTLE_SCENES[currentSlideIdx];
  const total = BATTLE_SCENES.length;

  useEffect(() => {
    let t: NodeJS.Timeout;
    if (isRunning) {
      t = setInterval(() => setElapsed((prev) => prev + 1), 1000);
    }
    return () => clearInterval(t);
  }, [isRunning]);

  const toggleCheck = (key: string) => {
    setCheckedChecklist((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const setRatingForCurrent = (stars: number) => {
    setRatings((prev) => ({ ...prev, [currentSlideIdx]: stars }));
  };

  const checklistItems = [
    { id: "eye_contact", label: "Make direct eye contact with the lead technical & medical judges" },
    { id: "vocal_pace", label: "Steady vocal pacing: avoid rushing through the 42% failure statistic" },
    { id: "metric_labeling", label: "Explicitly label financial metrics: 'Verified metric' vs 'Target'" },
    { id: "stage_pointing", label: "Physically gesture toward 3D anatomical coronary vessels during demo" },
    { id: "definitive_ending", label: "End on confident assertion: 'MedicalPlab is the future of clinical safety'" },
  ];

  const speakingTips = [
    { good: "Mathematical claim provenance", avoid: "Our AI is basically smart" },
    { good: "0.0% ungrounded assertions", avoid: "It almost never hallucinates" },
    { good: "Socratic pedagogical friction", avoid: "It chats with you" },
    { good: "£18k discretionary trust spend", avoid: "Selling to the government takes forever" },
  ];

  return (
    <div className="space-y-6">
      {/* Header Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 rounded-2xl bg-slate-950/90 border border-cyan-500/20 backdrop-blur-xl">
        <div>
          <div className="flex items-center gap-2 mb-1.5">
            <span className="px-2.5 py-0.5 rounded-lg bg-cyan-950 text-cyan-300 border border-cyan-500/40 text-xs font-mono font-bold flex items-center gap-1.5">
              <Volume2 className="w-3.5 h-3.5 text-cyan-400" />
              FOUNDER PITCH TRAINER & REHEARSAL COACH
            </span>
            <span className="text-xs font-mono text-emerald-400 font-bold">
              CONFIDENCE ENGINE
            </span>
          </div>
          <h3 className="text-xl sm:text-2xl font-black text-white tracking-wide">
            Pacing Stopwatch, Confidence Checklist & Self-Evaluator
          </h3>
          <p className="text-xs text-slate-400 font-sans mt-0.5">
            Drill every slide with vocal pacing controls, vocabulary coaching, and instant delivery evaluation.
          </p>
        </div>

        {/* Stopwatch Controller */}
        <div className="flex items-center gap-3 self-start md:self-center">
          <div className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl bg-slate-900 border border-slate-700 font-mono text-xs">
            <Clock className="w-4 h-4 text-cyan-400" />
            <span className="text-white font-bold">{elapsed}s</span>
            <span className="text-slate-500">/ {scene.durationSeconds}s target</span>
          </div>

          <button
            onClick={() => setIsRunning(!isRunning)}
            className={`p-2 rounded-xl border text-xs font-mono transition-all ${
              isRunning
                ? "bg-amber-950/80 border-amber-500/50 text-amber-300"
                : "bg-emerald-950/80 border-emerald-500/50 text-emerald-300"
            }`}
          >
            {isRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </button>

          <button
            onClick={() => {
              setElapsed(0);
              setIsRunning(false);
            }}
            className="p-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-400 hover:text-white"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Rehearsal Stage Card */}
      <div className="rounded-3xl p-6 sm:p-8 bg-gradient-to-b from-slate-950 via-[#070e1e] to-slate-950 border-2 border-cyan-500/30 shadow-[0_0_40px_rgba(0,242,254,0.12)] space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-5">
          <div>
            <span className="text-[10px] font-mono uppercase text-cyan-400 font-bold block mb-1">
              REHEARSAL SCENE {scene.id} OF {total} — {scene.stageBadge}
            </span>
            <h2 className="text-2xl sm:text-3xl font-black text-white">{scene.title}</h2>
          </div>

          {/* Interactive 5-Star Self Evaluator */}
          <div className="flex items-center gap-1.5 p-2 rounded-2xl bg-slate-900 border border-slate-800">
            <span className="text-[10px] font-mono text-slate-400 mr-1 block">SELF-RATING:</span>
            {[1, 2, 3, 4, 5].map((star) => {
              const currentRating = ratings[currentSlideIdx] || 0;
              return (
                <button
                  key={star}
                  onClick={() => setRatingForCurrent(star)}
                  className={`p-1 transition-colors ${
                    star <= currentRating ? "text-amber-400" : "text-slate-600 hover:text-slate-400"
                  }`}
                >
                  <Star className="w-4 h-4 fill-current" />
                </button>
              );
            })}
          </div>
        </div>

        {/* Big Script Card */}
        <div className="p-6 rounded-2xl bg-cyan-950/20 border border-cyan-500/30 space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-cyan-400 border-b border-cyan-500/20 pb-2">
            <span className="font-bold uppercase tracking-wider flex items-center gap-1.5">
              <Volume2 className="w-4 h-4" /> Spoken Script
            </span>
            <span className="text-slate-400">Target Pace: ~{scene.durationSeconds}s</span>
          </div>
          <p className="text-base sm:text-lg text-slate-100 font-sans leading-relaxed font-medium">
            &ldquo;{scene.speakerScript}&rdquo;
          </p>
        </div>

        {/* Confidence Checklist & Speaking Tips Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {/* Confidence Checklist */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
            <span className="text-xs font-mono text-emerald-400 font-bold uppercase tracking-wider block">
              Founder Confidence Checklist
            </span>
            <div className="space-y-2">
              {checklistItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => toggleCheck(item.id)}
                  className="w-full text-left flex items-start gap-2.5 p-2 rounded-xl hover:bg-slate-800/60 transition-colors"
                >
                  <div
                    className={`flex-shrink-0 w-4 h-4 rounded mt-0.5 border flex items-center justify-center ${
                      checkedChecklist[item.id]
                        ? "bg-emerald-950 border-emerald-500 text-emerald-400"
                        : "border-slate-700 bg-slate-900"
                    }`}
                  >
                    {checkedChecklist[item.id] && <CheckCircle2 className="w-3.5 h-3.5" />}
                  </div>
                  <span className="text-xs text-slate-300 font-sans">{item.label}</span>
                </button>
              ))}
            </div>
          </div>

          {/* High-Impact Vocabulary Coaching */}
          <div className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-3">
            <span className="text-xs font-mono text-cyan-400 font-bold uppercase tracking-wider block">
              Founder Speaking Tips: Power Vocabulary
            </span>
            <div className="space-y-2 text-xs font-sans">
              {speakingTips.map((tip, i) => (
                <div key={i} className="p-2.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between gap-3">
                  <div>
                    <span className="text-emerald-400 font-mono font-bold block">✓ Say:</span>
                    <span className="text-slate-200">{tip.good}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-rose-400 font-mono font-bold block">✗ Avoid:</span>
                    <span className="text-slate-400">{tip.avoid}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Step Navigation */}
        <div className="flex items-center justify-between border-t border-slate-800 pt-5">
          <button
            onClick={() => setCurrentSlideIdx((prev) => Math.max(0, prev - 1))}
            disabled={currentSlideIdx === 0}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              currentSlideIdx === 0
                ? "text-slate-600 bg-slate-900/40 cursor-not-allowed"
                : "text-slate-300 bg-slate-900 hover:bg-slate-800 hover:text-white border border-slate-700"
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Previous Scene</span>
          </button>

          <span className="text-xs font-mono text-slate-500">
            Rehearsing Scene {scene.id} of {total}
          </span>

          <button
            onClick={() => setCurrentSlideIdx((prev) => Math.min(total - 1, prev + 1))}
            disabled={currentSlideIdx === total - 1}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl font-mono text-xs font-bold transition-all ${
              currentSlideIdx === total - 1
                ? "text-slate-600 bg-slate-900/40 cursor-not-allowed"
                : "text-white bg-gradient-to-r from-cyan-500 to-blue-600 shadow-[0_0_12px_rgba(0,242,254,0.25)] hover:scale-[1.02]"
            }`}
          >
            <span>Next Scene</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
