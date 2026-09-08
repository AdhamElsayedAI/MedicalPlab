"use client";

import React, { useState, useEffect } from "react";
import confetti from "canvas-confetti";
import {
  GraduationCap,
  Clock,
  CheckCircle2,
  XCircle,
  Sparkles,
  ArrowRight,
  RotateCcw,
  BookOpen,
  Award,
} from "lucide-react";
import { PLAB_QUESTIONS } from "@/lib/demo-data";
import { PLABQuestion } from "@/lib/types";
import { api } from "@/lib/api-client";

interface ClinicalMCQEngineProps {
  initialQuestionId?: string;
  onNavigateToTutor?: (query: string) => void;
  onAttemptCompleted?: (topic: string, isCorrect: boolean) => void;
}

export const ClinicalMCQEngine: React.FC<ClinicalMCQEngineProps> = ({
  initialQuestionId,
  onNavigateToTutor,
  onAttemptCompleted,
}) => {
  const [currentIdx, setCurrentIdx] = useState(0);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [timeLeft, setTimeLeft] = useState(75);
  const [timerActive, setTimerActive] = useState(true);

  // Set initial question if provided
  useEffect(() => {
    if (initialQuestionId) {
      const idx = PLAB_QUESTIONS.findIndex((q) => q.id === initialQuestionId);
      if (idx !== -1) setCurrentIdx(idx);
    }
  }, [initialQuestionId]);

  const currentQ: PLABQuestion = PLAB_QUESTIONS[currentIdx] || PLAB_QUESTIONS[0];

  // Countdown timer
  useEffect(() => {
    if (!timerActive || isSubmitted || timeLeft <= 0) return;
    const interval = setInterval(() => {
      setTimeLeft((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(interval);
  }, [timerActive, isSubmitted, timeLeft]);

  const handleSelectOption = (key: string) => {
    if (isSubmitted) return;
    setSelectedOption(key);
  };

  const handleSubmit = async () => {
    if (!selectedOption || isSubmitted) return;
    setIsSubmitted(true);
    setTimerActive(false);

    const chosen = currentQ.options.find((o) => o.key === selectedOption);
    const isCorrect = chosen?.isCorrect || false;

    if (isCorrect) {
      confetti({
        particleCount: 80,
        spread: 70,
        origin: { y: 0.6 },
        colors: ["#00f2fe", "#00e676", "#3b82f6"],
      });
    }

    // Record attempt to Stage-G database
    await api.recordAttempt(currentQ.topic, isCorrect);
    if (onAttemptCompleted) {
      onAttemptCompleted(currentQ.topic, isCorrect);
    }
  };

  const handleNext = () => {
    const nextIdx = (currentIdx + 1) % PLAB_QUESTIONS.length;
    setCurrentIdx(nextIdx);
    setSelectedOption(null);
    setIsSubmitted(false);
    setTimeLeft(75);
    setTimerActive(true);
  };

  const isCurrentCorrect = currentQ.options.find((o) => o.key === selectedOption)?.isCorrect;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-6 space-y-6">
      {/* Header bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg bg-purple-950 text-purple-400 border border-purple-500/40">
              <GraduationCap className="w-4 h-4" />
            </span>
            <h2 className="text-xl sm:text-2xl font-black text-white tracking-wide">
              ADAPTIVE PLAB CLINICAL QUIZ
            </h2>
          </div>
          <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
            <span className="text-cyan-400 font-bold">{currentQ.specialty}</span>
            <span>//</span>
            <span>STAGE-C GENERATOR</span>
            <span>//</span>
            <span className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-slate-300">
              DIFFICULTY: {currentQ.difficulty}
            </span>
          </div>
        </div>

        {/* Timer Display */}
        <div className="flex items-center gap-2 bg-slate-900/90 px-3.5 py-1.5 rounded-xl border border-slate-800 text-xs font-mono">
          <Clock className={`w-4 h-4 ${timeLeft < 20 ? "text-rose-400 animate-pulse" : "text-cyan-400"}`} />
          <span className="text-slate-400">TIME REMAINING:</span>
          <span className={`font-bold text-sm ${timeLeft < 20 ? "text-rose-400" : "text-white"}`}>
            {timeLeft}s
          </span>
        </div>
      </div>

      {/* Main Vignette Card */}
      <div className="cyber-card rounded-2xl p-6 border border-cyan-500/25 bg-slate-950/85 space-y-5">
        <div className="flex items-center justify-between text-xs font-mono text-slate-400 border-b border-slate-800 pb-2.5">
          <span>CLINICAL VIGNETTE #0{currentIdx + 1}</span>
          <span className="text-cyan-400 font-bold">{currentQ.evidenceRef}</span>
        </div>

        <p className="text-sm sm:text-base text-slate-200 leading-relaxed font-sans font-medium">
          {currentQ.vignette}
        </p>

        {/* Options List */}
        <div className="space-y-2.5 pt-2">
          {currentQ.options.map((opt) => {
            const isSelected = selectedOption === opt.key;
            let optionStyles = "bg-slate-900/80 border-slate-800 text-slate-300 hover:border-cyan-500/50";

            if (isSelected && !isSubmitted) {
              optionStyles = "bg-cyan-500/20 border-cyan-400 text-cyan-200 shadow-[0_0_15px_rgba(0,242,254,0.25)]";
            } else if (isSubmitted) {
              if (opt.isCorrect) {
                optionStyles = "bg-emerald-950/60 border-emerald-500 text-emerald-200 shadow-[0_0_15px_rgba(0,230,118,0.25)]";
              } else if (isSelected && !opt.isCorrect) {
                optionStyles = "bg-rose-950/60 border-rose-500 text-rose-200";
              }
            }

            return (
              <div
                key={opt.key}
                onClick={() => handleSelectOption(opt.key)}
                className={`p-3.5 rounded-xl border text-xs sm:text-sm font-medium flex items-center justify-between cursor-pointer transition-all duration-200 ${optionStyles}`}
              >
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-lg bg-slate-950 border border-slate-700 flex items-center justify-center font-mono font-bold text-xs">
                    {opt.key}
                  </span>
                  <span>{opt.text}</span>
                </div>

                {isSubmitted && opt.isCorrect && (
                  <CheckCircle2 className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                )}
                {isSubmitted && isSelected && !opt.isCorrect && (
                  <XCircle className="w-5 h-5 text-rose-400 flex-shrink-0" />
                )}
              </div>
            );
          })}
        </div>

        {/* Submit & Navigation Button */}
        <div className="pt-3 flex items-center justify-between border-t border-slate-800">
          <span className="text-xs font-mono text-slate-400">
            {isSubmitted
              ? isCurrentCorrect
                ? "CORRECT ANSWER (+10 MASTERY XP)"
                : "INCORRECT - REVIEW EVIDENCE BELOW"
              : "Select single best answer and click Submit"}
          </span>

          {!isSubmitted ? (
            <button
              onClick={handleSubmit}
              disabled={!selectedOption}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold text-xs shadow-lg shadow-cyan-500/25 hover:shadow-cyan-500/40 disabled:opacity-50 transition-all"
            >
              Submit Answer
            </button>
          ) : (
            <button
              onClick={handleNext}
              className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 text-white font-bold text-xs flex items-center gap-2 shadow-lg shadow-cyan-500/25 transition-all"
            >
              <span>Next Clinical Scenario</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Distractor Elimination & Evidence Rationale (Shown after submit) */}
      {isSubmitted && (
        <div className="cyber-card rounded-2xl p-6 border border-cyan-500/30 bg-slate-950/90 space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <span className="text-xs font-mono text-cyan-400 font-bold flex items-center gap-1.5">
              <BookOpen className="w-4 h-4" />
              EVIDENCE-GROUNDED CLINICAL RATIONALE
            </span>
            <span className="text-[11px] font-mono text-emerald-400">
              NICE GUIDELINE VERIFIED
            </span>
          </div>

          <p className="text-xs text-slate-200 leading-relaxed">
            {currentQ.explanation}
          </p>

          {/* Distractor breakdown */}
          <div className="space-y-2 pt-2">
            <span className="text-[11px] font-mono text-slate-400 font-bold block">
              DISTRACTOR ELIMINATION ANALYSIS:
            </span>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
              {currentQ.options.map((opt) => (
                <div
                  key={opt.key}
                  className={`p-3 rounded-xl border text-[11px] font-mono ${
                    opt.isCorrect
                      ? "bg-emerald-950/40 border-emerald-500/40 text-emerald-300"
                      : "bg-slate-900/80 border-slate-800 text-slate-400"
                  }`}
                >
                  <span className="font-bold text-white mr-1.5">Option {opt.key}:</span>
                  <span>{opt.eliminationRationale}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Direct CTA to discuss on AI tutor */}
          {onNavigateToTutor && (
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => onNavigateToTutor(`Discuss rationale for ${currentQ.specialty} question: ${currentQ.explanation}`)}
                className="text-xs font-bold text-cyan-300 hover:text-cyan-200 flex items-center gap-1.5"
              >
                <span>Ask AI Tutor to explore this rationale further</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
